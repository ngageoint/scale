from __future__ import unicode_literals

from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    """Configuration for the scheduler app
    """
    name = 'scheduler'
    label = 'scheduler'
    verbose_name = 'Scheduler'

    def ready(self):
        """Registers components related to the scheduler"""

        # Register scheduler message types
        from messaging.messages.factory import add_message_type
        from scheduler.messages.restart_scheduler import RestartScheduler

        add_message_type(RestartScheduler)
