"""Defines the exceptions related to workspace brokers"""

from storage.configuration.exceptions import InvalidWorkspaceConfiguration


class InvalidBrokerConfiguration(InvalidWorkspaceConfiguration):
    """Exception indicating that a broker configuration was invalid
    """

    pass
