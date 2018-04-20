"""Defines exceptions that can occur when interacting with batch configurations"""
from util.exceptions import ValidationException


class InvalidConfiguration(ValidationException):
    """Exception indicating that the provided batch configuration was invalid"""

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidConfiguration, self).__init__(name, description)
