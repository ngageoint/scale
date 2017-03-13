"""Defines the exceptions related to Scan scanners"""

from ingest.scan.configuration.exceptions import InvalidScanConfiguration


class InvalidScannerConfiguration(InvalidScanConfiguration):
    """Exception indicating that a scanner configuration was invalid
    """

    pass


class ScanIngestJobAlreadyLaunched(APIException):
    """Exception indicating that a scanner has already spawned an ingest scan job
    """
    status_code = 409
    default_detail = 'Ingest Scan already launched'
    default_code = 'conflict'


class ScannerInterruptRequested(Exception):
    """Exception indicating that a scanner run was interrupted
    """

    pass
