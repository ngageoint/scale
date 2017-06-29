"""Defines the class represents the scheduler configuration"""
from __future__ import unicode_literals

from queue.models import DEFAULT_QUEUE_ORDER


class SchedulerConfiguration(object):
    """This class represents the scheduler configuration"""

    def __init__(self, scheduler=None):
        """Constructor

        :param scheduler: The scheduler model, possibly None
        :type scheduler: :class:`scheduler.models.Scheduler`
        """

        self.is_paused = True
        self.queue_mode = DEFAULT_QUEUE_ORDER

        if scheduler:
            self.is_paused = scheduler.is_paused
            self.queue_mode = scheduler.queue_mode
