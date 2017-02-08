"""Defines exceptions that can occur when conduction secrets transactions"""


class InvalidSecretsBackend(Exception):
    """Exception indicating that the provided secrets backend url was invalid
    """
    pass


class InvalidSecretsAuthorization(Exception):
    """Exception indicating that the provided credentials to a secrets request was invalid 
