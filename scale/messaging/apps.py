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
        from .message.factory import add_message_type
        from .backends.factory import add_message_backend

        from .message.echo import EchoCommandMessage
        from .backends.amqp import AMQPMessagingBackend
        from .backends.sqs import SQSMessagingBackend

        # # Register message types
        add_message_type(EchoCommandMessage)
        
        # Register message backends
        add_message_backend(AMQPMessagingBackend)
        add_message_backend(SQSMessagingBackend)