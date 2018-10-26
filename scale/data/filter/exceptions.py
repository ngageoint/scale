"""Defines exceptions that can occur when interacting with data filters"""
from util.exceptions import ValidationException


class InvalidDataFilter(ValidationException):
    """Exception indicating that the data filter is invalid"""

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidDataFilter, self).__init__(name, description)
