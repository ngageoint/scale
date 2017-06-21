"""Defines the application configuration for the scale messaging application"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.apps import AppConfig

"""Registers the messaging factory methods."""
from messaging.messages.factory import add_message_type
from .backends.factory import add_message_backend

from messaging.messages.echo import EchoCommandMessage
from .backends.amqp import AMQPMessagingBackend
from .backends.sqs import SQSMessagingBackend


class MessagingConfig(AppConfig):
    """Configuration for the messaging app"""
    name = 'messaging'
    label = 'Messaging'
    verbose_name = 'Message passing'

    def ready(self):
        # # Register message types
        add_message_type(EchoCommandMessage)

        # Register message backends
        add_message_backend(AMQPMessagingBackend)
        add_message_backend(SQSMessagingBackend)
