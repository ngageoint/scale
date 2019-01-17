"""Defines the class that represents a dataset"""
from __future__ import unicode_literals

from dataset.exceptions import InvalidDataSetDefinition


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
        self.param_names = set()

        # for param in self._definition['parameters']:
        #     if param in self.param_names:
        #         raise InvalidDataSetDefinition('INVALID_DATASET_DEFINITION',
        #             'Invalid dataset definition: %s cannot be defined more than once' % param)
        #     else:
        #         self.param_names.add(param)

        if do_validate:
            self.validate()

    def get_dict(self):
        """Returns the internal dictionary that represents this datasets definition

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition

    def add_parameter(self, parameter, parameter_def):
        """Adds a new parameter to the dataset definition

        :keyword parameter: Parameter to add
        :type parameter:
        :keyword parameter_def: Definition of the parameter
        :type parameter_def:
        """

    def get_parameter(self, parameter_name):
        """Retrieves the specified parameter from the dataset definition

        :returns: The specified parametr of the dataset definition
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

class DataSetMemberDefinition(object):
    """Represents a dataset member
    """

    def __init__(self, definition, do_validate=True):
        """Constructor

        :param definition: dict definition
        :type definition: dict
        """
        if 'name' in definition:
            self.name = definition['name']
        self._definition = definition

        if do_validate:
            self.validate()

    def get_dict(self):
        """Returns the dictionary of the definition

        :return: The member definition
        :rtype: dict
        """
        return self._definition

    def validate(self):
        """Validates the dataset member definition

        :returns: List of warnings found
        :rtype: [:class:`dataset.definition.definition.ValidationWarning`]
        """
        warnings = []
        return warnings
