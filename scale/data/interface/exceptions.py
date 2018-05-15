"""Defines exceptions that can occur when interacting with data interfaces"""
from util.exceptions import ValidationException


class InvalidInterface(ValidationException):
    """Exception indicating that the interface is invalid"""

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidInterface, self).__init__(name, description)


class InvalidInterfaceConnection(ValidationException):
    """Exception indicating that the interface connection is invalid"""

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidInterfaceConnection, self).__init__(name, description)
