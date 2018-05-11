"""Defines the class for representing a recipe definition"""
from __future__ import unicode_literals

from recipe.definition.exceptions import InvalidDefinition


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

    # TODO: add hard-coded data

    # TODO - implement adding dependencies and connections that can be validated
    def add_dependency(self, parent_job_name, child_job_name, connections):
        """Adds a dependency that one job has upon another job

        :param parent_job_name: The name of the parent job
        :type parent_job_name: string
        :param child_job_name: The name of the child job
        :type child_job_name: string
        :param connections: List of tuples where first item is parent output name and second item is child input name
        :type connections: [(string, string)]
        """

        self._topological_order = None  # Invalidate cache

        # TODO: implement
        parent_node = self.get_node(parent_job_name)
        child_node = self.get_node(child_job_name)
        dependency_connections = []
        for connection in connections:
            output_name = connection[0]
            input_name = connection[1]
            dependency_connection = DependencyInputConnection(input_name, parent_node, output_name)
            dependency_connections.append(dependency_connection)

        child_node.add_dependency(parent_node, dependency_connections)
        parent_node.add_child(child_node)
        if child_job_name in self._root_nodes:
            del self._root_nodes[child_job_name]

    def add_node(self, node):
        """Adds a node to the recipe graph. Nodes should not have any parents or children defined yet.

        :param node: The recipe node
        :type node: :class:`recipe.definition.node.Node`
        """

        self._graph[node.name] = node
        self._root_nodes[node.name] = node
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
