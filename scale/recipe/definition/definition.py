"""Defines the class for representing a recipe definition"""
from __future__ import unicode_literals

from recipe.definition.exceptions import InvalidDefinition
from recipe.definition.node import Node


class RecipeDefinition(object):
    """Represents a recipe definition, which consists of an input interface and a directed acyclic graph of recipe nodes
    """

    def __init__(self, interface):
        """Constructor

        :param interface: The input interface for the recipe
        :type interface: :class:`data.interface.interface.Interface`
        """

        self.interface = interface
        self._graph = {}  # {Name: Node}
        self._root_nodes = {}  # {Name: Node}, root nodes have no dependencies
        self._topological_order = None  # Cached topological ordering of the nodes (list of names)

    # TODO: add hard-coded data (call them default values?)

    def add_connection(self, node_name, connection):
        """Adds a connection to the input of the node

        :param node_name: The name of the node whose input is being connected to
        :type node_name: string
        :param connection: List of tuples where first item is parent output name and second item is child input name
        :type connection: :class:`recipe.definition.connection.InputConnection`

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the node is unknown or the connection is a
            duplicate
        """

        if node_name not in self._graph:
            raise InvalidDefinition('UNKNOWN_NODE', 'Node \'%s\' is not defined' % node_name)

        node = self._graph[node_name]
        node.add_connection(connection)

    def add_dependency(self, parent_name, child_name):
        """Adds a dependency that one node has upon another node

        :param parent_name: The name of the parent node
        :type parent_name: string
        :param child_name: The name of the child node
        :type child_name: string

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If either node is unknown
        """

        if child_name not in self._graph:
            raise InvalidDefinition('UNKNOWN_NODE', 'Node \'%s\' is not defined' % child_name)
        if parent_name not in self._graph:
            raise InvalidDefinition('UNKNOWN_NODE', 'Node \'%s\' is not defined' % parent_name)

        child_node = self._graph[child_name]
        parent_node = self._graph[parent_name]
        child_node.add_dependency(parent_node)
        if child_name in self._root_nodes:
            del self._root_nodes[child_name]

        self._topological_order = None  # Invalidate cache

    def add_node(self, name):
        """Adds a node to the recipe graph with the given name

        :param name: The node name
        :type name: string

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the node is duplicated
        """

        if name in self._graph:
            raise InvalidDefinition('DUPLICATE_NODE', 'Node \'%s\' is already defined' % name)

        node = Node(name)
        self._graph[name] = node
        self._root_nodes[name] = node
        self._topological_order = None  # Invalidate cache

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

    # TODO: create validate methods for passing data/interfaces to this recipe

    # TODO: validate, check old recipe_definition for things to check
    # TODO: will need job type and recipe type input interfaces to validate against, also need job type output interfaces
    def validate(self):
        """Validates this recipe definition

        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the definition is invalid
        """

        # TODO: validate recipe input?
        # TODO: validate topological order (checks for cycles)
        # TODO: check for recipe type containing itself?
        # TODO: validate each node
        return []

    def _calculate_topological_order(self):
        """Calculates a valid topological ordering (dependency order) for the recipe

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the definition contains a circular
            dependency
        """

        results = []
        perm_set = set()
        temp_set = set()
        unmarked_set = set(self._graph.keys())
        while unmarked_set:
            node_name = unmarked_set.pop()
            node = self._graph[node_name]
            self._topological_order_visit(node, results, perm_set, temp_set)
            unmarked_set = set(self._graph.keys()) - perm_set

        self._topological_order = results

    def _topological_order_visit(self, node, results, perm_set, temp_set):
        """Recursive depth-first search algorithm for determining a topological ordering of the recipe nodes

        :param node: The current node
        :type node: :class:`recipe.definition.node.Node`
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
            for child_node in node.children:
                self._topological_order_visit(child_node, results, perm_set, temp_set)
            perm_set.add(node.name)
            temp_set.remove(node.name)
            results.insert(0, node.name)
