"""Defines exceptions that can occur when interacting with job configuration"""
from __future__ import unicode_literals

from util.exceptions import ValidationException


class InvalidJobConfiguration(ValidationException):
    """Exception indicating that the provided job configuration was invalid
    """

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidJobConfiguration, self).__init__(name, description)
