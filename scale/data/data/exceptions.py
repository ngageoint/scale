"""Defines exceptions that can occur when interacting with interface data values"""
from util.exceptions import ValidationException


class InvalidData(ValidationException):
    """Exception indicating that the data is invalid"""

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidData, self).__init__(name, description)
