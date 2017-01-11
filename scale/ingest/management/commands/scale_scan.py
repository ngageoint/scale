"""Defines the command line method for running a Scan process"""
from __future__ import unicode_literals

import logging
import signal
import sys
from optparse import make_option

from django.core.management.base import BaseCommand

from ingest.models import Scan


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that executes the Workspace Scan processor
    """

    option_list = BaseCommand.option_list + (
        make_option('-i', '--scan-id', action='store', type='int', help=('ID of the Scan process to run')),
    )

    help = 'Executes the Scan processor to make a single pass over a workspace for ingest'

    def __init__(self):
        """Constructor
        """

        super(Command, self).__init__()

        self._scan_id = None
        self._scanner = None

    def handle(self, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scan processor.
        """

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        self._scan_id = options.get('scan_id')

        logger.info('Command starting: scale_scan')
        logger.info('Scan ID: %i', self._scan_id)

        logger.info('Querying database for Strike configuration')
        scan = Scan.objects.select_related('job').get(pk=self._scan_id)
        self._scanner = strike.get_scan_configuration().get_scanner()
        self._scanner.scan_id = self._scan_id

        logger.info('Starting %s monitor', self._monitor.monitor_type)
        self._monitor.run()
        logger.info('Monitor has stopped running')

        logger.info('Command completed: scale_scan')
        sys.exit(1)

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Strike command received sigterm, telling monitor to stop')

        if self._monitor:
            self._monitor.stop()
