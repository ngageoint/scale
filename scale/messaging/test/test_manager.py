from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django
from django.test import TestCase
from messaging.exceptions import CommandMessageExecuteFailure, InvalidCommandMessage
from messaging.messages.message import CommandMessage
from messaging.manager import CommandMessageManager
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
        send_message = MagicMock()
        manager._backend = MagicMock(send_message=send_message)
        manager.send_message(command)

        send_message.assert_called_with(call({'type': 'test', 'body': 'body_content'}))

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

    @patch('messaging.manager.CommandMessageManager._send_downstream')
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

    @patch('messaging.manager.CommandMessageManager._send_downstream')
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

    @patch('messaging.manager.get_message_type')
    def test_valid_extract_command(self, get_message_type):
        """Validate a successful _extract_command call instantiation of CommandMessage class from payload"""
        message = {'type': 'test', 'body': 'payload'}

        from_json = MagicMock(return_value=MagicMock(spec=CommandMessage))
        message_class = MagicMock(from_json=from_json)
        get_message_type.return_value = message_class
        result = CommandMessageManager._extract_command(message)

        get_message_type.assert_called_once()
        message_class.from_json.assert_called_with(message['body'])
        self.assertTrue(isinstance(result, CommandMessage))

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

    @patch('messaging.manager.get_message_type')
    def test_no_registered_type_extract_command(self, get_message_type):
        """Validate InvalidCommandMessage is raised when no type matches"""
        message = {'type': 'test', 'body': 'payload'}

        get_message_type.side_effect = KeyError
        with self.assertRaises(InvalidCommandMessage):
            CommandMessageManager._extract_command(message)
