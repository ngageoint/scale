"""Defines the class for handling recipe graph deltas"""
from __future__ import unicode_literals


class RecipeGraphDelta(object):
    """Represents the change between two different recipe graphs
    """

    def __init__(self, graph_a, graph_b):
        """Creates a representation of the delta from recipe graph A to recipe graph B

        :param graph_a: The first recipe graph
        :type graph_a: :class:`recipe.handlers.graph.RecipeGraph`
        :param graph_b: The second recipe graph
        :type graph_b: :class:`recipe.handlers.graph.RecipeGraph`
        """

        self._graph_a = graph_a
        self._graph_b = graph_b
        self._identical_nodes = {}  # {Job Name B: Job Name A}
        self._changed_nodes = {}  # {Job Name B: Job Name A}
        self._new_nodes = set()  # {Job Name B}
        self._deleted_nodes = set()  # {Job Name A}
        self._topo_a_nodes = self._graph_a.get_topological_order()  # Job names from A in topological order
        self._topo_b_nodes = self._graph_b.get_topological_order()  # Job names from B in topological order
        self._unresolved_a_nodes = set(self._topo_a_nodes)  # {Job Name A}
        self._unresolved_b_nodes = set(self._topo_b_nodes)  # {Job Name B}

        self._match_identical_nodes()
        # TODO: add code to actually check for changed nodes (nodes with changed versions, parents, or inputs)
        self._new_nodes = self._unresolved_b_nodes
        self._deleted_nodes = self._unresolved_a_nodes
        self._unresolved_a_nodes = set()
        self._unresolved_b_nodes = set()

    def get_identical_nodes(self):
        """Returns the job name mapping between the nodes in graph A and graph B that are identical with respect to each
        other.

        :returns: Dict where the keys are job names from graph B that map to the job names from graph A that are
            identical
        :rtype: {string: string}
        """

        return self._identical_nodes

    def _is_node_identical(self, job_name_a, job_name_b):
        """Compares the node from graph A and the node from graph B and return true if they are identical. This method
        assumes that the parents of node B have already been categorized if they are identical to any nodes in graph A
        (the B nodes must be processed in topological order).

        :param job_name_a: The job name for the node from graph A
        :type job_name_a: str
        :param job_name_b: The job name for the node from graph B
        :type job_name_b: str
        :returns: True if the nodes are identical, False otherwise
        :rtype: bool
        """

        node_a = self._graph_a.get_node(job_name_a)
        node_b = self._graph_b.get_node(job_name_b)

        # Check for same job type name and version
        if node_a.job_type_name != node_b.job_type_name or node_a.job_type_version != node_b.job_type_version:
            return False

        # Check that A and B have matching parents that are identical to one another
        a_parent_names = set(a_parent.job_name for a_parent in node_a.parents)
        for b_parent in node_b.parents:
            b_parent_name = b_parent.job_name
            if b_parent_name not in self._identical_nodes:
                return False  # B has a parent that is not identical to any other node
            matched_a_parent_name = self._identical_nodes[b_parent_name]
            if matched_a_parent_name not in a_parent_names:
                return False  # B has a parent that does not match a parent of A
            a_parent_names.remove(matched_a_parent_name)
        if a_parent_names:
            return False  # A has a parent that does not match a parent of B

        # Check that A and B use the same inputs
        a_inputs = dict(node_a.inputs)
        for b_input_name in node_b.inputs:
            if b_input_name not in a_inputs:
                return False  # B input not defined for A
            b_input = node_b.inputs[b_input_name]
            a_input = a_inputs[b_input_name]
            if not a_input.is_equal_to(b_input, self._identical_nodes):
                return False  # A and B have a non-matching input
            del a_inputs[b_input_name]
        if a_inputs:
            return False  # A input not defined for B

        return True

    def _match_identical_nodes(self):
        """Compares graphs A and B and matches all nodes that are identical
        """

        for job_name_b in self._topo_b_nodes:
            for job_name_a in self._topo_a_nodes:
                if self._is_node_identical(job_name_a, job_name_b):
                    self._identical_nodes[job_name_b] = job_name_a
                    self._unresolved_a_nodes.remove(job_name_a)
                    self._unresolved_b_nodes.remove(job_name_b)
                    break
