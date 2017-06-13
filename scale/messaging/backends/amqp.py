"""Backend supporting AMQP 0.9.1, specifically targeting RabbitMQ message broker"""
from __future__ import unicode_literals

import logging
import Queue

from contextlib import closing

from kombu import Connection

from . import MessagingBackend

logger = logging.getLogger(__name__)


class AMQPMessagingBackend(MessagingBackend):
    def __init__(self):
        super(AMQPMessagingBackend, self).__init__('amqp')

        # Message retrieval timeout
        self.timeout = 1
        
        # Default serializer is json, but let's be explicit
        self.serializer = 'json'

    def send_message(self, message):
        """See :meth:`messaging.backends.MessagingBackend.send_message`
        """
        with Connection(self.broker_url) as connection:
            with closing(connection.SimpleQueue(self.queue_name)) as simple_queue:
                simple_queue.put(message, serializer=self.serializer)

    def receive_messages(self, batch_size, callback):
        """See :meth:`messaging.backends.MessagingBackend.receive_messages`
        """
        with Connection(self.broker_url) as connection:
            with closing(connection.SimpleQueue(self.queue_name)) as simple_queue:
                for _ in range(batch_size):
                    try:
                        message = simple_queue.get(timeout=self.timeout)
                    
                        try:
                            callback(message.payload)
                            message.ack()
                        except Exception as ex:
                            logger.exception('Failure during message processing.')
                    except Queue.Empty:
                        # We've reached the end of the queue... exit loop
                        break
