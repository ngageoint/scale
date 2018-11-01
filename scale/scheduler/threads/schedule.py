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

    def __init__(self, client):
        """Constructor

        :param driver: The Mesos scheduler client
        :type driver: :class:`mesoshttp.client.MesosClient`
        """

        super(SchedulingThread, self).__init__('Scheduling', THROTTLE, WARN_THRESHOLD)
        self._client = client
        self._manager = SchedulingManager()

    @property
    def client(self):
        """Returns the client

        :returns: The client
        :rtype: :class:`mesoshttp.client.MesosClient`
        """

        return self._driver

    @client.setter
    def client(self, value):
        """Sets the driver

        :param value: The client
        :type value: :class:`mesoshttp.client.MesosClient`
        """

        self._driver = value

    def _execute(self):
        """See :meth:`scheduler.threads.base_thread.BaseSchedulerThread._execute`
        """

        self._manager.perform_scheduling(self._client, now())
