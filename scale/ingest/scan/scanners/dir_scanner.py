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
        self._scan_dir = None

    def load_configuration(self, configuration):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.load_configuration`
        """

        self._scan_dir = self._scanned_workspace.workspace_volume_path

    def _callback(self, file_list):
        """See :meth:`ingest.scan.scanners.scanner.Scanner._callback`
        """
        
        for file_name in file_list:
            if not self._stop_received:
                self._ingest_file(file_name)
            else:
                raise ScannerInterruptRequested

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

    def _ingest_file(self, file_name):
        """Applies rules and initiates ingest for a single file name

        :param file_name: full path to file name
        :type file_name: string
        """
        
        if self._dry_run:
            logger.info("Scan detected file in workspace '%s': %s" % (self._scanned_workspace.name, file_name))
        else:
            ingest = self._create_ingest(file_name)
            size = os.path.getsize(file_name)
            self._process_ingest(ingest, file_name, size)
            logger.info("Scan ingested file from workspace '%s': %s" % (self._scanned_workspace.name, file_name))
