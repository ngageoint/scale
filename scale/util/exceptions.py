"""Defines utility exceptions"""


class FileDoesNotExist(Exception):
    """Exception indicating an attempt was made to access a file that no longer exists
    """

    pass


class InvalidBrokerUrl(Exception):
    """Exception indicating the broker URL does not meet the format requirements"""

    pass


class InvalidAWSCredentials(Exception):
    """Exception indicating missing credentials required to successfully authenticate to AWS"""

    pass


class RollbackTransaction(Exception):
    """Exception that can be thrown and swallowed to explicitly rollback a transaction"""

    pass


class ScaleLogicBug(Exception):
    """Exception that indicates a critical Scale logic bug has occurred"""

    pass


class TerminatedCommand(Exception):
    """Exception that can be thrown to indicate that a Scale command recieved a SIGTERM signal"""

    pass
