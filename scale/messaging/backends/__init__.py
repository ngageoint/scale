from __future__ import unicode_literals

from abc import ABCMeta
from collections import namedtuple

from django.conf import settings


class MessagingBackend(object):

    __metaclass__ = ABCMeta

    def __init__(self, backend_type):
        """Instantiates backend specific settings 
        """

        # Unique type of MessagingBackend, each type must be registered in apps.py
        self.type = backend_type

        # Connection string pulled from configuration
        self.broker_url = settings.BROKER_URL

        # TODO: Transition to more advanced message routing per command message type
        self.queue_name = settings.QUEUE_NAME

    def send_message(self, message):
        """Send a single message to the backend
        
        Presently connections are not persisted across send_message calls.
        We could greatly improve message throughput if we managed this at the
        instance level. This isn't really a major concern as bottlenecks are
        not from the sender perspective.

        :param message: stringified JSON payload
        :type message: string
        """
        raise NotImplementedError

    def receive_messages(self, batch_size, callback):
        """Receive a batch of messages from the backend
        
        TODO: Presently connections are not persisted across receive_message calls.
        We could greatly improve message throughput if we managed this at the
        instance level. This isn't really a major concern as bottlenecks are
        not from the sender perspective. We are sharing the connection across
        the batch_size.

        :param batch_size: Number of messages to be processed
        :type batch_size: int
        :param callback: Function pointer to 
        :return:
        :rtype: [string]
        """
        raise NotImplementedError
