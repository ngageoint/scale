"""Defines exceptions that can occur when interacting with a job interface"""


class InvalidInterfaceDefinition(Exception):
    """Exception indicating that the provided definition of a job interface was invalid
    """
    pass


class InvalidEnvironment(Exception):
    """Exception indicating that the provided definition of a job interface was invalid
    """
    pass


class InvalidSetting(Exception):
    """Exception indicating that the provided job settings were invalid
    """
    pass
