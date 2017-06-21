from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import MagicMock
from mock import patch

from messaging.exceptions import CommandMessageExecuteFailure, InvalidCommandMessage
from messaging.manager import CommandMessageManager


################################################################################
# WARNING this file is specifically testing with singleton CommandMessageManager
################################################################################


class TestSingletonCommandMessageManager(TestCase):
    def setUp(self):
        django.setup()

    @patch('messaging.manager.get_message_backend')
    @patch('messaging.manager.BrokerDetails')
    def test_verify_singleton(self, broker_details, get_message_backend):
        """Validate that multiple instantiation attempts result in single instance"""

        self.assertEquals(CommandMessageManager(), CommandMessageManager())

    @patch('messaging.manager.get_message_backend')
    @patch('messaging.manager.BrokerDetails')
    @patch('messaging.manager.CommandMessageManager._process_message')
    def test_receive_message(self, process, broker_details, get_message_backend):
        """Exercise all exception code paths within recieve_message"""

        process.side_effect = [InvalidCommandMessage, CommandMessageExecuteFailure]
        manager = CommandMessageManager()
        manager._backend = MagicMock()
        manager._backend.receive_messages.return_value = [MagicMock(), MagicMock()]
        manager.receive_messages()
