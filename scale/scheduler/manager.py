"""Defines the class that manages high-level scheduler configuration and metrics"""
from __future__ import unicode_literals

import threading

from django.utils.timezone import now

from queue.models import QUEUE_ORDER_FIFO
from scheduler.configuration import SchedulerConfiguration
from scheduler.models import Scheduler


class SchedulerManager(object):
    """This class manages the high-level scheduler configuration and metrics. It is a combination of data from both the
    Scale database and the Mesos master. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self.config = SchedulerConfiguration()
        self.framework_id = None
        self.hostname = None
        self.mesos_address = None

        self._job_launch_count = 0  # Number of new job executions scheduled since last status JSON
        self._last_json = now()  # Last time status JSON was generated
        self._lock = threading.Lock()
        self._task_launch_count = 0  # Number of tasks launched since last status JSON

    def add_scheduling_counts(self, job_launch_count, task_launch_count):
        """Updates the scheduler information from Mesos

        :param job_launch_count: The number of new job executions launched
        :type job_launch_count: int
        :param task_launch_count: The number of tasks launched
        :type task_launch_count: int
        """

        with self._lock:
            self._job_launch_count += job_launch_count
            self._task_launch_count += task_launch_count

    def generate_status_json(self, status_dict):
        """Generates the portion of the status JSON that describes the scheduler settings and metrics

        :param status_dict: The status JSON dict
        :type status_dict: dict
        """

        with self._lock:
            when = now()
            last_json = self._last_json
            job_launch_count = self._job_launch_count
            task_launch_count = self._task_launch_count
            self._last_json = when
            self._job_launch_count = 0
            self._task_launch_count = 0

        mesos_address = self.mesos_address

        duration = (when - last_json).total_seconds()
        job_launch_per_sec = self._round_count_per_sec(job_launch_count / duration)
        task_launch_per_sec = self._round_count_per_sec(task_launch_count / duration)

        if mesos_address:
            mesos_dict = {'framework_id': self.framework_id, 'master_hostname': mesos_address.hostname,
                          'master_port': mesos_address.port}
        else:
            mesos_dict = {'framework_id': self.framework_id, 'master_hostname': None, 'master_port': None}
        metrics_dict = {'jobs_launched_per_sec': job_launch_per_sec, 'tasks_launched_per_sec': task_launch_per_sec}
        status_dict['scheduler'] = {'hostname': self.hostname, 'mesos': mesos_dict, 'metrics': metrics_dict}

    def sync_with_database(self):
        """Syncs with the database to retrieve an updated scheduler model
        """

        scheduler_model = Scheduler.objects.first()
        new_config = SchedulerConfiguration(scheduler_model)
        self.config = new_config

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


scheduler_mgr = SchedulerManager()
