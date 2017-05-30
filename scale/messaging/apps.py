"""Defines the application configuration for the scale messaging application"""
from __future__ import unicode_literals
from django.apps import AppConfig


class MessagingConfig(AppConfig):
    """Configuration for the metrics app"""
    name = 'messaging'
    label = 'messaging'
    verbose_name = 'Message passing'

    def ready(self):
        """Registers the messaging factory methods."""
        import message.factory as factory

        from message.echo import EchoCommandMessage

        # # Register message types
        factory.add_message_type(EchoCommandMessage)