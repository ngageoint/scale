"""Defines the command for performing testing with EchoCommandMessage"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
from datetime import datetime

from django.core.management.base import BaseCommand

from messaging.manager import CommandMessageManager
from messaging.messages.echo import EchoCommandMessage
from messaging.messages.factory import get_message_type

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command for performing testing with EchoCommandMessage
    """

    help = 'Command for performing testing with send messages'

    def add_arguments(self, parser):
        parser.add_argument('-b', '--body', action='store',
                            help='Message payload to send.')
        parser.add_argument('-c', '--count', action='store', type=int,
                            help='Message repetitions to send.')
        parser.add_argument('-t', '--type', action='store',
                            help='Message type to send.')

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        """

        body = options.get('body')
        type = options.get('type')
        count = options.get('count')
        if not count:
            count = 1

        logger.info('Command starting: scale_send_message')

        Message = get_message_type(type)

        manager = CommandMessageManager()
        messages = [Message.from_json(body) for _ in range(count)]
        manager.send_messages(messages)

        logger.info('Command completed: scale_send_message')
