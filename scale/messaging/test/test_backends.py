from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from mock import patch
from mock import Mock

import django
from django.conf import settings
from django.test import TestCase
from kombu import Queue

from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.backend import MessagingBackend
from messaging.backends.sqs import SQSMessagingBackend


# Dummy class for ABC __init__ testing
class ShadowBackend(MessagingBackend):
    def __init__(self, type):
        super(ShadowBackend, self).__init__(type)


class TestMessagingBackend(TestCase):
    def setUp(self):
        django.setup()

    @patch('util.broker.BrokerDetails.from_broker_url')
    def TestValidInit(self, from_broker_url):
        """Validate correct initialization of backend internal properties"""

        from_broker_url = Mock(return_value='unreal')

        backend = ShadowBackend('shadow')
        self.assertEquals(backend.type, 'shadow')
        self.assertEqual(backend._broker_url, settings.BROKER_URL)
        self.assertEqual(backend._broker, 'unreal')
        self.assertEqual(backend._queue_name, settings.QUEUE_NAME)
        from_broker_url.assert_called_with(settings.BROKER_URL)

    def TestNotImplementedErrorSendMessage(self):
        backend = ShadowBackend('shadow')
        backend.send_message('test')

    def TestNotImplementedErrorReceiveMessage(self):
        backend = ShadowBackend('shadow')
        backend.receive_messages(10)


class TestAMQPBackend(TestCase):
    def setUp(self):
        django.setup()

    def TestValidInit(self):
        """Validate initialization specific to AMQP backend is completed"""
        backend = AMQPMessagingBackend()
        self.assertEqual(backend.type, 'amqp')
        self.assertEqual(backend._timeout, 1)

    @patch('messaging.backends.amqp.Connection')
    def TestValidSendMessage(self, connection):
        """Validate message is sent via the backend"""

        message = {'type': 'echo', 'body': 'yes'}

        put_func = Mock()
        simple_queue = Mock(put_func=put_func)
        connection.SimpleQueue = Mock(return_value=simple_queue)

        backend = AMQPMessagingBackend()
        backend.send_message(message)

        put_func.assert_called_with(message)

    @patch('messaging.backends.amqp.Connection')
    def TestValidReceiveMessages(self, connection):
        """Validate successful message retrieval via AMQP backend"""

        message1 = Mock(payload={'type': 'echo', 'body': '1'})
        message2 = Mock(payload={'type': 'echo', 'body': '2'})
        get_func = Mock(return_value=[message1, message2, Queue.Empty])
        simple_queue = Mock(put_func=get_func)
        connection.SimpleQueue = Mock(return_value=simple_queue)

        backend = AMQPMessagingBackend()
        results = backend.receive_messages(10)
        results = list(results)
        self.assertEqual(len(results), 2)
        message1.ack.assert_called()
        message2.ack.assert_called()


class TestSQSBackend(TestCase):
    def setUp(self):
        django.setup()

