"""Defines the command that performs a Scale database update"""
from __future__ import unicode_literals

import logging
import signal
import sys

from django.core.management.base import BaseCommand

from scheduler.database.updater import DatabaseUpdater
from util.exceptions import TerminatedCommand


logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1
SIGTERM_EXIT_CODE = 2


class Command(BaseCommand):
    """Command that performs a Scale database update
    """

    help = 'Performs a Scale database update'

    def __init__(self):
        """Constructor
        """

        super(Command, self).__init__()

        self._updater = DatabaseUpdater()

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        """

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        logger.info('Starting Scale database update')
        try:
            self._updater.update()
        except TerminatedCommand:
            logger.warning('Scale database update stopped, exiting with code %d', SIGTERM_EXIT_CODE)
            sys.exit(SIGTERM_EXIT_CODE)
        except Exception as ex:
            logger.exception('Scale database update encountered error, exiting with code %d', GENERAL_FAIL_EXIT_CODE)
            sys.exit(GENERAL_FAIL_EXIT_CODE)

        logger.info('Completed Scale database update')

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Scale database update received sigterm, telling updater to stop')
        self._updater.stop()
