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
        """Registers job errors"""
        from error.exceptions import register_error
        from job.configuration.exceptions import MissingMount, MissingSetting
        from job.configuration.results.exceptions import InvalidResultsManifest, MissingRequiredOutput

        register_error(InvalidResultsManifest(''))
        register_error(MissingMount(''))
        register_error(MissingRequiredOutput(''))
        register_error(MissingSetting(''))
