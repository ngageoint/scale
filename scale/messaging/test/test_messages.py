from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django
from django.test import TestCase
from messaging.messages.chain import ChainCommandMessage
from messaging.messages.fail import FailCommandMessage
from mock import patch

import messaging.messages.factory as message_factory
from messaging.messages.echo import EchoCommandMessage
from messaging.messages.message import CommandMessage


# Dummy class for ABC __init__ testing
class DummyMessage(CommandMessage):
    def __init__(self):
        super(DummyMessage, self).__init__('dummy')

    def to_json(self):  # pragma: no cover
        pass

    @staticmethod
    def from_json(self, message):  # pragma: no cover
        pass

    def execute(self):  # pragma: no cover
        pass


class TestCommandMessage(TestCase):
    def setUp(self):
        django.setup()

    def test_valid_init(self):
        """Validate correct initialization of messages internal properties"""

        message = DummyMessage()
        self.assertEquals(message.type, 'dummy')
        self.assertEqual(message.new_messages, [])


class TestChainedCommandMessage(TestCase):
    def setUp(self):
        django.setup()

    def test_valid_init(self):
        """Validate correct initialization of messages internal properties"""

        message = ChainCommandMessage()
        self.assertEquals(message.type, 'chain')
        self.assertEqual(message.new_messages, [])


    def test_valid_execute(self):
        """Validate message execution logic with downstream messages for echo command"""

        message = ChainCommandMessage()
        self.assertTrue(message.execute())
        self.assertEquals(len(message.new_messages), 1)

    def test_valid_from_json(self):
        """Validate instantiation of echo command message from json"""

        payload = {'test': 'value'}
        message = ChainCommandMessage.from_json(payload)
        self.assertEquals(message._payload, payload)

    def test_valid_to_json(self):
        """Validate serialization of echo command message to json"""

        payload = {'test': 'value'}
        message = ChainCommandMessage()
        message._payload = payload
        self.assertEquals(message.to_json(), payload)


class TestEchoCommandMessage(TestCase):
    def setUp(self):
        django.setup()

    def test_valid_init(self):
        """Validate correct initialization of messages internal properties"""

        message = EchoCommandMessage()
        self.assertEquals(message.type, 'echo')
        self.assertEqual(message.new_messages, [])

    def test_valid_execute(self):
        """Validate message execution logic with downstream messages for echo command"""

        message = EchoCommandMessage()
        self.assertTrue(message.execute())

    def test_valid_from_json(self):
        """Validate instantiation of echo command message from json"""

        payload = {'test': 'value'}
        message = EchoCommandMessage.from_json(payload)
        self.assertEquals(message._payload, payload)

    def test_valid_to_json(self):
        """Validate serialization of echo command message to json"""

        payload = {'test': 'value'}
        message = EchoCommandMessage()
        message._payload = payload
        self.assertEquals(message.to_json(), payload)

class TestFailingCommandMessage(TestCase):
    def setUp(self):
        django.setup()

    def test_valid_init(self):
        """Validate correct initialization of messages internal properties"""

        message = FailCommandMessage()
        self.assertEquals(message.type, 'failing')
        self.assertEqual(message.new_messages, [])

    def test_valid_execute(self):
        """Validate message execution logic with downstream messages for echo command"""

        message = FailCommandMessage()
        self.assertFalse(message.execute())

    def test_valid_from_json(self):
        """Validate instantiation of echo command message from json"""

        payload = {'test': 'value'}
        message = FailCommandMessage.from_json(payload)
        self.assertEquals(message._payload, payload)

    def test_valid_to_json(self):
        """Validate serialization of echo command message to json"""

        payload = {'test': 'value'}
        message = FailCommandMessage()
        message._payload = payload
        self.assertEquals(message.to_json(), payload)


class TestMessagesFactory(TestCase):
    def setUp(self):
        django.setup()

    def test_add_message_type(self):
        """Validate add message type functionality"""
        message = DummyMessage

        message_factory._MESSAGE_TYPES = {}
        message_factory.add_message_type(message)
        # Yeah, not a typo... coverage
        message_factory.add_message_type(message)
        self.assertEqual(message_factory._MESSAGE_TYPES.keys(), ['dummy'])

    def test_successfully_get_message_backend(self):
        """Validate successful retrieval of message type from factory"""
        message_factory._MESSAGE_TYPES = {'key1': 'value1', 'key2': 'value2'}

        self.assertEqual(message_factory.get_message_type('key1'), 'value1')

    def test_unmatched_get_message_backend(self):
        """Validate missing message type behavior of factory"""
        message_factory._MESSAGE_TYPES = {'key1': 'value1', 'key2': 'value2'}

        with self.assertRaises(KeyError):
            message_factory.get_message_type('key3')

    def test_get_message_backends(self):
        """Validate listing behavior of types from factory"""
        message_factory._MESSAGE_TYPES = {'key1': 'value', 'key2': 'value'}

        self.assertEqual(message_factory.get_message_types(), message_factory._MESSAGE_TYPES.keys())
