"""Defines the class that represents a dataset"""
from __future__ import unicode_literals


class ValidationWarning(object):
    """Tracks dataset definition warnings during validation that may not prevent the dataset from working."""

    def __init__(self, key, details):
        """Constructor sets basic attributes.

        :param key: A unique identifier clients can use to recognize the warning.
        :type key: string
        :param details: A user-friendly description of the problem, including field names and/or associated values.
        :type details: string
        """
        self.key = key
        self.details = details

class DataSetDefinition(object):
    """Represents the dataset definition
    """

    def __init__(self, definition, do_validate=True):
        """Constructor

        :param definition: dict definition
        :type definition: dict
        """
        if 'name' in definition:
            self.name = definition['name']
        self._definition = definition

    def get_dict(self):
        """Returns the internal dictionary that represents this datasets definition

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition

    #TODO
    def add_parameter(self, parameter):
        """Adds a global parameter to the dataset definition

        :keyword parameter: Parameter to add
        :type parameter:
        """

    def get_parameter(self, parameter_name):
        """Retrieves the specified parameter from the dataset definition

        :returns: The specified parametr of the datase definition
        :rtype:
        """

    def validate(self):
        """Validates the dataset definition

        :returns: A list of warnings discovered during validation
        :rtype: :class:[`dataset.definition.definition.ValidationWarning`]
        """

        # validate definition parameter
        warnings = self._validate_parameters()

        return warnings

    def _validate_parameters(self):
        """Validates the dataset parameters

        :return: A list of warnings discovered during parameter validation
        :rtype: :class:[`dataset.definition.definition.ValidationWarning`]
        """

        warnings = []

        return warnings
