"""Defines the application configuration for the job application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class JobConfig(AppConfig):
    """Configuration for the job app
    """
    name = 'job'
    label = 'job'
    verbose_name = 'Job'

    def ready(self):
        """Registers components related to jobs"""

        # Register job errors
        from error.exceptions import register_error
        from job.configuration.exceptions import MissingMount, MissingSetting
        from job.configuration.results.exceptions import InvalidResultsManifest, MissingRequiredOutput

        register_error(InvalidResultsManifest(''))
        register_error(MissingMount(''))
        register_error(MissingRequiredOutput(''))
        register_error(MissingSetting(''))

        # Register job message types
        from job.messages.blocked_jobs import BlockedJobs
        from job.messages.job_exe_end import CreateJobExecutionEnd
        from job.messages.pending_jobs import PendingJobs
        from job.messages.running_jobs import RunningJobs
        from messaging.messages.factory import add_message_type

        add_message_type(BlockedJobs)
        add_message_type(CreateJobExecutionEnd)
        add_message_type(PendingJobs)
        add_message_type(RunningJobs)
