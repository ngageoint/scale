"""Defines the class that manages high-level scheduler configuration"""
from __future__ import unicode_literals

import threading

from django.utils.timezone import now

from queue.models import QUEUE_ORDER_FIFO
from scheduler.models import Scheduler


class SchedulerManager(object):
    """This class manages the high-level scheduler configuration. It is a combination of data from both the Scale
    database and the Mesos master. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._framework_id = None
        self._job_exe_count = 0  # Number of new job executions scheduled since last status JSON
        self._last_json = now()  # Last time status JSON was generated
        self._lock = threading.Lock()
        self._mesos_address = None
        self.scheduler = None
        self._task_count = 0  # Number of tasks launched since last status JSON

    @property
    def framework_id(self):
        """Returns the framework ID

        :returns: The framework ID
        :rtype: string
        """

        return self._framework_id

    @property
    def mesos_address(self):
        """Returns the Mesos master address (hostname and port)

        :returns: The address of the Mesos master
        :rtype: :class:`util.host.HostAddress`
        """

        return self._mesos_address

    def add_scheduling_counts(self, job_exe_count, task_count):
        """Updates the scheduler information from Mesos

        :param job_exe_count: The number of new job executions scheduled
        :type job_exe_count: int
        :param task_count: The number of tasks launched
        :type task_count: int
        """

        with self._lock:
            self._job_exe_count += job_exe_count
            self._task_count += task_count

    def generate_status_json(self, status_dict):
        """Generates the portion of the status JSON that describes the scheduler settings and metrics

        :param status_dict: The status JSON dict
        :type status_dict: dict
        """

        with self._lock:
            when = now()
            last_json = self._last_json
            job_exe_count = self._job_exe_count
            task_count = self._task_count
            self._last_json = when
            self._job_exe_count = 0
            self._task_count = 0

        duration = (when - last_json).total_seconds()
        job_exe_per_sec = self._round_count_per_sec(job_exe_count / duration)
        task_per_sec = self._round_count_per_sec(task_count / duration)

        status_dict['scheduler'] = {'job_exe_per_sec': job_exe_per_sec, 'task_per_sec': task_per_sec}

    def is_paused(self):
        """Indicates whether the scheduler is currently paused or not

        :returns: True if the scheduler is paused, False otherwise
        :rtype: bool
        """

        with self._lock:
            if not self.scheduler:
                return True
            return self.scheduler.is_paused

    def queue_mode(self):
        """Returns the current mode for ordering the queue

        :returns: The queue mode
        :rtype: string
        """

        with self._lock:
            if not self.scheduler:
                return QUEUE_ORDER_FIFO
            return self.scheduler.queue_mode

    def sync_with_database(self):
        """Syncs with the database to retrieve an updated scheduler model
        """

        scheduler = Scheduler.objects.first()

        with self._lock:
            self.scheduler = scheduler

    def update_from_mesos(self, framework_id=None, mesos_address=None):
        """Updates the scheduler information from Mesos

        :param framework_id: The framework ID of the scheduler
        :type framework_id: string
        :param mesos_address: The address of the Mesos master
        :type mesos_address: :class:`util.host.HostAddress`
        """

        with self._lock:
            if framework_id:
                self._framework_id = framework_id
            if mesos_address:
                self._mesos_address = mesos_address

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
