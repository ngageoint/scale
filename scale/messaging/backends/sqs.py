"""Backend supporting AMQP 0.9.1, specifically targeting RabbitMQ message broker"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import logging

from util.aws import AWSCredentials, SQSClient
from . import MessagingBackend

logger = logging.getLogger(__name__)


class SQSMessagingBackend(MessagingBackend):
    def __init__(self):
        super(SQSMessagingBackend, self).__init__('sqs')

        self._region_name = self._broker.get_broker()

        self._credentials = AWSCredentials(self._broker.get_user_name(),
                                           self._broker.get_password())

    def send_message(self, message):
        """See :meth:`messaging.backends.MessagingBackend.send_message`
        """
        with SQSClient(self._credentials, self._region_name) as client:
            logger.debug('Sending message of type: %s', message['type'])
            client.send_message(self._queue_name, json.dumps(message))

    def receive_messages(self, batch_size):
        """See :meth:`messaging.backends.MessagingBackend.receive_messages`
        """
        with SQSClient(self._credentials, self._region_name) as client:
            for message in client.receive_messages(self._queue_name):
                try:
                    yield json.loads(message.body)
                    message.delete()
                except Exception as ex:
                    logger.exception('Failure during message processing.')
