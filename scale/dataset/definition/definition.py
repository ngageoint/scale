"""Defines the class that represents a dataset"""
from __future__ import unicode_literals

from data.interface.interface import Interface
from data.interface.json.interface_v6 import InterfaceV6
from data.interface.parameter import Parameter
from dataset.exceptions import InvalidDataSetDefinition
from util.validation import ValidationWarning

class DataSetDefinition(object):
    """Represents the dataset definition
    """

    def __init__(self, definition):
        """Constructor

        :param definition: Parameters of the definition
        :type defintion: dict
        """

        # self.name = name
        if not definition:
            definition = {}
        self._definition = definition
        self.param_names = set()
        self.parameters = {}
        if 'parameters' in self._definition:
            self.parameters = InterfaceV6(definition['parameters']).get_interface()
            self.param_names = self.parameters.parameters.keys()
        self.global_parameters = {}
        if 'global_parameters' in self._definition:
            self.global_parameters = InterfaceV6(definition['global_parameters']).get_interface()
            keys = self.global_parameters.parameters.keys()
            dupes = self.param_names.intersection(keys)
            if dupes:
                raise InvalidDataSetDefinition('INVALID_DATASET_DEFINITION',
                    'Invalid dataset definition: Names must be unique. %s defined more than once' % dupes)
            self.param_names.update(keys)


    def get_dict(self):
        """Returns the internal dictionary that represents this datasets definition

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition

    def add_parameter(self, parameter):
        """Adds a new parameter to the dataset definition

        :keyword parameter: Parameter to add
        :type parameter:
        """
        if parameter.name in self.param_names:
            raise InvalidDataSetDefinition('INVALID_DATASET_DEFINITION',
                'Invalid dataset definition: %s cannot be defined more than once' % parameter.name)
        else:
            self.param_names.add(parameter.name)
            self.parameters[parameter.name] = parameter

    def add_global_parameter(self, parameter):
        """Adds a new global parameter to the dataset definition

        :keyword parameter: Parameter to add
        :type parameter:
        """
        if parameter.name in self.param_names:
            raise InvalidDataSetDefinition('INVALID_DATASET_DEFINITION',
                'Invalid dataset definition: %s cannot be defined more than once' % parameter.name)
        else:
            self.param_names.add(parameter.name)
            self.global_parameters[parameter.name] = parameter

    def get_parameter(self, parameter_name):
        """Retrieves the specified parameter from the dataset definition

        :returns: The specified parameter of the dataset definition
        :rtype: :class:`data.interface.parameter.Parameter`
        """
        if parameter_name in self.parameters:
            return self.parameters[parameter_name]
        if parameter_name in self.global_parameters:
            return self.global_parameters[parameter_name]
        return None

    def validate_data(self, data):
        return data.validate(self.parameters)

    def validate(self):
        """Validates the dataset definition

        :returns: A list of warnings discovered during validation
        :rtype: :class:[`util.validation.ValidationWarning`]
        """
        # validate definition parameters
        return self._validate_parameters()


    def _validate_parameters(self):
        """Validates the dataset parameters

        :return: A list of warnings discovered during parameter validation
        :rtype: :class:[`util.validation.ValidationWarning`]
        """

        warnings = []
        for parameter in self.parameters:
            warnings.extend(parameter.validate)

        return warnings

class DataSetMemberDefinition(object):
    """Represents a dataset member
    """

    def __init__(self, definition=None):
        """Constructor

        :param name: Name of the dataset member
        :type name: string
        :param interface_dict:
        """
        self._definition = definition

        if 'name' in definition:
            self.param_name = definition['name']

        if 'input' in definition:
            self.interface = InterfaceV6(interface=definition['input']).get_interface()

    def add_input(self, input_param):
        """Adds an input

        :param input_param: The input parameter
        :type input_param: :class:`data.interface.parameter.Parameter`
        """

        self.interface.add_parameter(input_param)

    def get_interface(self):
        """Returns the input interface for this member

        :returns: The input interface object for this member
        :rtype: :class:`data.interface.interface.Interface`
        """

        return self.interface

    def get_dict(self):
        """Returns the underlying dictionary of this member definition
        :returns: the dataset member definition
        :rtype: dict
        """
        return self._definition

    def validate(self):
        """Validates this dataset member definition

        :param member_definition:
        :param_type
        :returns: List of warnings found with the interface
        :rtype: [:class:`util.validation.ValidationWarning`]
        """

        return self.interface.validate()
