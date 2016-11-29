"""Defines the class that manages high-level scheduler configuration"""
from __future__ import unicode_literals

import threading

from scheduler.models import Scheduler


class SchedulerManager(object):
    """This class manages the high-level scheduler configuration. It is a combination of data from both the Scale
    database and the Mesos master. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._framework_id = None
        self._lock = threading.Lock()
        self._mesos_address = None
        self._scheduler = None

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

    def is_paused(self):
        """Indicates whether the scheduler is currently paused or not

        :returns: True if the scheduler is paused, False otherwise
        :rtype: bool
        """

        with self._lock:
            if not self._scheduler:
                return True
            return self._scheduler.is_paused

    def sync_with_database(self):
        """Syncs with the database to retrieve an updated scheduler model
        """

        scheduler = Scheduler.objects.first()

        with self._lock:
            self._scheduler = scheduler

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


scheduler_mgr = SchedulerManager()
