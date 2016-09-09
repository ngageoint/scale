"""Defines utility exceptions"""


class FileDoesNotExist(Exception):
    """Exception indicating an attempt was made to access a file that no longer exists
    """

    pass


class InvalidAWSCredentials(Exception):
    """Exception indicating missing credentials required to successfully authenticate to AWS"""

    pass


class RollbackTransaction(Exception):
    """Exception that can be thrown and swallowed to explicitly rollback a transaction"""

    pass