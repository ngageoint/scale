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
        # Register source message types
        from messaging.messages.factory import add_message_type
        from source.messages.purge_source_file import PurgeSourceFile

        add_message_type(PurgeSourceFile)
