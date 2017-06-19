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
    def send_message(self, message):
        """Send a single message to the backend

        Presently connections are not persisted across send_message calls.
        We could greatly improve message throughput if we managed this at the
        class instance level. This isn't really a major concern as bottlenecks are
        not from the sender perspective.

        :param message: JSON payload
        :type message: dict
        """

    @abstractmethod
    def receive_messages(self, batch_size):
        """Receive a batch of messages from the backend

        TODO: Presently connections are not persisted across receive_message calls.
        We could greatly improve message throughput if we managed this at the
        class instance level. This isn't a huge concern as we are sharing the
        connection across the batch_size.

        Implementing function must yield messages from backend. Messages must be
        in dict.

        :param batch_size: Number of messages to be processed
        :type batch_size: int
        :return: Yielded list of messages
        :rtype: [dict]
        """