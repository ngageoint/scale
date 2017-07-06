"""Defines the class that manages high-level scheduler configuration and metrics"""
from __future__ import unicode_literals

import logging
import threading
from collections import namedtuple

from django.utils.timezone import now

from scheduler.configuration import SchedulerConfiguration
from scheduler.models import Scheduler

logger = logging.getLogger(__name__)
SchedulerState = namedtuple('SchedulerState', ['state', 'title', 'description'])


class SchedulerManager(object):
    """This class manages the high-level scheduler configuration and metrics. It is a combination of data from both the
    Scale database and the Mesos master. This class is thread-safe."""

    # Scheduler States
    paused_desc = 'Scheduler is paused, so no new jobs will be scheduled. Existing jobs will continue to run.'
    PAUSED = SchedulerState(state='PAUSED', title='Paused', description=paused_desc)
    READY = SchedulerState(state='READY', title='Ready', description='Scheduler is ready to run new jobs.')

    def __init__(self):
        """Constructor
        """

        self.config = SchedulerConfiguration()
        self.framework_id = None
        self.hostname = None
        self.mesos_address = None

        self._job_fin_count = 0  # Number of job executions finished since last status JSON
        self._job_launch_count = 0  # Number of new job executions scheduled since last status JSON
        self._last_json = now()  # Last time status JSON was generated
        self._lock = threading.Lock()
        self._new_offer_count = 0  # Number of new offers received since last status JSON
        self._offer_launch_count = 0  # Number of offers used in launches since last status JSON
        self._task_fin_count = 0  # Number of tasks finished since last status JSON
        self._task_launch_count = 0  # Number of tasks launched since last status JSON
        self._task_update_count = 0  # Number of task updates since last status JSON

        self._state = None
        self._update_state()

    def add_new_offer_count(self, new_offer_count):
        """Add count from a group of newly received offers

        :param new_offer_count: The number of new offers received
        :type new_offer_count: int
        """

        with self._lock:
            self._new_offer_count += new_offer_count

    def add_scheduling_counts(self, job_launch_count, task_launch_count, offer_launch_count):
        """Add metric counts from a round of scheduling

        :param job_launch_count: The number of new job executions launched
        :type job_launch_count: int
        :param task_launch_count: The number of tasks launched
        :type task_launch_count: int
        :param offer_launch_count: The number of offers accepted in the launch
        :type offer_launch_count: int
        """

        with self._lock:
            self._job_launch_count += job_launch_count
            self._task_launch_count += task_launch_count
            self._offer_launch_count = offer_launch_count

    def add_task_update_counts(self, was_task_finished, was_job_finished):
        """Add metric counts from a new task update

        :param was_task_finished: Whether the task was finished (terminal task update)
        :type was_task_finished: bool
        :param was_job_finished: Whether a job execution was finished (terminal state)
        :type was_job_finished: bool
        """

        with self._lock:
            self._task_update_count += 1
            if was_task_finished:
                self._task_fin_count += 1
            if was_job_finished:
                self._job_fin_count += 1

    def generate_status_json(self, status_dict):
        """Generates the portion of the status JSON that describes the scheduler settings and metrics

        :param status_dict: The status JSON dict
        :type status_dict: dict
        """

        with self._lock:
            when = now()
            state = self._state
            last_json = self._last_json
            job_fin_count = self._job_fin_count
            job_launch_count = self._job_launch_count
            new_offer_count = self._new_offer_count
            offer_launch_count = self._offer_launch_count
            task_fin_count = self._task_fin_count
            task_launch_count = self._task_launch_count
            task_update_count = self._task_update_count
            self._last_json = when
            self._job_fin_count = 0
            self._job_launch_count = 0
            self._new_offer_count = 0
            self._offer_launch_count = 0
            self._task_fin_count = 0
            self._task_launch_count = 0
            self._task_update_count = 0

        mesos_address = self.mesos_address

        duration = (when - last_json).total_seconds()
        job_fin_per_sec = self._round_count_per_sec(job_fin_count / duration)
        job_launch_per_sec = self._round_count_per_sec(job_launch_count / duration)
        new_offer_per_sec = self._round_count_per_sec(new_offer_count / duration)
        offer_launch_per_sec = self._round_count_per_sec(offer_launch_count / duration)
        task_fin_per_sec = self._round_count_per_sec(task_fin_count / duration)
        task_launch_per_sec = self._round_count_per_sec(task_launch_count / duration)
        task_update_per_sec = self._round_count_per_sec(task_update_count / duration)

        if mesos_address:
            mesos_dict = {'framework_id': self.framework_id, 'master_hostname': mesos_address.hostname,
                          'master_port': mesos_address.port}
        else:
            mesos_dict = {'framework_id': self.framework_id, 'master_hostname': None, 'master_port': None}
        metrics_dict = {'new_offers_per_sec': new_offer_per_sec, 'task_updates_per_sec': task_update_per_sec,
                        'tasks_finished_per_sec': task_fin_per_sec, 'jobs_finished_per_sec': job_fin_per_sec,
                        'jobs_launched_per_sec': job_launch_per_sec, 'tasks_launched_per_sec': task_launch_per_sec,
                        'offers_launched_per_sec': offer_launch_per_sec}
        state_dict = {'name': state.state, 'title': state.title, 'description': state.description}
        status_dict['scheduler'] = {'hostname': self.hostname, 'mesos': mesos_dict, 'metrics': metrics_dict,
                                    'state': state_dict}

    def sync_with_database(self):
        """Syncs with the database to retrieve an updated scheduler model
        """

        scheduler_model = Scheduler.objects.first()
        new_config = SchedulerConfiguration(scheduler_model)

        with self._lock:
            self.config = new_config
            self._update_state()

    def update_from_mesos(self, framework_id=None, mesos_address=None):
        """Updates the scheduler information from Mesos

        :param framework_id: The framework ID of the scheduler
        :type framework_id: string
        :param mesos_address: The address of the Mesos master
        :type mesos_address: :class:`util.host.HostAddress`
        """

        if framework_id:
            self.framework_id = framework_id
        if mesos_address:
            self.mesos_address = mesos_address

    def _round_count_per_sec(self, number):
        """Rounds the given count per second to the appropriate number of digits

        :param number: The number to round
        :type number: float
        :returns: The number rounded to the appropriate number of digits
        :rtype: float/int
        """

        if number > 100.0:
            return int(round(number, 0))
        elif number > 10.0:
            return round(number, 1)
        return round(number, 2)

    def _update_state(self):
        """Updates the scheduler's state. Caller must have obtained the scheduler's thread lock.
        """

        old_state = self._state

        if self.config.is_paused:
            self._state = self.PAUSED
        else:
            self._state = self.READY

        if old_state and old_state != self._state:
            logger.info('Scheduler is now in %s state', self._state.state)


scheduler_mgr = SchedulerManager()
