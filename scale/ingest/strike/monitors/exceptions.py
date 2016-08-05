"""Defines the exceptions related to Strike monitors"""

from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration


class InvalidMonitorConfiguration(InvalidStrikeConfiguration):
    """Exception indicating that a monitor configuration was invalid
    """

    pass


class SQSNotificationError(Exception):
    """Error class used when there is a problem processing an SQS S3 notification"""

    pass


class S3NoDataNotificationError(Exception):
    """Error class used when there is no data associated with an S3 notification"""

    pass
