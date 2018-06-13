"""Defines the class for handling recipe graph deltas"""
from __future__ import unicode_literals

from collections import namedtuple

Change = namedtuple('Change', ['name', 'description'])
Reason = namedtuple('Reason', ['name', 'description'])

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

        self.can_be_reprocessed = True
        self.reasons = []
        self._graph_a = graph_a
        self._graph_b = graph_b
        self._matched_recipe_inputs = {}  # {Recipe Input B: Recipe Input A}
        self._identical_nodes = {}  # {Job Name B: Job Name A}
        self._changed_nodes = {}  # {Job Name B: Job Name A}
        self._new_nodes = set()  # {Job Name B}
        self._deleted_nodes = set()  # {Job Name A}
        self._force_reprocess = set()
        self._changes = {}  # {Job Name B: [Change]}
        self._topo_a_nodes = self._graph_a.get_topological_order()  # Job names from A in topological order
        self._topo_b_nodes = self._graph_b.get_topological_order()  # Job names from B in topological order
        self._unresolved_a_nodes = set(self._topo_a_nodes)  # {Job Name A}
        self._unresolved_b_nodes = set(self._topo_b_nodes)  # {Job Name B}

        self._match_recipe_inputs()
        self._match_identical_nodes()
        self._match_changed_nodes()
        self._new_nodes = self._unresolved_b_nodes
        self._deleted_nodes = self._unresolved_a_nodes
        self._unresolved_a_nodes = set()
        self._unresolved_b_nodes = set()

    def get_changed_nodes(self):
        """Returns the job name mapping between the nodes in graph A and graph B that represent changed nodes that
        supersede one another

        :returns: Dict where the keys are job names from graph B that map to the job names from graph A that they
            supersede
        :rtype: {string: string}
        """

        return self._changed_nodes

    def get_deleted_nodes(self):
        """Returns the set of job names from graph A that represent job nodes that were deleted in graph B

        :returns: The set of job names from graph A that were deleted in graph B
        :rtype: {string}
        """

        return self._deleted_nodes

    def get_identical_nodes(self):
        """Returns the job name mapping between the nodes in graph A and graph B that are identical with respect to each
        other.

        :returns: Dict where the keys are job names from graph B that map to the job names from graph A that are
            identical
        :rtype: {string: string}
        """

        return self._identical_nodes

    def get_new_nodes(self):
        """Returns the set of job names from graph B that represent job nodes that are new (did not exist in graph A)

        :returns: The set of job names from graph B that are new
        :rtype: {string}
        """

        return self._new_nodes

    def reprocess_identical_node(self, job_name):
        """Marks the node with the given job name as changed instead of identical. This can be used to reprocess jobs
        that have not changed. All children nodes will be changed as well.

        :param job_name: The job name of the node
        :type job_name: string
        """

        nodes_to_reprocess = [job_name]
        while nodes_to_reprocess:
            job_name = nodes_to_reprocess.pop()
            if job_name in self._identical_nodes:
                node = self._graph_b.get_node(job_name)
                self._changed_nodes[job_name] = self._identical_nodes[job_name]
                del self._identical_nodes[job_name]
                self._force_reprocess.add(job_name)
                for child in node.children:
                    nodes_to_reprocess.append(child.node_name)

    def _determine_changes(self, job_name_a, job_name_b):
        """Compares the node from graph A and the node from graph B and sets the changes found between them

        :param job_name_a: The job name for the node from graph A
        :type job_name_a: str
        :param job_name_b: The job name for the node from graph B
        :type job_name_b: str
        """

        node_a = self._graph_a.get_node(job_name_a)
        node_b = self._graph_b.get_node(job_name_b)
        changes = []
        self._changes[job_name_b] = changes

        # Check for same job type name and version
        if node_a.job_type_name != node_b.job_type_name:
            msg = 'Job type changed from %s to %s'
            changes.append(Change('JOB_TYPE_CHANGE', msg % (node_a.job_type_name, node_b.job_type_name)))
            return
        if node_a.job_type_version != node_b.job_type_version:
            msg = 'Job type version changed from %s to %s'
            changes.append(Change('JOB_TYPE_VERSION_CHANGE', msg % (node_a.job_type_version, node_b.job_type_version)))
            return

        # Check that A and B have matching parents that are identical to one another
        a_parent_names = set(a_parent.node_name for a_parent in node_a.parents)
        for b_parent in node_b.parents:
            b_parent_name = b_parent.node_name
            if b_parent_name not in self._identical_nodes:
                changes.append(Change('PARENT_CHANGE', 'Parent job %s changed' % b_parent_name))
                return  # B has a parent that is not identical to any other node
            matched_a_parent_name = self._identical_nodes[b_parent_name]
            if matched_a_parent_name not in a_parent_names:
                changes.append(Change('NEW_PARENT', 'New parent job %s added' % b_parent_name))
                return  # B has a parent that does not match a parent of A
            a_parent_names.remove(matched_a_parent_name)
        if a_parent_names:
            changes.append(Change('REMOVED_PARENT', 'Previous parent job %s removed' % a_parent_names.pop()))
            return  # A has a parent that does not match a parent of B

        # Check that A and B use the same inputs
        a_inputs = dict(node_a.inputs)
        for b_input_name in node_b.inputs:
            if b_input_name not in a_inputs:
                changes.append(Change('NEW_INPUT', 'New input %s added' % b_input_name))
                return  # B input not defined for A
            b_input = node_b.inputs[b_input_name]
            a_input = a_inputs[b_input_name]
            if not a_input.is_equal_to(b_input, self._matched_recipe_inputs, self._identical_nodes):
                changes.append(Change('INPUT_CHANGE', 'Input %s changed' % b_input_name))
                return  # A and B have a non-matching input
            del a_inputs[b_input_name]
        if a_inputs:
            changes.append(Change('REMOVED_INPUT', 'Previous input %s removed' % a_inputs.keys().pop()))
            return  # A input not defined for B

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
        a_parent_names = set(a_parent.node_name for a_parent in node_a.parents)
        for b_parent in node_b.parents:
            b_parent_name = b_parent.node_name
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
            if not a_input.is_equal_to(b_input, self._matched_recipe_inputs, self._identical_nodes):
                return False  # A and B have a non-matching input
            del a_inputs[b_input_name]
        if a_inputs:
            return False  # A input not defined for B

        return True

    def _match_changed_nodes(self):
        """Compares graphs A and B and matches all nodes that are "changed" (node B supersedes node A). This should be
        done after matching all identical nodes.
        """

        # Currently "changed" jobs are detected as nodes with the same job_name but are not identical
        for job_name in set(self._unresolved_b_nodes):
            if job_name in self._unresolved_a_nodes:
                self._changed_nodes[job_name] = job_name
                self._unresolved_a_nodes.remove(job_name)
                self._unresolved_b_nodes.remove(job_name)
                self._determine_changes(job_name, job_name)

    def _match_identical_nodes(self):
        """Compares graphs A and B and matches all nodes that are identical
        """

        for job_name_b in self._topo_b_nodes:
            for job_name_a in self._unresolved_a_nodes:
                if self._is_node_identical(job_name_a, job_name_b):
                    self._identical_nodes[job_name_b] = job_name_a
                    self._unresolved_a_nodes.remove(job_name_a)
                    self._unresolved_b_nodes.remove(job_name_b)
                    break

    def _match_recipe_inputs(self):
        """Compares graphs A and B and matches all recipe inputs that are identical
        """

        # Right now the new recipe (B) expects to see an identically named A input for each required B input
        for b_input_name in self._graph_b.inputs:
            b_input = self._graph_b.inputs[b_input_name]
            if b_input_name not in self._graph_a.inputs:
                if b_input.required:
                    self.can_be_reprocessed = False
                    desc = 'New required input %s does not exist in previous recipes' % b_input_name
                    reason = Reason('NEW_REQUIRED_INPUT', desc)
                    self.reasons.append(reason)
                continue
            a_input = self._graph_a.inputs[b_input_name]
            if a_input.input_type != b_input.input_type:
                self.can_be_reprocessed = False
                desc = 'Input %s changed type and cannot be reused from previous recipes' % b_input_name
                reason = Reason('INPUT_TYPE_CHANGE', desc)
                self.reasons.append(reason)
                continue
            if b_input.required and not a_input.required:
                self.can_be_reprocessed = False
                desc = 'Input %s is now required and may not exist in previous recipes' % b_input_name
                reason = Reason('INPUT_NOW_REQUIRED', desc)
                self.reasons.append(reason)
                continue
            self._matched_recipe_inputs[b_input_name] = b_input_name
