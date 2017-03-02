"""Defines the exceptions related to Scan scanners"""

from ingest.scan.configuration.exceptions import InvalidScanConfiguration


class InvalidScannerConfiguration(InvalidScanConfiguration):
    """Exception indicating that a scanner configuration was invalid
    """

    pass


class ScannerInterruptRequested(Exception):
    """Exception indicating that a scanner run was interrupted
    """

    pass
