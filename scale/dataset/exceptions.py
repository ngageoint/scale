"""Defines exceptions that can occur when interacting with datasets, datasetmembers, and datasetfiles"""
from __future__ import unicode_literals
from util.exceptions import ValidationException

class InvalidDataSet(ValidationException):
    """Exception indicating the dataset is invalid
    """

    def __init__(self, name, description):
        """Constructor

        :param description: The description of the error
        :type description: string
        """

        super(InvalidDataSet, self).__init__(name, description)

class InvalidDataSetMember(ValidationException):
    """Exception indicating the dataset is invalid
    """

    def __init__(self, name, description):
        """Constructor

        :param description: The description of the error
        :type description: string
        """

        super(InvalidDataSetMember, self).__init__(name, description)

class InvalidDataSetDefinition(ValidationException):
    """Exception indicating that a dataset definition was given an invalid value
    """

    def __init__(self, name, description):
        """Constructor

        :param name: The name of the validation error
        :type name: string
        :param description: The description of the validation error
        :type description: string
        """

        super(InvalidDataSetDefinition, self).__init__(name, description)