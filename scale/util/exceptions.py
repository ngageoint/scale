"""Defines utility exceptions"""


class RollbackTransaction(Exception):
    """Exception that can be thrown and swallowed to explicitly rollback a transaction"""

    pass


class InvalidAWSCredentials(Exception):
    """Exception indicating missing credentials required to successfully authenticate to AWS"""

    pass


class QueueNotFound(Exception):
    """Exception indicating AWS SQS queue could not be found by name"""

    pass
