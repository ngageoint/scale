from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import Queue
import json

import django
from django.conf import settings
from django.test import TestCase
from mock import MagicMock
from mock import call, patch

import messaging.backends.factory as backend_factory
from messaging.backends.amqp import AMQPMessagingBackend
from messaging.backends.backend import MessagingBackend
from messaging.backends.sqs import SQSMessagingBackend


# Dummy class for ABC __init__ testing
class DummyBackend(MessagingBackend):
    def __init__(self):
        super(DummyBackend, self).__init__('dummy')

    def send_messages(self, message):  # pragma: no cover
        pass

    def receive_messages(self, batch_size):  # pragma: no cover
        pass


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

        messages = [{'type': 'echo', 'body': 'yes'}]

        backend = AMQPMessagingBackend()
        backend.send_messages(messages)

        # Deep diving through context managers to assert put call
        put = connection.return_value.__enter__.return_value.SimpleQueue.return_value.put
        put.assert_called_with(messages[0])
        self.assertEquals(put.call_count, 1)

    @patch('messaging.backends.amqp.Connection')
    def test_valid_send_messages(self, connection):
        """Validate message is sent via the AMQP backend"""

        messages = [
            {'type': 'echo', 'body': '1'},
            {'type': 'echo', 'body': '2'}
        ]

        backend = AMQPMessagingBackend()
        backend.send_messages(messages)

        # Deep diving through context managers to assert put call
        put = connection.return_value.__enter__.return_value.SimpleQueue.return_value.put
        put.assert_has_calls([call(x) for x in messages])
        self.assertEquals(put.call_count, 2)

    @patch('messaging.backends.amqp.Connection')
    def test_valid_receive_messages(self, connection):
        """Validate successful message retrieval via AMQP backend"""

        message1 = MagicMock(payload={'type': 'echo', 'body': '1'})
        message2 = MagicMock(payload={'type': 'echo', 'body': '2'})
        get_func = MagicMock(side_effect=[message1, message2, Queue.Empty])

        # Deep diving through context managers to patch get call
        connection.return_value.__enter__.return_value.SimpleQueue.return_value.get = get_func

        backend = AMQPMessagingBackend()
        generator = backend.receive_messages(5)
        results = []
        try:
            results = [generator.next()]
            while True:
                results.append(generator.send(True))
        except StopIteration:
            pass

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
        generator = backend.receive_messages(2)
        result = []
        try:
            results = [generator.next()]
            while True:
                results.append(generator.send(True))
        except StopIteration:
            pass

        # wrap result in list to force generator iteration
        self.assertEqual(len(results), 2)
        message1.ack.assert_called()
        message2.ack.assert_called()
        message3.ack.assert_not_called()

    @patch('messaging.backends.amqp.Connection')
    def test_false_result_during_receive_message_yield(self, connection):
        """Validate message ack is not done with yield returns False in AMQP backend"""

        message = MagicMock()
        message.payload = 'test'
        get_func = MagicMock(return_value=message)

        # Deep diving through context managers to patch get call
        connection.return_value.__enter__.return_value.SimpleQueue.return_value.get = get_func

        backend = AMQPMessagingBackend()

        generator = backend.receive_messages(10)
        try:
            for _ in generator:
                generator.send(False)
        except StopIteration:  # pragma: no cover
            pass

        message.ack.assert_not_called()


class TestBackendsFactory(TestCase):
    def setUp(self):
        django.setup()

    def test_add_message_backend(self):
        """Validate add message backend functionality"""
        backend = DummyBackend

        backend_factory._MESSAGE_BACKENDS = {}
        backend_factory.add_message_backend(backend)
        # Yeah, not a typo... coverage
        backend_factory.add_message_backend(backend)
        self.assertEqual(backend_factory._MESSAGE_BACKENDS.keys(), ['dummy'])

    def test_successfully_get_message_backend(self):
        """Validate successful retrieval of message backend from factory"""
        backend_factory._MESSAGE_BACKENDS = {'key1': 'value1', 'key2': 'value2'}

        self.assertEqual(backend_factory.get_message_backend('key1'), 'value1')

    def test_unmatched_get_message_backend(self):
        """Validate missing message backend behavior from factory"""
        backend_factory._MESSAGE_BACKENDS = {'key1': 'value1', 'key2': 'value2'}

        with self.assertRaises(KeyError):
            backend_factory.get_message_backend('key3')

    def test_get_message_backends(self):
        """Validate listing behavior of backends from factory"""
        backend_factory._MESSAGE_BACKENDS = {'key1': 'value', 'key2': 'value'}

        self.assertEqual(backend_factory.get_message_backends(), backend_factory._MESSAGE_BACKENDS.keys())


