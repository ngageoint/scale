from abc import ABCMeta
from collections import namedtuple

from django.conf import settings

MessageObject = namedtuple('MessagingObject', ['body', 'backend_object'])

class MessagingBackend(object):

    __metaclass__ = ABCMeta

    def __init__(self, backend_type):

        # Unique type of MessagingBackend, each type must be registered in apps.py
        self.type = type

        # Connection string pulled from configuration
        self.broker_url = settings.SCALE_BROKER_URL

        # TODO: Transition to more advanced message routing per command message type
        self.queue_name = 'scale-command-messages'

    def send_message(self, message):
        """

        :param message:
        :type message:
        """
        raise NotImplementedError

    def receive_messages(self, batch_size, callback):
        """

        :param batch_size:
        :param callback:
        :return:
        :rtype: [string]
        """
        raise NotImplementedError
