"""Defines the class for representing a recipe definition"""
from __future__ import unicode_literals

from data.interface.exceptions import InvalidInterface
from recipe.definition.connection import DependencyInputConnection, RecipeInputConnection
from recipe.definition.exceptions import InvalidDefinition
from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition


class RecipeDefinition(object):
    """Represents a recipe definition, which consists of an input interface and a directed acyclic graph of recipe nodes
    """

    def __init__(self, input_interface):
        """Constructor

        :param input_interface: The input interface for the recipe
        :type input_interface: :class:`data.interface.interface.Interface`
        """

        self.input_interface = input_interface
        self.graph = {}  # {Name: Node}
        self._topological_order = None  # Cached topological ordering of the nodes (list of names)

    def add_dependency(self, parent_name, child_name):
        """Adds a dependency that one node has upon another node

        :param parent_name: The name of the parent node
        :type parent_name: string
        :param child_name: The name of the child node
        :type child_name: string

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If either node is unknown
        """

        if child_name not in self.graph:
            raise InvalidDefinition('UNKNOWN_NODE', 'Node \'%s\' is not defined' % child_name)
        if parent_name not in self.graph:
            raise InvalidDefinition('UNKNOWN_NODE', 'Node \'%s\' is not defined' % parent_name)

        child_node = self.graph[child_name]
        parent_node = self.graph[parent_name]
        child_node.add_dependency(parent_node)

        self._topological_order = None  # Invalidate cache

    def add_dependency_input_connection(self, node_name, node_input_name, dependency_name, dependency_output_name):
        """Adds a connection from a dependency output to the input of a node

        :param node_name: The name of the node whose input is being connected to
        :type node_name: string
        :param node_input_name: The name of the node's input
        :type node_input_name: string
        :param dependency_name: The name of the dependency node whose output is being connected to the input
        :type dependency_name: string
        :param dependency_output_name: The name of the dependency node's output
        :type dependency_output_name: string

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If either node is unknown, the dependency node
            is the wrong type, or the connection is a duplicate
        """

        if dependency_name not in self.graph:
            raise InvalidDefinition('UNKNOWN_NODE', 'Node \'%s\' is not defined' % dependency_name)

        if self.graph[dependency_name].node_type != JobNodeDefinition.NODE_TYPE:
            msg = 'Node \'%s\' has a connection to a node that is not a job' % node_name
            raise InvalidDefinition('CONNECTION_INVALID_NODE', msg)

        connection = DependencyInputConnection(node_input_name, dependency_name, dependency_output_name)
        self._add_connection(node_name, connection)

    def add_job_node(self, name, job_type_name, job_type_version, revision_num):
        """Adds a job node to the recipe graph

        :param name: The node name
        :type name: string
        :param job_type_name: The name of the job type
        :type job_type_name: string
        :param job_type_version: The version of the job type
        :type job_type_version: string
        :param revision_num: The revision number of the job type
        :type revision_num: int

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the node is duplicated
        """

        self._add_node(JobNodeDefinition(name, job_type_name, job_type_version, revision_num))

    def update_job_nodes(self, job_type_name, job_type_version, revision_num):
        """Updates the revision of job nodes with the given name and version

        :param job_type_name: The name of the job type
        :type job_type_name: string
        :param job_type_version: The version of the job type
        :type job_type_version: string
        :param revision_num: The new revision number of the job type
        :type revision_num: int
        :returns: True if a node was updated, otherwise false
        :rtype: bool
        """

        found = False
        for node_name in self.get_topological_order():
            node = self.graph[node_name]
            if isinstance(node, JobNodeDefinition):
                if node.job_type_name == job_type_name and node.job_type_version == job_type_version:
                    if node.revision_num >= revision_num:
                        continue
                    else:
                        node.revision_num = revision_num
                        found = True
                        
        return found

    def add_recipe_input_connection(self, node_name, node_input_name, recipe_input_name):
        """Adds a connection from a recipe input to the input of a node

        :param node_name: The name of the node whose input is being connected to
        :type node_name: string
        :param node_input_name: The name of the node's input
        :type node_input_name: string
        :param recipe_input_name: The name of the recipe input being connected to the node's input
        :type recipe_input_name: string

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the node or recipe input is unknown or the
            connection is a duplicate
        """

        if recipe_input_name not in self.input_interface.parameters:
            raise InvalidDefinition('UNKNOWN_INPUT', 'Recipe input \'%s\' is not defined' % recipe_input_name)

        connection = RecipeInputConnection(node_input_name, recipe_input_name)
        self._add_connection(node_name, connection)

    def add_recipe_node(self, name, recipe_type_name, revision_num):
        """Adds a recipe node to the recipe graph

        :param name: The node name
        :type name: string
        :param recipe_type_name: The name of the recipe type
        :type recipe_type_name: string
        :param revision_num: The revision number of the recipe type
        :type revision_num: int

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the node is duplicated
        """

        self._add_node(RecipeNodeDefinition(name, recipe_type_name, revision_num))

    def update_recipe_nodes(self, recipe_type_name, revision_num):
        """Updates the revision of recipe nodes with the given name to the specified revision_num

        :param recipe_type_name: The name of the recipe type
        :type recipe_type_name: string
        :param revision_num: The new revision number of the recipe type
        :type revision_num: int
        :returns: True if a node was updated, otherwise false
        :rtype: bool
        """

        found = False
        for node_name in self.get_topological_order():
            node = self.graph[node_name]
            if isinstance(node, RecipeNodeDefinition):
                if node.recipe_type_name == recipe_type_name:
                    if node.revision_num >= revision_num:
                        continue
                    else:
                        node.revision_num = revision_num
                        found = True
                        
        return found

    def generate_node_input_data(self, node_name, recipe_input_data, node_outputs):
        """Generates the input data for the node with the given name

        :param node_name: The name of the node
        :type node_name: string
        :param recipe_input_data: The input data for the recipe
        :type recipe_input_data: :class:`data.data.data.Data`
        :param node_outputs: The RecipeNodeOutput tuples stored in a dict by node name
        :type node_outputs: dict
        :returns: The input data for the node
        :rtype: :class:`data.data.data.Data`

        :raises :class:`data.data.exceptions.InvalidData`: If there is a duplicate data value
        """

        return self.graph[node_name].generate_input_data(recipe_input_data, node_outputs)

    def get_topological_order(self):
        """Returns the recipe node names in a valid topological ordering (dependency order)

        :returns: The list of nodes names in a topological ordering
        :rtype: list

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the definition contains a circular
            dependency
        """

        if self._topological_order is None:
            self._calculate_topological_order()

        return self._topological_order

    def get_interfaces(self):
        """Gets the input and output interfaces for each node in this recipe

        :returns: A dict of input interfaces and a dict of output interfaces
        :rtype: dict, dict
        """

        inputs = {}
        outputs = {}
        
        for node_name in self.get_topological_order():
            node = self.graph[node_name]
            inputs[node_name] = node.get_input_interface()
            outputs[node_name] = node.get_output_interface()

        return inputs, outputs

    def validate(self, node_input_interfaces, node_output_interfaces):
        """Validates this recipe definition

        :param node_input_interfaces: The input interface for each node stored by node name
        :type node_input_interfaces: dict
        :param node_output_interfaces: The output interface for each node stored by node name
        :type node_output_interfaces: dict
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the definition is invalid
        """

        try:
            warnings = self.input_interface.validate()
        except InvalidInterface as ex:
            raise InvalidDefinition('INPUT_INTERFACE', ex.error.description)

        # Processing nodes in topological order will also detect any circular dependencies
        for node_name in self.get_topological_order():
            node = self.graph[node_name]
            warnings.extend(node.validate(self.input_interface, node_input_interfaces, node_output_interfaces))

        return warnings

    def _add_connection(self, node_name, connection):
        """Adds a connection to the input of the node

        :param node_name: The name of the node whose input is being connected to
        :type node_name: string
        :param connection: The connection to the node input
        :type connection: :class:`recipe.definition.connection.InputConnection`

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the node is unknown or the connection is a
            duplicate
        """

        if node_name not in self.graph:
            raise InvalidDefinition('UNKNOWN_NODE', 'Node \'%s\' is not defined' % node_name)

        node = self.graph[node_name]
        node.add_connection(connection)

    def _add_node(self, node):
        """Adds a node to the recipe graph

        :param node: The node
        :type node: :class:`recipe.definition.node.NodeDefinition`

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the node is duplicated
        """

        if node.name in self.graph:
            raise InvalidDefinition('DUPLICATE_NODE', 'Node \'%s\' is already defined' % node.name)

        self.graph[node.name] = node
        self._topological_order = None  # Invalidate cache

    def _calculate_topological_order(self):
        """Calculates a valid topological ordering (dependency order) for the recipe

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the definition contains a circular
            dependency
        """

        results = []
        perm_set = set()
        temp_set = set()
        unmarked_set = set(self.graph.keys())
        while unmarked_set:
            node_name = unmarked_set.pop()
            node = self.graph[node_name]
            self._topological_order_visit(node, results, perm_set, temp_set)
            unmarked_set = set(self.graph.keys()) - perm_set

        self._topological_order = results

    def _topological_order_visit(self, node, results, perm_set, temp_set):
        """Recursive depth-first search algorithm for determining a topological ordering of the recipe nodes

        :param node: The current node
        :type node: :class:`recipe.definition.node.NodeDefinition`
        :param results: The list of node names in topological order
        :type results: list
        :param perm_set: A permanent set of visited nodes (node names)
        :type perm_set: set
        :param temp_set: A temporary set of visited nodes (node names)
        :type temp_set: set

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the definition contains a circular
            dependency
        """

        if node.name in temp_set:
            msg = 'Recipe node \'%s\' has a circular dependency on itself' % node.name
            raise InvalidDefinition('CIRCULAR_DEPENDENCY', msg)

        if node.name not in perm_set:
            temp_set.add(node.name)
            for child_node in node.children.values():
                self._topological_order_visit(child_node, results, perm_set, temp_set)
            perm_set.add(node.name)
            temp_set.remove(node.name)
            results.insert(0, node.name)
