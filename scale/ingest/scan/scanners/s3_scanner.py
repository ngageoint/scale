"""Defines a scanner that scans an S3 bucket backed workspace for files"""
from __future__ import unicode_literals

import logging

from ingest.scan.scanners.scanner import Scanner

logger = logging.getLogger(__name__)


class S3Scanner(Scanner):
    """A scanner for an S3 bucket backed workspace
    """

    def __init__(self):
        """Constructor
        """

        super(S3Scanner, self).__init__('s3', ['s3'])

    def load_configuration(self, configuration):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.load_configuration`
        """

        # Nothing to do as all configuration is done at workspace broker level.
        pass

    def validate_configuration(self, configuration):
        """See :meth:`ingest.scan.scanners.scanner.Scanner.validate_configuration`
        """

        # No configuration is required for S3 scanner as everything is provided
        # by way of the workspace configurations.

        return []

    def _ingest_file(self, file_name, file_size):
        """Applies rules and update ingest for a single S3 object

        :param file_name: S3 object key
        :type file_name: string
        :param file_size: object size in bytes
        :type file_size: int
        :returns: Ingest model prepped for bulk create
        :rtype: :class:`ingest.models.Ingest`
        """

        ingest = None

        if self._dry_run:
            logger.info("Scan detected S3 object in workspace '%s': %s" % (self._scanned_workspace.name, file_name))
        else:
            ingest = self._process_ingest(file_name, file_size)
            logger.info("Scan processed S3 object from workspace '%s': %s" % (self._scanned_workspace.name, file_name))

        return ingest
