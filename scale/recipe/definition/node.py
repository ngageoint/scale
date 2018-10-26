"""Defines the classes for representing nodes within a recipe definition"""
from __future__ import unicode_literals

from abc import ABCMeta

from data.data.data import Data
from data.interface.exceptions import InvalidInterfaceConnection
from data.interface.interface import Interface
from recipe.definition.exceptions import InvalidDefinition


class NodeDefinition(object):
    """Represents a node within a recipe definition
    """

    __metaclass__ = ABCMeta

    def __init__(self, name, node_type):
        """Constructor

        :param name: The unique name of the node in the recipe graph
        :type name: string
        :param node_type: The type of the node
        :type node_type: string
        """

        self.name = name
        self.node_type = node_type
        self.parents = {}  # {Name: Node}
        self.connections = {}  # {Input name: InputConnection}
        self.children = {}  # {Name: Node}
        self.allows_child_creation = True  # Indicates whether children of this node can be created immediately

    def add_connection(self, connection):
        """Adds a connection that connects a parameter to one of this node's inputs

        :param connection: The connection to add
        :type connection: :class:`recipe.definition.connection.InputConnection`

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the definition is invalid
        """

        try:
            if connection.input_name in self.connections:
                msg = 'Input \'%s\' has more than one parameter connected to it' % connection.input_name
                raise InvalidInterfaceConnection('DUPLICATE_INPUT', msg)

            self.connections[connection.input_name] = connection
        except InvalidInterfaceConnection as ex:
            msg = 'Node \'%s\' interface error: %s' % (self.name, ex.error.description)
            raise InvalidDefinition('NODE_INTERFACE', msg)

    def add_dependency(self, node):
        """Adds a dependency that this node has on the given node

        :param node: The dependency node to add
        :type node: :class:`recipe.definition.node.NodeDefinition`
        """

        self.parents[node.name] = node
        node.children[self.name] = self

    def generate_input_data(self, recipe_input_data, node_outputs):
        """Generates the input data for this node

        :param recipe_input_data: The input data for the recipe
        :type recipe_input_data: :class:`data.data.data.Data`
        :param node_outputs: The RecipeNodeOutput tuples stored in a dict by node name
        :type node_outputs: dict
        :returns: The input data for this node
        :rtype: :class:`data.data.data.Data`

        :raises :class:`data.data.exceptions.InvalidData`: If there is a duplicate data value
        """

        input_data = Data()

        for connection in self.connections.values():
            connection.add_value_to_data(input_data, recipe_input_data, node_outputs)

        return input_data

    def validate(self, recipe_input_interface, node_input_interfaces, node_output_interfaces):
        """Validates this node

        :param recipe_input_interface: The interface for the recipe input
        :type recipe_input_interface: :class:`data.interface.interface.Interface`
        :param node_input_interfaces: The input interface for each node stored by node name
        :type node_input_interfaces: dict
        :param node_output_interfaces: The output interface for each node stored by node name
        :type node_output_interfaces: dict
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the definition is invalid
        """

        warnings = []
        input_interface = node_input_interfaces[self.name]
        connecting_interface = Interface()

        # Generate complete dependency set for this node
        all_dependencies = set()
        dependency_list = list(self.parents.values())
        while dependency_list:
            dependency = dependency_list.pop()
            if dependency.name not in all_dependencies:
                all_dependencies.add(dependency.name)
                dependency_list.extend(list(dependency.parents.values()))

        try:
            for connection in self.connections.values():
                # Validate each connection
                warnings.extend(connection.validate(all_dependencies))
                # Combine all connections into a connecting interface
                warnings.extend(connection.add_parameter_to_interface(connecting_interface, recipe_input_interface,
                                                                      node_output_interfaces))
            # Validate that connecting interface can be passed to this interface
            warnings.extend(input_interface.validate_connection(connecting_interface))
        except InvalidInterfaceConnection as ex:
            msg = 'Node \'%s\' interface error: %s' % (self.name, ex.error.description)
            raise InvalidDefinition('NODE_INTERFACE', msg)

        return warnings


class ConditionNodeDefinition(NodeDefinition):
    """Represents a condition within a recipe definition
    """

    NODE_TYPE = 'condition'

    def __init__(self, name, input_interface, data_filter):
        """Constructor

        :param name: The unique name of the node in the recipe graph
        :type name: string
        :param input_interface: The input interface of the condition
        :type input_interface: :class:`data.interface.interface.Interface`
        :param data_filter: The data filter of the condition
        :type data_filter: :class:`data.filter.filter.DataFilter`
        """

        super(ConditionNodeDefinition, self).__init__(name, ConditionNodeDefinition.NODE_TYPE)

        self.input_interface = input_interface
        self.data_filter = data_filter

        # TODO: generate output interface from input interface + data filter
        # TODO: input params with required=False that are checked for existence in data filter should become
        # required=True on output
        self.output_interface = input_interface


class JobNodeDefinition(NodeDefinition):
    """Represents a job within a recipe definition
    """

    NODE_TYPE = 'job'

    def __init__(self, name, job_type_name, job_type_version, revision_num):
        """Constructor

        :param name: The unique name of the node in the recipe graph
        :type name: string
        :param job_type_name: The name of the job type
        :type job_type_name: string
        :param job_type_version: The version of the job type
        :type job_type_version: string
        :param revision_num: The revision number of the job type
        :type revision_num: int
        """

        super(JobNodeDefinition, self).__init__(name, JobNodeDefinition.NODE_TYPE)

        self.job_type_name = job_type_name
        self.job_type_version = job_type_version
        self.revision_num = revision_num


class RecipeNodeDefinition(NodeDefinition):
    """Represents a recipe within a recipe definition
    """

    NODE_TYPE = 'recipe'

    def __init__(self, name, recipe_type_name, revision_num):
        """Constructor

        :param name: The unique name of the node in the recipe graph
        :type name: string
        :param recipe_type_name: The name of the recipe type
        :type recipe_type_name: string
        :param revision_num: The revision number of the recipe type
        :type revision_num: int
        """

        super(RecipeNodeDefinition, self).__init__(name, RecipeNodeDefinition.NODE_TYPE)

        self.recipe_type_name = recipe_type_name
        self.revision_num = revision_num
