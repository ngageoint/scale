"""Defines the exceptions related to Strike monitors"""

from util.exceptions import ValidationException


class InvalidMonitorConfiguration(ValidationException):
    """Exception indicating that the provided strike configuration was invalid"""

    def __init__(self, description):
        """Constructor

        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidMonitorConfiguration, self).__init__('INVALID_MONITOR_CONFIGURATION', description)


class SQSNotificationError(Exception):
    """Error class used when there is a problem processing an SQS S3 notification"""

    pass


class S3NoDataNotificationError(Exception):
    """Error class used when there is no data associated with an S3 notification"""

    pass
