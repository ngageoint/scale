"""Defines the application configuration for the job application"""
from __future__ import absolute_import
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
        from job.configuration.results.exceptions import InvalidResultsManifest, MissingRequiredOutput
        from job.execution.configuration.exceptions import MissingMount, MissingSetting

        register_error(InvalidResultsManifest(''))
        register_error(MissingMount(''))
        register_error(MissingRequiredOutput(''))
        register_error(MissingSetting(''))

        # Register job message types
        from job.messages.blocked_jobs import BlockedJobs
        from job.messages.cancel_jobs import CancelJobs
        from job.messages.cancel_jobs_bulk import CancelJobsBulk
        from job.messages.completed_jobs import CompletedJobs
        from job.messages.failed_jobs import FailedJobs
        from job.messages.job_exe_end import CreateJobExecutionEnd
        from job.messages.pending_jobs import PendingJobs
        from job.messages.process_job_input import ProcessJobInput
        from job.messages.publish_job import PublishJob
        from job.messages.running_jobs import RunningJobs
        from job.messages.uncancel_jobs import UncancelJobs
        from job.messages.unpublish_jobs import UnpublishJobs
        from messaging.messages.factory import add_message_type

        add_message_type(BlockedJobs)
        add_message_type(CancelJobs)
        add_message_type(CancelJobsBulk)
        add_message_type(CompletedJobs)
        add_message_type(FailedJobs)
        add_message_type(CreateJobExecutionEnd)
        add_message_type(PendingJobs)
        add_message_type(ProcessJobInput)
        add_message_type(PublishJob)
        add_message_type(RunningJobs)
        add_message_type(UncancelJobs)
        add_message_type(UnpublishJobs)
