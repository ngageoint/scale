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


class S3Scanner(Scanner):
    """A scanner for an S3 bucket backed workspace
    """

    def __init__(self):
        """Constructor
        """

        super(S3Scanner, self).__init__('s3', ['s3'])
        self._bucket_name = None
        self._credentials = None
        self._region_name = None


    def load_configuration(self, configuration):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.load_configuration`
        """

        self._bucket_name = configuration['bucket_name']
        self._region_name = configuration.get('region_name')
        # TODO Change credentials to use an encrypted store key reference
        self._credentials = AWSClient.instantiate_credentials_from_config(configuration)

    def _callback(self, object_list):
        """See :meth:`ingest.scan.scanners.scanner.Scanner._callback`
        """
        
        for key in object_list:
            if not self._stop_received:
                self._ingest_s3_object(key)
            else:
                raise ScannerInterruptRequested

    def validate_configuration(self, configuration):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.validate_configuration`
        """

        warnings = []
        if 'bucket_name' not in configuration:
            raise InvalidScannerConfiguration('bucket_name is required for s3 scanner')
        if not isinstance(configuration['bucket_name'], basestring):
            raise InvalidScannerConfiguration('bucket_name must be a string')
        if not configuration['bucket_name']:
            raise InvalidScannerConfiguration('bucket_name must be a non-empty string')

        # If credentials exist, validate them.
        credentials = AWSClient.instantiate_credentials_from_config(configuration)

        region_name = configuration.get('region_name')

        # Check whether the bucket can actually be accessed
        with S3Client(credentials, region_name) as client:
            try:
                client.get_bucket(configuration['bucket_name'])
            except ClientError:
                warnings.append(ValidationWarning('bucket_access',
                                                  'Unable to access S3 Bucket. Check the name, region and credentials.'))

        return warnings

    def _ingest_s3_object(self, object_key):
        """Applies rules and initiates ingest for a single S3 object

        :param object_key: S3 object key
        :type object_key: string
        """
        
        if self._dry_run:
            logger.info("Scan detected S3 object in workspace '%s': %s" % (self._scanned_workspace.name, object_key))
        else:
            ingest = self._create_ingest(object_name)
            self._process_ingest(ingest, object_key, None)
            logger.info("Scan ingested S3 object from workspace '%s':" % (self._scanned_workspace.name, object_key))
