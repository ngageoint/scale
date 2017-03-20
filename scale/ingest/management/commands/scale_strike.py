"""Defines the command line method for running a Strike process"""
from __future__ import unicode_literals

import logging
import signal
import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from ingest.models import Strike

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that executes the Strike processor
    """

    help = 'Executes the Strike processor to monitor and process incoming files for ingest'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--strike-id', action='store', type=int,
                            help=('ID of the Strike process to run'))

    def __init__(self):
        """Constructor
        """

        super(Command, self).__init__()

        self._strike_id = None
        self._monitor = None

    def handle(self, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Strike processor.
        """

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        self._strike_id = options.get('strike_id')

        logger.info('Command starting: scale_strike')
        logger.info('Strike ID: %i', self._strike_id)

        logger.info('Querying database for Strike configuration')
        strike = Strike.objects.select_related('job').get(pk=self._strike_id)
        self._monitor = strike.get_strike_configuration().get_monitor()
        self._monitor.strike_id = self._strike_id

        logger.info('Starting %s monitor', self._monitor.monitor_type)
        self._monitor.run()
        logger.info('Monitor has stopped running')

        logger.info('Command completed: scale_strike')
        sys.exit(1)

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Strike command received sigterm, telling monitor to stop')

        if self._monitor:
            self._monitor.stop()
