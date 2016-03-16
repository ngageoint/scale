"""Defines the application configuration for the queue application"""
from django.apps import AppConfig


class QueueConfig(AppConfig):
    """Configuration for the queue app
    """
    name = u'queue'
    label = u'queue'
    verbose_name = u'Queue'

    def ready(self):
        """Registers the job load metrics processor with the clock system."""
        import job.clock as clock
        from queue.job_load import JobLoadProcessor

        clock.register_processor('scale-job-load', JobLoadProcessor)
