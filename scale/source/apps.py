"""Defines the application configuration for the source application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class SourceConfig(AppConfig):
    """Configuration for the source app
    """
    name = 'source'
    label = 'source'
    verbose_name = 'Source'

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """

        from job.configuration.data.data_file import DATA_FILE_PARSE_SAVER
        from source.configuration.source_data_file import SourceDataFileParseSaver
        from source.triggers.parse_trigger_handler import ParseTriggerHandler
        from trigger.handler import register_trigger_rule_handler

        # Register source file parse saver
        DATA_FILE_PARSE_SAVER['DATA_FILE_PARSE_SAVER'] = SourceDataFileParseSaver()

        # Register parse trigger rule handler
        register_trigger_rule_handler(ParseTriggerHandler())
