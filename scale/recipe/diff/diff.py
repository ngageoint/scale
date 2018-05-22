"""Defines the class for representing a diff between two recipe definitions"""
from __future__ import unicode_literals

from collections import namedtuple

from data.interface.exceptions import InvalidInterfaceConnection
from recipe.diff.node import create_diff_for_node, NodeDiff


Reason = namedtuple('Reason', ['name', 'description'])


class RecipeDiff(object):
    """Represents the diff (difference) betweeen two different recipe definitions
    """

    def __init__(self, prev_recipe_definition, recipe_definition):
        """Constructor

        :param prev_recipe_definition: The previous recipe definition
        :type prev_recipe_definition: :class:`recipe.definition.definition.RecipeDefinition`
        :param recipe_definition: The newer recipe definition
        :type recipe_definition: :class:`recipe.definition.definition.RecipeDefinition`
        """

        self.can_be_reprocessed = True
        self.reasons = []
        self.graph = {}  # {Name: NodeDiff}

        self._compare_input_interfaces(prev_recipe_definition, recipe_definition)
        self._create_diff_graph(prev_recipe_definition, recipe_definition)

    def get_nodes_to_copy(self):
        """Returns a dict of node diffs for the nodes that should be copied during a reprocess

        :returns: Dict of node diffs stored by node name
        :rtype: dict
        """

        nodes_to_copy = {}

        if self.can_be_reprocessed:
            for node_diff in self.graph.values():
                if node_diff.should_be_copied():
                    nodes_to_copy[node_diff.name] = node_diff

        return nodes_to_copy

    def get_nodes_to_supersede(self):
        """Returns a dict of node diffs for the nodes that should be superseded during a reprocess

        :returns: Dict of node diffs stored by node name
        :rtype: dict
        """

        nodes_to_supersede = {}

        if self.can_be_reprocessed:
            for node_diff in self.graph.values():
                if node_diff.should_be_superseded():
                    nodes_to_supersede[node_diff.name] = node_diff

        return nodes_to_supersede

    def get_nodes_to_unpublish(self):
        """Returns a dict of node diffs for the nodes that require unpublishing as a result of a reprocess

        :returns: Dict of node diffs stored by node name
        :rtype: dict
        """

        nodes_to_unpublish = {}

        if self.can_be_reprocessed:
            for node_diff in self.graph.values():
                if node_diff.should_be_unpublished():
                    nodes_to_unpublish[node_diff.name] = node_diff

        return nodes_to_unpublish

    def set_force_reprocess(self, reprocess_nodes):
        """Provides a set of nodes to force to reprocess. The given dict contains node names as keys representing the
        nodes to force to reprocess. Each node name maps to a dict, which is empty for non-recipe nodes. For recipe
        nodes, the dict recursively represents the node names within that recipe that should be foreced to reprocess,
        and so on.

        :param reprocess_nodes: Dict where each key is a node name mapping recursively to another dict of nodes
        :type reprocess_nodes: dict
        """

        for node_name in reprocess_nodes.keys():
            if node_name in self.graph:
                self.graph[node_name].set_force_reprocess(reprocess_nodes)

    def _create_diff_graph(self, prev_recipe_definition, recipe_definition):
        """Creates the graph containing the diff for each node

        :param prev_recipe_definition: The previous recipe definition
        :type prev_recipe_definition: :class:`recipe.definition.definition.RecipeDefinition`
        :param recipe_definition: The newer recipe definition
        :type recipe_definition: :class:`recipe.definition.definition.RecipeDefinition`
        """

        # Topological order is important since we assume a node's parents have been processed first
        for node_name in recipe_definition.get_topological_order():
            # Create a matching diff for this node
            node = recipe_definition.graph[node_name]
            node_diff = create_diff_for_node(node, self.can_be_reprocessed, NodeDiff.NEW)
            self.graph[node_diff.name] = node_diff
            for parent_name in node.parents.keys():
                parent_diff = self.graph[parent_name]
                node_diff.add_dependency(parent_diff)

            # Find matching node in previous definition and compare
            if node_diff.name in prev_recipe_definition.graph:
                prev_node = prev_recipe_definition.graph[node_diff.name]
                node_diff.compare_to_previous(prev_node)

        # Add deleted nodes from previous definition
        for node_name in prev_recipe_definition.get_topological_order():
            if node_name in self.graph:
                continue
            deleted_node = prev_recipe_definition.graph[node_name]
            deleted_node_diff = create_diff_for_node(deleted_node, self.can_be_reprocessed, NodeDiff.DELETED)
            self.graph[deleted_node_diff.name] = deleted_node_diff
            for parent_name in deleted_node.parents.keys():
                parent_diff = self.graph[parent_name]
                deleted_node_diff.add_dependency(parent_diff)

    def _compare_input_interfaces(self, prev_recipe_definition, recipe_definition):
        """Compares the input interfaces betweeen the recipe definitions

        :param prev_recipe_definition: The previous recipe definition
        :type prev_recipe_definition: :class:`recipe.definition.definition.RecipeDefinition`
        :param recipe_definition: The newer recipe definition
        :type recipe_definition: :class:`recipe.definition.definition.RecipeDefinition`
        """

        try:
            # Ensure that previous input interface can be passed to newer input interface
            recipe_definition.input_interface.validate_connection(prev_recipe_definition.input_interface)
        except InvalidInterfaceConnection as ex:
            self.can_be_reprocessed = False
            self.reasons.append(Reason('INPUT_CHANGE', 'Input interface has changed: %s' % ex.error.description))
