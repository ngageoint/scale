"""Defines the class that represents a dataset"""
from __future__ import unicode_literals

from data.data.json.data_v6 import DataV6
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

        if not definition:
            definition = {}
        self._definition = definition
        self.param_names = set()
        self.parameters = {}
        if 'parameters' in self._definition:
            self.parameters = InterfaceV6(interface=definition['parameters']).get_interface()
            self.param_names = set(self.parameters.parameters.keys())

        self.global_parameters = {}
        if 'global_parameters' in self._definition:
            self.global_parameters = InterfaceV6(definition['global_parameters']).get_interface()
            keys = self.global_parameters.parameters.keys()
            dupes = self.param_names.intersection(keys)
            if dupes:
                raise InvalidDataSetDefinition('INVALID_DATASET_DEFINITION',
                    'Invalid dataset definition: Names must be unique. %s defined more than once' % dupes)
            self.param_names.update(keys)

        self.global_data = {}
        if 'global_data' in self._definition:
            self.global_data = DataV6(definition['global_data']).get_data()

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

    def get_parameters(self):
        """Retrieves the list of parameter keys from the dataset definition

        :returns: The list of parameter keys
        :rtype: [str]
        """
        names = self.parameters.keys()
        names.extend(self.global_parameters.keys())
        return names

    def validate_data(self, data):
        return data.validate(self.parameters)

    def validate(self, data=None):
        """Validates the dataset definition

        :returns: A list of warnings discovered during validation
        :rtype: :class:[`util.validation.ValidationWarning`]
        """
        # validate definition parameters
        warnings = self._validate_parameters()

        if self.global_data:
            warnings.append(self.global_data.validate(self.global_parameters))

        if data:
            warnings.append(self.validate_data(data))

        return warnings


    def _validate_parameters(self):
        """Validates the dataset parameters

        :return: A list of warnings discovered during parameter validation
        :rtype: :class:[`util.validation.ValidationWarning`]
        """

        warnings = []
        warnings.extend(self.parameters.validate())

        return warnings
