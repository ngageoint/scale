"""Defines exceptions that can occur when interacting with Strike configuration"""
from util.exceptions import ValidationException


class InvalidStrikeConfiguration(ValidationException):
    """Exception indicating that the provided strike configuration was invalid"""

    def __init__(self, description):
        """Constructor

        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidStrikeConfiguration, self).__init__('INVALID_STRIKE_CONFIGURATION', description)