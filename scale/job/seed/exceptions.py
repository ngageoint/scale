"""Defines exceptions that can occur when interacting with a Seed job interface"""
from __future__ import unicode_literals

from util.exceptions import ValidationException


class InvalidSeedManifestDefinition(ValidationException):
    """Exception indicating that the provided definition of a Seed Manifest was invalid
    """

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidSeedManifestDefinition, self).__init__(name, description)


class InvalidSeedMetadataDefinition(ValidationException):
    """Exception indicating that the provided definition of a Seed Metadata was invalid
    """
    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidSeedMetadataDefinition, self).__init__(name, description)
