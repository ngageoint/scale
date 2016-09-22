"""Defines exceptions that can occur when interacting with a job results"""


class InvalidResultsManifest(Exception):
    """Exception indicating that a result manifest was invalid
    """
    pass


class MissingRequiredOutput(Exception):
    """Exception indicating that a required output was not produced
    """
