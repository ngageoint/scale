"""Defines the command line method for running a Scan process"""
from __future__ import unicode_literals

import logging
import signal
import sys

# Attempt this for development, if it fails ignore
try:
    from mock import patch
except:
    pass
from distutils.util import strtobool
from optparse import make_option

from django.core.management.base import BaseCommand

from ingest.models import Scan
from storage.models import Workspace

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that executes the Workspace Scan processor
    """

    option_list = BaseCommand.option_list + (
        make_option('-i', '--scan-id', action='store', type='int', help=('ID of the Scan process to run')),
        # TODO: Using string instead of bool to accomodate job_data limitations.
        # This should be refactored when seed integration is done.
        make_option('-d', '--dry-run', action="store", type='string', default='False',
                    help=('Perform a dry-run of scan, skipping ingest')),
        make_option('-l', '--local', action="store_true", default=False,
                    help=('Perform a patch on workspace for local testing'))
    )

    help = 'Executes the Scan processor to make a single pass over a workspace for ingest'

    def __init__(self):
        """Constructor
        """

        super(Command, self).__init__()

        self._scanner = None

    def handle(self, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scan processor.
        """

        # Register a listener to handle clean shutdowns
        signal.signal(signal.SIGTERM, self._onsigterm)

        scan_id = options.get('scan_id')
        dry_run = bool(strtobool(options.get('dry_run')))
        local = options.get('local')

        if not scan_id:
            logger.error('-i or --scan-id parameter must be specified for Scan configuration.')
            sys.exit(1)

        logger.info('Command starting: scale_scan')
        logger.info('Scan ID: %i', scan_id)
        logger.info('Dry Run: %s', str(dry_run))
        logger.info('Local Test: %s', local)

        logger.info('Querying database for Scan configuration')
        scan = Scan.objects.select_related('job').get(pk=scan_id)
        self._scanner = scan.get_scan_configuration().get_scanner()
        self._scanner.scan_id = scan_id

        logger.info('Starting %s scanner', self._scanner.scanner_type)

        # Patch _get_volume_path for local testing outside of docker.
        # This is useful for testing when Scale isn't managing mounts.
        if options['local'] and patch:
            workspace = self._scanner._scanned_workspace
            if 'broker' in workspace.json_config and 'host_path' in workspace.json_config['broker']:
                with patch.object(Workspace, '_get_volume_path',
                                  return_value=workspace.json_config['broker']['host_path']) as mock_method:
                    self._scanner.run(dry_run=dry_run)
                    logger.info('Scanner has stopped running')
                    logger.info('Command completed: scale_scan')
                    return

        self._scanner.run(dry_run=dry_run)
        logger.info('Scanner has stopped running')

        logger.info('Command completed: scale_scan')

    def _onsigterm(self, signum, _frame):
        """See signal callback registration: :py:func:`signal.signal`.

        This callback performs a clean shutdown when a TERM signal is received.
        """

        logger.info('Scan command received sigterm, telling scanner to stop')

        if self._scanner:
            self._scanner.stop()
