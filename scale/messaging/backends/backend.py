from abc import ABCMeta, abstractmethod

from django.conf import settings

from util.broker import BrokerDetails


class MessagingBackend(object):
    __metaclass__ = ABCMeta

    def __init__(self, backend_type):
        """Instantiates backend specific settings
        """

        # Unique type of MessagingBackend, each type must be registered in apps.py
        self.type = backend_type

        # Connection string pulled from configuration
        self._broker_url = settings.BROKER_URL
        self._broker = BrokerDetails.from_broker_url(settings.BROKER_URL)

        # TODO: Transition to more advanced message routing per command message type
        self._queue_name = settings.QUEUE_NAME

    @abstractmethod
    def send_messages(self, messages):
        """Send a collection of messages to the backend
        
        Connections are not persisted across send_messages calls. It is recommended that if a large
        number of messages are to be sent it be done directly in a single function call.

        :param messages: JSON payload of messages
        :type messages: [dict]
        """

    @abstractmethod
    def receive_messages(self, batch_size):
        """Receive a batch of messages from the backend


        Connections are not persisted across receive_messages calls. It is recommended that if a large
        number of messages are to be retrieved it be done directly in a single function call.

        Implementing function must yield messages from backend. Messages must be
        in dict.

        :param batch_size: Number of messages to be processed
        :type batch_size: int
        :return: Yielded list of messages
        :rtype: Generator[dict]
        """
