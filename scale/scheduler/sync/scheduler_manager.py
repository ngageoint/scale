"""Defines the class that manages the syncing of the scheduler with the scheduler model"""
from __future__ import unicode_literals

import threading

from scheduler.models import Scheduler


class SchedulerManager(object):
    """This class manages the syncing of the scheduler with the scheduler model that contains cluster-wide scheduling
    configuration. This class is thread-safe."""

    def __init__(self, scheduler=None):
        """Constructor

        :param scheduler: The scheduler model
        :type scheduler: :class:`scheduler.models.Scheduler`
        """

        self._lock = threading.Lock()
        self._scheduler = scheduler

    def get_scheduler(self):
        """Returns the scheduler model

        :returns: The scheduler model
        :rtype: :class:`scheduler.models.Scheduler`
        """

        with self._lock:
            return self._scheduler

    def is_paused(self):
        """Indicates whether the scheduler is currently paused or not

        :returns: True if the scheduler is paused, False otherwise
        :rtype: bool
        """

        with self._lock:
            return self._scheduler.is_paused

    def sync_with_database(self):
        """Syncs with the database to retrieve an updated scheduler model
        """

        scheduler = Scheduler.objects.first()

        with self._lock:
            self._scheduler = scheduler
