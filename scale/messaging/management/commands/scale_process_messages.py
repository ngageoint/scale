"""Defines the command for retrieval and execution of CommandMessages"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import signal

from django.core.management.base import BaseCommand

from messaging.manager import CommandMessageManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command for retrieval and execution of CommandMessages from queue
    """

    help = 'Command for retrieval and execution of CommandMessages from queue'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        """
        logger.info('Command starting: scale_process_messages')

        self.running = True

        # Set the signal handler
        signal.signal(signal.SIGINT, self.interupt)
        signal.signal(signal.SIGTERM, self.interupt)

        manager = CommandMessageManager()

        while self.running:
            manager.receive_messages()

        logger.info('Command completed: scale_process_messages')

    def interupt(self, signum, frame):
        logger.info('Halting queue processing as a result of signal: {}'.format(signum))
        self.running = False
