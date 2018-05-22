"""Defines the class for handling a data interface"""
from __future__ import unicode_literals

from data.interface.exceptions import InvalidInterface, InvalidInterfaceConnection


class Interface(object):
    """Represents a grouping of parameters
    """

    def __init__(self):
        """Constructor
        """

        self.parameters = {}  # {Name: Parameter}

    def add_parameter(self, parameter):
        """Adds the parameter to the interface

        :param parameter: The parameter to add
        :type parameter: :class:`data.interface.parameter.Parameter`

        :raises :class:`data.interface.exceptions.InvalidInterface`: If the parameter is a duplicate
        """

        if parameter.name in self.parameters:
            raise InvalidInterface('DUPLICATE_INPUT', 'Duplicate parameter \'%s\'' % parameter.name)

        self.parameters[parameter.name] = parameter

    def add_parameter_from_output_interface(self, input_name, output_name, output_interface):
        """Adds an output parameter from the given output interface to this interface with the given input name. This is
        used to create a connecting interface that can be validated for passing to another interface.

        :param input_name: The name of the input parameter to add
        :type input_name: string
        :param output_name: The name of the output parameter in the output interface
        :type output_name: string
        :param output_interface: The output interface
        :type output_interface: :class:`data.interface.interface.Interface`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.interface.exceptions.InvalidInterfaceConnection`: If the interface connection is invalid
        """

        if input_name in self.parameters:
            msg = 'Input \'%s\' has more than one parameter connected to it' % input_name
            raise InvalidInterfaceConnection('DUPLICATE_INPUT', msg)

        new_param = output_interface.parameters[output_name].copy()
        new_param.name = input_name
        self.add_parameter(new_param)

        return []

    def validate(self):
        """Validates this interface

        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.interface.exceptions.InvalidInterface`: If the interface is invalid
        """

        warnings = []

        for parameter in self.parameters.values():
            warnings.extend(parameter.validate())

        return warnings

    def validate_connection(self, connecting_interface):
        """Validates that the given connecting interface can be accepted by this interface

        :param connecting_interface: The interface attempting to connect to this interface
        :type connecting_interface: :class:`data.interface.interface.Interface`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.interface.exceptions.InvalidInterfaceConnection`: If the interface connection is invalid
        """

        warnings = []

        for parameter in self.parameters.values():
            if parameter.name in connecting_interface.parameters:
                connecting_parameter = connecting_interface.parameters[parameter.name]
                warnings.extend(parameter.validate_connection(connecting_parameter))
            elif parameter.required:
                raise InvalidInterfaceConnection('PARAM_REQUIRED', 'Parameter \'%s\' is required' % parameter.name)

        return warnings
