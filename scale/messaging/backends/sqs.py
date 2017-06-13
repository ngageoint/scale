"""Backend supporting AMQP 0.9.1, specifically targeting RabbitMQ message broker"""
from __future__ import unicode_literals

import json
import logging

from django.conf import settings

from . import MessagingBackend
from util.aws import AWSCredentials, SQSClient

logger = logging.getLogger(__name__)


class SQSMessagingBackend(MessagingBackend):
    def __init__(self):
        super(SQSMessagingBackend, self).__init__('sqs')

        
        self._region_name = settings.AWS_REGION_NAME
        
        self._credentials = AWSCredentials(settings.AWS_ACCESS_KEY, settings.AWS_SECRET_KEY)

    def send_message(self, message):
        """See :meth:`messaging.backends.MessagingBackend.send_message`
        """
        with SQSClient(self._credentials, self._region_name) as client:
            client.send_message(self.queue_name, json.dumps(message))

    def receive_messages(self, batch_size, callback):
        """See :meth:`messaging.backends.MessagingBackend.receive_messages`
        """
        with SQSClient(self._credentials, self._region_name) as client:
            for message in client.receive_messages(self.queue_name):
                try:
                    callback(json.loads(message.body))
                    message.delete()
                except Exception as ex:
                    logger.exception('Failure during message processing.')

