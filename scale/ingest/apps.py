"""The Scale ingest application"""
from __future__ import unicode_literals

from django.apps import AppConfig


class IngestConfig(AppConfig):
    """Configuration for the ingest app
    """
    name = 'ingest'
    label = 'ingest'
    verbose_name = 'Ingest'

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """

        from ingest.triggers.ingest_trigger_handler import IngestTriggerHandler
        from trigger.handler import register_trigger_rule_handler

        # Register ingest trigger rule handler
        register_trigger_rule_handler(IngestTriggerHandler())
