from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django
from django.test import TestCase
from messaging.exceptions import CommandMessageExecuteFailure, InvalidCommandMessage
from messaging.message import CommandMessage
from messaging.messages import CommandMessageManager
from mock import MagicMock, Mock
from mock import call, patch


class TestCommandMessageManager(TestCase):
    def setUp(self):
        django.setup()

    def test_send_message(self):
        """Validate that send_message composes dict with `type` and `body` keys for backend"""
        command = MagicMock(message_type='test')
        command.to_json = MagicMock(return_value='body_content')
        manager = CommandMessageManager()
        manager._backend = MagicMock()
        manager.send_message(command)

        manager._backend.send_message.assert_called_with({'type': 'test', 'body': 'body_content'})

    def test_send_message_no_type(self):
        """Validate that send_message raises AttributeError when message_type is not available"""

        class InvalidCommand(object):
            def to_json(self):
                pass

        message = InvalidCommand()
        manager = CommandMessageManager()

        with self.assertRaises(AttributeError):
            manager.send_message(message)

    def test_send_message_no_serializer(self):
        """Validate that send_message raises AttributeError when to_json is not available"""

        class InvalidCommand(object):
            def __init__(self):
                self.message_type = 'test'

        message = InvalidCommand()
        manager = CommandMessageManager()

        with self.assertRaises(AttributeError):
            manager.send_message(message)

    def test_receive_message(self):
        """Validate the receive_message calls _process_message with each result"""

        mocks = [MagicMock() for _ in range(10)]
        manager = CommandMessageManager()
        manager._backend = MagicMock()
        process_message = manager._process_message = Mock()
        manager._backend.receive_messages = Mock(return_value=mocks)
        manager.receive_messages()

        calls = [call(x) for x in mocks]
        process_message.assert_has_calls(calls)
        self.assertEquals(process_message.call_count, 10)

    @patch('messaging.messages.CommandMessageManager._send_downstream')
    def test_successful_process_message(self, send_downstream):
        """Validate logic for a successful command process """

        message = {'type': 'test', 'body': 'payload'}

        manager = CommandMessageManager()
        command = Mock()
        command.execute = Mock(return_value=True)
        command.new_messages = []
        extract_command = manager._extract_command = Mock(return_value=command)

        manager._process_message(message)

        extract_command.assert_called_once()
        send_downstream.assert_called_with([])

    @patch('messaging.messages.CommandMessageManager._send_downstream')
    def test_failing_process_message(self, send_downstream):
        """Validate logic for a successful command process """

        message = {'type': 'test', 'body': 'payload'}

        manager = CommandMessageManager()
        command = Mock()
        command.execute = Mock(return_value=False)
        extract_command = manager._extract_command = Mock(return_value=command)

        with self.assertRaises(CommandMessageExecuteFailure):
            manager._process_message(message)

        extract_command.assert_called_once()
        self.assertFalse(send_downstream.called)

    def test_successful_send_downstream(self):
        """Validate call of send_message for each downstream message"""

        messages = ['one', 'two']

        manager = CommandMessageManager()
        send_message = manager._send_message = Mock()
        manager._send_downstream(messages)

        calls = [call(x) for x in messages]
        send_message.assert_has_calls(calls)

    def test_no_message_send_downstream(self):
        """Validate send_message is not called when messages is empty"""

        manager = CommandMessageManager()
        send_message = manager.send_message = Mock()
        manager._send_downstream([])

        self.assertFalse(send_message.called)

    @patch('message.message.factory.get_message_type')
    def test_valid_extract_command(self, get_message_type):
        """Validate a successful _extract_command call instantiation of CommandMessage class from payload"""
        message = {'type': 'test', 'body': 'payload'}

        message_class = Mock(spec=CommandMessage)
        get_message_type = Mock(return_value=message_class)
        result = CommandMessageManager._extract_command(message)

        get_message_type.assert_called_once()
        self.assertEquals(result, message_class)

    def test_missing_type_extract_command(self):
        """Validate InvalidCommandMessage is raised when missing type key"""
        message = {'body': 'payload'}

        with self.assertRaises(InvalidCommandMessage):
            CommandMessageManager._extract_command(message)

    def test_missing_body_extract_command(self):
        """Validate InvalidCommandMessage is raised when missing body key"""
        message = {'type': 'test'}

        with self.assertRaises(InvalidCommandMessage):
            CommandMessageManager._extract_command(message)

    def test_no_registered_type_extract_command(self):
        """Validate InvalidCommandMessage is raised when no type matches"""
        message = {'type': 'test', 'body': 'payload'}

        get_message_type = Mock(side_effect=KeyError)
        with self.assertRaises(InvalidCommandMessage):
            CommandMessageManager._extract_command(message)
