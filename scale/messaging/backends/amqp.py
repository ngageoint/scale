"""Backend supporting AMQP 0.9.1, specifically targeting RabbitMQ message broker"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import Queue
import logging
from contextlib import closing

from kombu import Connection

from messaging.backends.backend import MessagingBackend

logger = logging.getLogger(__name__)


class AMQPMessagingBackend(MessagingBackend):
    """Backend supporting message passing via AMQP 0.9.1 broker, targeting RabbitMQ"""

    def __init__(self):
        super(AMQPMessagingBackend, self).__init__('amqp')

        # Message retrieval timeout
        self._timeout = 1

    def send_messages(self, messages):
        """See :meth:`messaging.backends.backend.MessagingBackend.send_messages`"""
        with Connection(self._broker_url) as connection:
            with closing(connection.SimpleQueue(self._queue_name)) as simple_queue:
                for message in messages:
                    logger.debug('Sending message of type: %s', message['type'])
                    simple_queue.put(message)

    def receive_messages(self, batch_size):
        """See :meth:`messaging.backends.backend.MessagingBackend.receive_messages`"""
        with Connection(self._broker_url) as connection:
            with closing(connection.SimpleQueue(self._queue_name)) as simple_queue:
                for _ in range(batch_size):
                    try:
                        message = simple_queue.get(timeout=self._timeout)

                        # Accept success back via generator send
                        success = yield message.payload
                        if success:
                            message.ack()
                    except Queue.Empty:
                        # We've reached the end of the queue... exit loop
                        break

    def get_queue_size(self):
        """See :meth:`messaging.backends.backend.MessagingBackend.get_queue_size`"""

        queue_size = 0
        with Connection(self._broker_url) as connection:
            with closing(connection.SimpleQueue(self._queue_name)) as simple_queue:
                queue_size = simple_queue.qsize()
        return queue_size