class TestMessagingBackend(TestCase):
    def setUp(self):
        django.setup()

    @patch('messaging.backends.backend.BrokerDetails')
    def test_valid_init(self, broker_details):
        """Validate correct initialization of backend internal properties"""

        from_broker_url = MagicMock(return_value='unreal')
        broker_details.from_broker_url = from_broker_url

        backend = DummyBackend()
        self.assertEquals(backend.type, 'dummy')
        self.assertEqual(backend._broker_url, settings.BROKER_URL)
        self.assertEqual(backend._broker, 'unreal')
        self.assertEqual(backend._queue_name, settings.QUEUE_NAME)
        from_broker_url.assert_called_with(settings.BROKER_URL)


class TestSQSBackend(TestCase):
    def setUp(self):
        django.setup()

    @patch('messaging.backends.backend.BrokerDetails.from_broker_url')
    def test_valid_init(self, details):
        """Validate initialization specific to SQS backend is completed"""
        region_name = 'us-east-1'
        user_name = 'user'
        password = 'pass'

        details.return_value.get_address.return_value = region_name = 'us-east-1'
        details.return_value.get_user_name.return_value = user_name = 'user'
        details.return_value.get_password.return_value = password = 'pass'

        backend = SQSMessagingBackend()
        self.assertEqual(backend.type, 'sqs')
        self.assertEqual(backend._region_name, region_name)
        self.assertEqual(backend._credentials.access_key_id, user_name)
        self.assertEqual(backend._credentials.secret_access_key, password)

    @patch('messaging.backends.sqs.SQSClient')
    def test_valid_single_send_messages(self, client):
        """Validate message is sent via the SQS backend"""

        messages = [{'type': 'echo', 'body': 'yes'}]

        backend = SQSMessagingBackend()
        backend.send_messages(messages)

        put = client.return_value.__enter__.return_value.send_messages
        self.assertIn(json.dumps(messages[0]), str(put.mock_calls[0]))
        self.assertEquals(put.call_count, 1)

    @patch('messaging.backends.sqs.SQSClient')
    def test_valid_multiple_send_messages(self, client):
        """Validate message is sent via the SQS backend"""

        messages = [
            {'type': 'echo', 'body': '1'},
            {'type': 'echo', 'body': '2'}
        ]

        backend = SQSMessagingBackend()
        backend.send_messages(messages)

        put = client.return_value.__enter__.return_value.send_messages
        for message in messages:
            self.assertIn(json.dumps(message), str(put.mock_calls[0]))
        self.assertEquals(put.call_count, 1)

    @patch('messaging.backends.sqs.SQSClient')
    def test_valid_receive_messages(self, client):
        """Validate successful message retrieval via SQS backend"""

        message1 = MagicMock(body=json.dumps({'type': 'echo', 'body': '1'}))
        message2 = MagicMock(body=json.dumps({'type': 'echo', 'body': '2'}))
        get_func = MagicMock(return_value=[message1, message2])

        client.return_value.__enter__.return_value.receive_messages = get_func

        backend = SQSMessagingBackend()
        generator = backend.receive_messages(5)
        results = []
        try:
            results = [generator.next()]
            while True:
                results.append(generator.send(True))
        except StopIteration:
            pass

        # wrap result in list to force generator iteration
        self.assertEqual(len(results), 2)
        message1.delete.assert_called()
        message2.delete.assert_called()

    @patch('messaging.backends.sqs.SQSClient')
    def test_exception_during_receive_messages(self, client):
        """Validate exception handling during message consumption from SQS backend"""

        message = MagicMock()
        value = {'test': 'thing'}
        message.body = json.dumps(value)
        get_func = MagicMock(return_value=[message])

        client.return_value.__enter__.return_value.receive_messages = get_func

        backend = SQSMessagingBackend()

        generator = backend.receive_messages(10)
        results = []
        try:
            results = [generator.next()]
            while True:
                results.append(generator.send(False))
        except StopIteration:
            pass

        self.assertEquals(results, [value])
        message.delete.assert_not_called()
