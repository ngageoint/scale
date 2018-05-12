"""Defines the class for handling a data interface"""
from __future__ import unicode_literals

from data.interface.exceptions import InvalidInterfaceConnection


class Interface(object):
    """Represents a grouping of parameters
    """

    def __init__(self):
        """Constructor
        """

        self.parameters = {}  # {Name: Parameter}

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
        self.parameters[input_name] = new_param
        return []

    def validate_connection(self, connecting_interface):
        """Validates that the given connecting interface can be accepted by this interface

        :param connecting_interface: The interface attempting to connect to this interface
        :type connecting_interface: :class:`data.interface.interface.Interface`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.interface.exceptions.InvalidInterfaceConnection`: If the interface connection is invalid
        """

        # TODO: implement
        # TODO: make sure all parameters match type and multiplicity
        # TODO: make sure all required parameters are provided
        # TODO: provide warnings for mismatched media types
        return []

    # TODO: a general validate method for just this interface

    # TODO: a method to validate data being passed to this one (ensure valid data)
    # - return warnings for "extra" values provided
