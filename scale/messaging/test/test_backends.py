from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import Queue
from mock import call, patch
from mock import MagicMock

import django
from django.conf import settings
from django.test import TestCase

from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.backend import MessagingBackend
from messaging.backends.sqs import SQSMessagingBackend


# Dummy class for ABC __init__ testing
class ShadowBackend(MessagingBackend):
    def __init__(self, type):
        super(ShadowBackend, self).__init__(type)

    def send_message(self, message):
        pass

    def receive_messages(self, batch_size):
        pass


class TestMessagingBackend(TestCase):
    def setUp(self):
        django.setup()

    @patch('messaging.backends.backend.BrokerDetails')
    def test_valid_init(self, broker_details):
        """Validate correct initialization of backend internal properties"""

        from_broker_url = MagicMock(return_value='unreal')
        broker_details.from_broker_url = from_broker_url

        backend = ShadowBackend('shadow')
        self.assertEquals(backend.type, 'shadow')
        self.assertEqual(backend._broker_url, settings.BROKER_URL)
        self.assertEqual(backend._broker, 'unreal')
        self.assertEqual(backend._queue_name, settings.QUEUE_NAME)
        from_broker_url.assert_called_with(settings.BROKER_URL)


class TestAMQPBackend(TestCase):
    def setUp(self):
        django.setup()

    def test_valid_init(self):
        """Validate initialization specific to AMQP backend is completed"""
        backend = AMQPMessagingBackend()
        self.assertEqual(backend.type, 'amqp')
        self.assertEqual(backend._timeout, 1)

    @patch('messaging.backends.amqp.Connection')
    def test_valid_send_message(self, connection):
        """Validate message is sent via the AMQP backend"""

        message = {'type': 'echo', 'body': 'yes'}

        backend = AMQPMessagingBackend()
        backend.send_message(message)

        # Deep diving through context managers to assert put call
        put = connection.return_value.__enter__.return_value.SimpleQueue.return_value.put
        put.assert_called_with(message)

    @patch('messaging.backends.amqp.Connection')
    def test_valid_receive_message(self, connection):
        """Validate successful message retrieval via AMQP backend"""

        message1 = MagicMock(payload={'type': 'echo', 'body': '1'})
        message2 = MagicMock(payload={'type': 'echo', 'body': '2'})
        get_func = MagicMock(side_effect=[message1, message2, Queue.Empty])
        
        # Deep diving through context managers to patch get call
        connection.return_value.__enter__.return_value.SimpleQueue.return_value.get = get_func

        backend = AMQPMessagingBackend()
        results = backend.receive_messages(5)
        # wrap result in list to force generator iteration
        results = list(results)
        self.assertEqual(len(results), 2)
        message1.ack.assert_called()
        message2.ack.assert_called()
        
    @patch('messaging.backends.amqp.Connection')
    def test_valid_single_batch_receive_message(self, connection):
        """Validate successful message retrieval via AMQP backend of first 2 messages"""

        message1 = MagicMock(payload={'type': 'echo', 'body': '1'})
        message2 = MagicMock(payload={'type': 'echo', 'body': '2'})
        message3 = MagicMock(payload={'type': 'echo', 'body': '3'})
        get_func = MagicMock(side_effect=[message1, message2, Queue.Empty])
        
        # Deep diving through context managers to patch get call
        connection.return_value.__enter__.return_value.SimpleQueue.return_value.get = get_func

        backend = AMQPMessagingBackend()
        results = backend.receive_messages(2)
        # wrap result in list to force generator iteration
        results = list(results)
        self.assertEqual(len(results), 2)
        message1.ack.assert_called()
        message2.ack.assert_called()
        message3.ack.assert_not_called()

    @patch('messaging.backends.amqp.Connection')
    def test_exception_during_receive_message(self, connection):
        """Validate exception handling during message consumption from AMQP backend"""

        message = MagicMock()
        message.payload.side_effect = Exception
        get_func = MagicMock(return_value=[message])
        
        # Deep diving through context managers to patch get call
        connection.return_value.__enter__.return_value.SimpleQueue.return_value.get = get_func

        backend = AMQPMessagingBackend()
        
        for _ in backend.receive_messages(10):
            pass
        
        message.ack.assert_not_called()
        

class TestSQSBackend(TestCase):
    def setUp(self):
        django.setup()

