"""Defines the classes for representing a connection between two interface parameters within a recipe definition"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

from data.interface.exceptions import InvalidInterfaceConnection


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

    @abstractmethod
    def add_value_to_data(self, data, recipe_input_data, node_outputs):
        """Adds the value for this connection to the data

        :param data: The data to add the value to
        :type data: :class:`data.data.data.Data`
        :param recipe_input_data: The input data for the recipe
        :type recipe_input_data: :class:`data.data.data.Data`
        :param node_outputs: The RecipeNodeOutput tuples stored in a dict by node name
        :type node_outputs: dict

        :raises :class:`data.data.exceptions.InvalidData`: If there is a duplicate data value
        """

        raise NotImplementedError()

    @abstractmethod
    def is_equal_to(self, connection):
        """Returns true if and only if the given input connection is equal to this one

        :param connection: The input connection
        :type connection: :class:`recipe.definition.connection.InputConnection`
        :returns: True if the connections are equal, False otherwise
        :rtype: bool
        """

        raise NotImplementedError()

    @abstractmethod
    def validate(self, all_dependencies):
        """Validates this connection

        :param all_dependencies: A set of all dependencies (node names) for the input node
        :type all_dependencies: set
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.interface.exceptions.InvalidInterfaceConnection`: If the interface connection is invalid
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
        """See :meth:`recipe.definition.connection.InputConnection.add_parameter_to_interface`
        """

        output_interface = node_output_interfaces[self.node_name]
        return interface.add_parameter_from_output_interface(self.input_name, self.output_name, output_interface)

    def add_value_to_data(self, data, recipe_input_data, node_outputs):
        """See :meth:`recipe.definition.connection.InputConnection.add_value_to_data`
        """

        output_data = node_outputs[self.node_name].output_data
        data.add_value_from_output_data(self.input_name, self.output_name, output_data)

    def is_equal_to(self, connection):
        """See :meth:`recipe.definition.connection.InputConnection.is_equal_to`
        """

        if not isinstance(connection, DependencyInputConnection):
            return False

        same_input_name = self.input_name == connection.input_name
        same_node_name = self.node_name == connection.node_name
        same_output_name = self.output_name == connection.output_name

        return same_input_name and same_node_name and same_output_name

    def validate(self, all_dependencies):
        """See :meth:`recipe.definition.connection.InputConnection.validate`
        """

        # Check that the connection's dependency is met
        if self.node_name not in all_dependencies:
            msg = 'Cannot get output \'%s\' without dependency on node \'%s\''
            raise InvalidInterfaceConnection('MISSING_DEPENDENCY', msg % (self.output_name, self.node_name))

        return []


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
        """See :meth:`recipe.definition.connection.InputConnection.add_parameter_to_interface`
        """

        return interface.add_parameter_from_output_interface(self.input_name, self.recipe_input_name,
                                                             recipe_input_interface)

    def add_value_to_data(self, data, recipe_input_data, node_outputs):
        """See :meth:`recipe.definition.connection.InputConnection.add_value_to_data`
        """

        data.add_value_from_output_data(self.input_name, self.recipe_input_name, recipe_input_data)

    def is_equal_to(self, connection):
        """See :meth:`recipe.definition.connection.InputConnection.is_equal_to`
        """

        if not isinstance(connection, RecipeInputConnection):
            return False

        same_input_name = self.input_name == connection.input_name
        same_recipe_input_name = self.recipe_input_name == connection.recipe_input_name
        return same_input_name and same_recipe_input_name

    def validate(self, all_dependencies):
        """See :meth:`recipe.definition.connection.InputConnection.validate`
        """

        return []
