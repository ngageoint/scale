"""Defines the classes for representing a connection between two interface parameters within a recipe definition"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod


class InputConnection(object):
    """Abstract base class that represents a connection between two interface parameters
    """

    __metaclass__ = ABCMeta

    def __init__(self, input_name):
        """Constructor

        :param input_name: The name of the node's input
        :type input_name: string
        """

        self.input_name = input_name

    @abstractmethod
    def add_parameter_to_interface(self, interface, recipe_input_interface, node_output_interfaces):
        """Adds the parameter for this connection to the interface

        :param interface: The interface to add the parameter to
        :type interface: :class:`data.interface.interface.Interface`
        :param recipe_input_interface: The interface for the recipe input
        :type recipe_input_interface: :class:`data.interface.interface.Interface`
        :param node_output_interfaces: The output interface for each node stored by node name
        :type node_output_interfaces: dict
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.interface.exceptions.InvalidInterfaceConnection`: If the interface connection is invalid
        """

        raise NotImplementedError()

    # TODO: raise exception for invalid data
    @abstractmethod
    def add_argument_to_data(self, data, recipe_input, node_output):
        """Adds the parameter for this connection to the interface

        :param data: The data to add the argument to
        :type data: :class:`data.data.data.Data`
        :param recipe_input: The recipe input data
        :type recipe_input: :class:`data.data.data.Data`
        :param node_output: The output data for each node stored by node name
        :type node_output: dict
        :returns: A list of warnings discovered during validation
        :rtype: list
        """

        raise NotImplementedError()


class DependencyInputConnection(InputConnection):
    """Represents a connection from one node's output to another node's input
    """

    def __init__(self, input_name, node_name, output_name):
        """Constructor

        :param input_name: The name of the node's input
        :type input_name: string
        :param node_name: The name of the dependency node providing its output
        :type node_name: string
        :param output_name: The name of the dependency node's output
        :type output_name: string
        """

        super(DependencyInputConnection, self).__init__(input_name)

        self.node_name = node_name
        self.output_name = output_name

    def add_parameter_to_interface(self, interface, recipe_input_interface, node_output_interfaces):
        """See :meth:`recipe.handlers.connection.InputConnection.add_parameter_to_interface`
        """

        output_interface = node_output_interfaces[self.node_name]
        return interface.add_parameter_from_output_interface(self.input_name, self.output_name, output_interface)


class RecipeInputConnection(InputConnection):
    """Represents a connection from the recipe's input to a node's input
    """

    def __init__(self, input_name, recipe_input_name):
        """Constructor

        :param input_name: The name of the node's input
        :type input_name: string
        :param recipe_input_name: The name of the recipe input
        :type recipe_input_name: string
        """

        super(RecipeInputConnection, self).__init__(input_name)

        self.recipe_input_name = recipe_input_name

    def add_parameter_to_interface(self, interface, recipe_input_interface, node_output_interfaces):
        """See :meth:`recipe.handlers.connection.InputConnection.add_parameter_to_interface`
        """

        return interface.add_parameter_from_output_interface(self.input_name, self.recipe_input_name,
                                                             recipe_input_interface)
