"""Defines a scanner that scans an S3 bucket backed workspace for files"""
from __future__ import unicode_literals

import json
import logging
import os

from botocore.exceptions import ClientError

from ingest.scan.configuration.scan_configuration import ValidationWarning
from ingest.scan.scanners.exceptions import (InvalidScannerConfiguration, ScannerInterruptRequested)
from ingest.scan.scanners.scanner import Scanner
from util.aws import AWSClient, S3Client

logger = logging.getLogger(__name__)


class DirScanner(Scanner):
    """A scanner for an S3 bucket backed workspace
    """

    def __init__(self):
        """Constructor
        """

        super(DirScanner, self).__init__('dir', ['host'])
        self._transfer_suffix = None

    def load_configuration(self, configuration):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.load_configuration`
        """

        self._transfer_suffix = configuration['transfer_suffix']

    def validate_configuration(self, configuration):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.validate_configuration`
        """

        if 'transfer_suffix' not in configuration:
            raise InvalidScannerConfiguration('transfer_suffix is required for dir scanner')
        if not isinstance(configuration['transfer_suffix'], basestring):
            raise InvalidScannerConfiguration('transfer_suffix must be a string')
        if not configuration['transfer_suffix']:
            raise InvalidScannerConfiguration('transfer_suffix must be a non-empty string')
        
        return []

    def _ingest_file(self, file_name, file_size):
        """Applies rules and initiates ingest for a single file name

        :param file_name: full path to file name
        :type file_name: string
        :param file_size: file size in bytes
        :type file_size: int
        :returns: Ingest model prepped for bulk create
        :rtype: :class:`ingest.models.Ingest`
        """

        ingest = None

        if self._dry_run:
            logger.info("Scan detected file in workspace '%s': %s" % (self._scanned_workspace.name, file_name))
        else:
            if file_name.endswith(self._transfer_suffix):
                logger.info("Skipping file '%s' that is in transfer state." % file_name)
                return
            ingest = self._process_ingest(file_name, file_size)
            logger.info("Scan processed file from workspace '%s': %s" % (self._scanned_workspace.name, file_name))

        return ingest
