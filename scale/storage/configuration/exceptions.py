"""Defines exceptions that can occur when interacting with Workspace configuration"""
from __future__ import unicode_literals

from util.exceptions import ValidationException


class InvalidWorkspaceConfiguration(ValidationException):
    """Exception indicating that the provided Workspace configuration was invalid"""

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidWorkspaceConfiguration, self).__init__(name, description)