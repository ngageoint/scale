class SQSNotificationError(Exception):
    """Error class used when there is a problem processing an SQS S3 notification."""
    pass


class S3NoDataNotificationError(Exception):
    """Error class used when there is no data associated with an S3 notification."""
    pass
