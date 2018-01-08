"""Defines the class represents the scheduler configuration"""
from __future__ import unicode_literals

from queue.models import DEFAULT_QUEUE_ORDER


DEFAULT_NUM_MESSAGE_HANDLERS = 0
DEFAULT_LOGGING_LEVEL = 'INFO'

class SchedulerConfiguration(object):
    """This class represents the scheduler configuration"""

    def __init__(self, scheduler=None):
        """Constructor

        :param scheduler: The scheduler model, possibly None
        :type scheduler: :class:`scheduler.models.Scheduler`
        """

        self.is_paused = True
        self.num_message_handlers = DEFAULT_NUM_MESSAGE_HANDLERS
        self.queue_mode = DEFAULT_QUEUE_ORDER
        self.system_job_logging_level = DEFAULT_LOGGING_LEVEL

        if scheduler:
            self.is_paused = scheduler.is_paused
            self.num_message_handlers = scheduler.num_message_handlers
            self.queue_mode = scheduler.queue_mode
            self.system_job_logging_level = scheduler.system_job_logging_level 
