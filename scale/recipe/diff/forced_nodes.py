"""Defines the class for representing nodes within a recipe that are being forced to reprocess"""
from __future__ import unicode_literals


class ForcedNodes(object):
    """Represents nodes within a recipe that are being forced to reprocess
    """

    def __init__(self):
        """Constructor
        """

        self.all_nodes = False
        self._nodes = set()
        self._subrecipe_nodes = {}  # {Node name: ForcedNodes}

    def add_node(self, node_name):
        """Adds a node to be forced to be reprocessed

        :param node_name: The node name
        :type node_name: string
        """

        if not self.all_nodes:
            self._nodes.add(node_name)

    def add_subrecipe(self, node_name, forced_nodes):
        """Adds a sub-recipe node to be forced to be reprocessed

        :param node_name: The node name of the sub-recipe
        :type node_name: string
        :param forced_nodes: The forced nodes for the sub-recipe
        :type forced_nodes: :class:`recipe.diff.forced_nodes.ForcedNodes`
        """

        if not self.all_nodes:
            self._nodes.add(node_name)
            self._subrecipe_nodes[node_name] = forced_nodes

    def get_forced_nodes_for_subrecipe(self, node_name):
        """Returns the ForcedNodes object for the given sub-recipe, possibly None

        :param node_name: The node name of the sub-recipe
        :type node_name: string
        :returns: The forced nodes for the sub-recipe
        :rtype: :class:`recipe.diff.forced_nodes.ForcedNodes`
        """

        if self.all_nodes:
            forced_nodes = ForcedNodes()
            forced_nodes.set_all_nodes()
        elif node_name in self._subrecipe_nodes:
            forced_nodes = self._subrecipe_nodes[node_name]
        else:
            forced_nodes = None

        return forced_nodes

    def get_forced_node_names(self):
        """Returns the forced node names

        :returns: The forced node names
        :rtype: set
        """

        return self._nodes

    def is_node_forced_to_reprocess(self, node_name):
        """Indicates whether the given node is forced to reprocess

        :param node_name: The node name
        :type node_name: string
        :returns: True if the given node is forced to reprocess, False otherwise
        :rtype: bool
        """

        return self.all_nodes or node_name in self._nodes

    def set_all_nodes(self):
        """Sets all nodes to be forced to reprocess
        """

        self.all_nodes = True
        self._nodes = set()
        self._subrecipe_nodes = {}
