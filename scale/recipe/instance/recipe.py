"""Defines the class for representing an instance of an executing recipe"""
from __future__ import absolute_import
from __future__ import unicode_literals

from data.interface.exceptions import InvalidInterface
from recipe.definition.connection import DependencyInputConnection, RecipeInputConnection
from recipe.definition.exceptions import InvalidDefinition
from recipe.definition.node import JobNode, RecipeNode


class RecipeDefinition(object):
    """Represents an executing recipe
    """

    # TODO: will pass in new RecipeNode models
    def __init__(self, definition):
        """Constructor

        :param definition: The recipe definition
        :type definition: :class:`recipe.definition.node.Node`
        """

        self._definition = definition
        self.graph = {}  # {Name: Node}

        # TODO: create the graph and all dependency links from definition and RecipeNode models

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
            for child_node in node.children.values():
                self._topological_order_visit(child_node, results, perm_set, temp_set)
            perm_set.add(node.name)
            temp_set.remove(node.name)
            results.insert(0, node.name)
