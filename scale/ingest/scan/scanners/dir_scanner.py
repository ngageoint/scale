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

        self._scan_dir = self._monitored_workspace.workspace_volume_path

    def _callback(self, file_list):
        """Callback for handling files identified by list_files callback
        
        :param file_list: List of files found within workspace
        :type file_list: string
        """
        
        for file_name in file_list:
            if not self._stop_received:
                self._ingest_file(file_name)
            else:
                raise ScannerInterruptRequested

    def run(self):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.run`
        """

        logger.info('Running S3 bucket scanner')

        # Initialize workspace scan via storage broker.
        self._scanned_workspace.list_objects(callback)

    def stop(self):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.stop`
        """

        self._stop_received = True

    def validate_configuration(self, configuration):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.validate_configuration`
        """

        warnings = []
        
        return warnings

    def _ingest_s3_object(self, object_key):
        """Applies rules and initiates ingest for a single S3 object

        :param object_key: S3 object key
        :type object_key: string
        """
        
        if self._dry_run:
            logger.info("Scan detected '%s' in bucket '%s'." % (object_key, self._bucket_name))
        else:
            ingest = self._create_ingest(object_name)
            self._process_ingest(ingest, object_key, None)
            logger.info("Scan ingested '%s' from bucket '%s'..." % (object_key, self._bucket_name))
