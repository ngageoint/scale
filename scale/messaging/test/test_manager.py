from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import MagicMock
from mock import call, patch

from messaging.exceptions import CommandMessageExecuteFailure, InvalidCommandMessage
from messaging.manager import CommandMessageManager
from messaging.messages.message import CommandMessage


class TestCommandMessageManager(TestCase):
    def setUp(self):
        django.setup()

        # Stomp singleton for unit testing.
        @classmethod
        def manager_new(self, cls):
            """Removed Singleton from manager"""

            return super(CommandMessageManager, cls).__new__(cls)
            
        def manager_init(self):
            pass
            

        self.new_patcher = patch('messaging.manager.CommandMessageManager.__new__', manager_new)
        self.init_patcher = patch('messaging.manager.CommandMessageManager.__init__', manager_init)
        self.new_patcher.start()
        self.init_patcher.start()

    def tearDown(self):
        self.new_patcher.stop()
        self.init_patcher.stop()

    def test_send_message(self):
        """Validate that send_message composes dict with `type` and `body` keys for backend"""
        command = MagicMock(type='test')
        command.to_json.return_value = 'body_content'
        manager = CommandMessageManager()
        send_messages = MagicMock()
        backend = MagicMock(send_messages=send_messages)
        manager._backend = backend

        manager.send_messages([command])

        send_messages.assert_called_with([{'type': 'test', 'body': 'body_content'}])

    def test_send_messages_no_type(self):
        """Validate that send_message raises AttributeError when message type is not available"""

        class InvalidCommand(object):
            def to_json(self):  # pragma: no cover
                pass

        message = InvalidCommand()
        manager = CommandMessageManager()

        with self.assertRaises(AttributeError):
            manager.send_messages([message])

    def test_send_message_no_serializer(self):
        """Validate that send_message raises AttributeError when to_json is not available"""

        class InvalidCommand(object):
            def __init__(self):
                self.type = 'test'

        message = InvalidCommand()
        manager = CommandMessageManager()

        with self.assertRaises(AttributeError):
            manager.send_messages([message])

    def test_receive_message(self):
        """Validate the receive_message calls _process_message with each result"""

        mocks = [MagicMock() for _ in range(10)]

        def gen():
            for mock in mocks:
                yield mock

        manager = CommandMessageManager()
        manager._backend = MagicMock()
        process_message = manager._process_message = MagicMock()
        manager._backend.receive_messages = MagicMock(return_value=gen())
        manager.receive_messages()

        calls = [call(x) for x in mocks]
        process_message.assert_has_calls(calls)
        self.assertEquals(process_message.call_count, 10)

    @patch('messaging.manager.CommandMessageManager._extract_command')
    @patch('messaging.manager.CommandMessageManager._send_downstream')
    def test_successful_process_message(self, send_downstream, extract_command):
        """Validate logic for a successful command process """

        message = {'type': 'test', 'body': 'payload'}

        manager = CommandMessageManager()
        command = MagicMock(execute=MagicMock(return_value=True))
        command.execute.return_value = True
        command.new_messages = []
        extract_command.return_value = command

        manager._process_message(message)

        send_downstream.assert_called_with([])

    @patch('messaging.manager.CommandMessageManager._extract_command')
    @patch('messaging.manager.CommandMessageManager._send_downstream')
    def test_failing_process_message(self, send_downstream, extract_command):
        """Validate logic for a process message failing in process execution"""

        message = {'type': 'test', 'body': 'payload'}

        manager = CommandMessageManager()
        command = MagicMock()
        command.execute = MagicMock(return_value=False)
        extract_command.return_value = command

        with self.assertRaises(CommandMessageExecuteFailure):
            manager._process_message(message)

        self.assertFalse(send_downstream.called)

    @patch('messaging.manager.CommandMessageManager.send_messages')
    def test_successful_send_downstream(self, send_messages):
        """Validate call of send_message for each downstream message"""

        messages = ['one', 'two']

        manager = CommandMessageManager()
        manager._send_downstream(messages)

        send_messages.assert_called_with(messages)

    @patch('messaging.manager.CommandMessageManager.send_messages')
    def test_no_message_send_downstream(self, send_messages):
        """Validate send_message is not called when messages is empty"""

        manager = CommandMessageManager()
        manager._send_downstream([])

        self.assertFalse(send_messages.called)

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
