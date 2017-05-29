# Backend supporting AMQP 0.9.1, specifically targeting RabbitMQ message broker

import logging

from kombu import Connection

from . import backend

logger = logging.getLogger(__name__)

class AMQPMessagingBackend(backend.MessagingBackend):
    def __init__(self):
        super(AMQPMessagingBackend, self).__init__('amqp')

        # Message retrieval timeout
        self.timeout = 1

    def send_message(self, message):
        with Connection(self.broker_url) as connection:
            simple_queue = connection.SimpleQueue(self.queue_name)
            simple_queue.put(message)

    def receive_messages(self, batch_size, callback):
        with Connection(self.broker_url) as connection:
            simple_queue = connection.SimpleQueue(self.queue_name)
            for _ in range(batch_size):
                message = simple_queue.get(timeout=self.timeout)
                try:
                    callback(message.payload)
                    message.ack()
                except Exception as ex:
                    logger.exception('Failure during message processing.')
