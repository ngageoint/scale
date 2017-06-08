"""Defines the class that manages the scheduling background thread"""
from __future__ import unicode_literals

import datetime

from django.utils.timezone import now

from scheduler.scheduling.manager import SchedulingManager
from scheduler.threads.base_thread import BaseSchedulerThread


THROTTLE = datetime.timedelta(seconds=1)
WARN_THRESHOLD = datetime.timedelta(seconds=1)


class SchedulingThread(BaseSchedulerThread):
    """This class manages the scheduling background thread for the scheduler"""

    def __init__(self, driver):
        """Constructor

        :param driver: The Mesos scheduler driver
        :type driver: :class:`mesos_api.mesos.SchedulerDriver`
        """

        super(SchedulingThread, self).__init__('Scheduling', THROTTLE, WARN_THRESHOLD)
        self._driver = driver
        self._manager = SchedulingManager()

    @property
    def driver(self):
        """Returns the driver

        :returns: The driver
        :rtype: :class:`mesos_api.mesos.SchedulerDriver`
        """

        return self._driver

    @driver.setter
    def driver(self, value):
        """Sets the driver

        :param value: The driver
        :type value: :class:`mesos_api.mesos.SchedulerDriver`
        """

        self._driver = value

    def _execute(self):
        """See :meth:`scheduler.threads.base_thread.BaseSchedulerThread._execute`
        """

        self._manager.perform_scheduling(self._driver, now())
