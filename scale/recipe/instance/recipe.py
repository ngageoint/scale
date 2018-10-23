"""Defines the class for representing an instance of an executing recipe"""
from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from recipe.definition.node import ConditionNodeDefinition, JobNodeDefinition, RecipeNodeDefinition
from recipe.instance.node import ConditionNodeInstance, DummyNodeInstance, JobNodeInstance, RecipeNodeInstance


logger = logging.getLogger(__name__)


class RecipeInstance(object):
    """Represents an executing recipe
    """

    def __init__(self, definition, recipe_model, recipe_nodes):
        """Constructor

        :param definition: The recipe definition
        :type definition: :class:`recipe.definition.definition.RecipeDefinition`
        :param recipe_model: The recipe model
        :type recipe_model: :class:`recipe.models.Recipe`
        :param recipe_nodes: The list of RecipeNode models with related fields populated
        :type recipe_nodes: list
        """

        self._definition = definition
        self.recipe_model = recipe_model
        self.graph = {}  # {Name: Node}

        # Create graph of recipe nodes
        recipe_node_dict = {recipe_node.node_name: recipe_node for recipe_node in recipe_nodes}
        for node_name in self._definition.get_topological_order():
            node_definition = self._definition.graph[node_name]
            if node_name in recipe_node_dict:
                recipe_node_model = recipe_node_dict[node_name]
                is_original = recipe_node_model.is_original
                if node_definition.node_type == JobNodeDefinition.NODE_TYPE:
                    node = JobNodeInstance(node_definition, recipe_node_model.job, is_original)
                elif node_definition.node_type == RecipeNodeDefinition.NODE_TYPE:
                    node = RecipeNodeInstance(node_definition, recipe_node_model.sub_recipe, is_original)
                elif node_definition.node_type == ConditionNodeDefinition.NODE_TYPE:
                    node = ConditionNodeInstance(node_definition, recipe_node_model.condition, is_original)
            else:
                node = DummyNodeInstance(node_definition)
            self.graph[node.name] = node
            for parent_name in node_definition.parents.keys():
                node.add_dependency(self.graph[parent_name])

    def get_jobs_to_update(self):
        """Returns the jobs within this recipe that should be updated to a new status (either BLOCKED or PENDING)

        :returns: A dict with status (PENDING or BLOCKED) mapping to lists of job IDs
        :rtype: dict
        """

        blocked_job_ids = []
        pending_job_ids = []

        for node_name in self._definition.get_topological_order():
            if node_name in self.graph:
                node = self.graph[node_name]
                node.get_jobs_to_update(pending_job_ids, blocked_job_ids)

        return {'BLOCKED': blocked_job_ids, 'PENDING': pending_job_ids}

    def get_nodes_to_create(self):
        """Returns the node definitions within this recipe for nodes that should be created

        :returns: A dict where node names map to node definitions
        :rtype: dict
        """

        nodes_to_create = {}

        for node_name in self._definition.get_topological_order():
            if node_name in self.graph:
                node = self.graph[node_name]
                if node.needs_to_be_created():
                    nodes_to_create[node_name] = node.definition

        return nodes_to_create

    def get_nodes_to_process_input(self):
        """Returns the node instances within this recipe for nodes that need to process their input

        :returns: A dict where node names map to node instances
        :rtype: dict
        """

        nodes_to_process_input = {}

        if self.recipe_model.has_input():  # If recipe doesn't have input yet, no nodes can process input yet
            for node_name in self._definition.get_topological_order():
                if node_name in self.graph:
                    node = self.graph[node_name]
                    if node.needs_to_process_input():
                        nodes_to_process_input[node_name] = node

        return nodes_to_process_input

    def get_original_leaf_nodes(self):
        """Returns a mapping of original leaf nodes with the recipe

        :returns: A dict with node name mapping to original leaf nodes
        :rtype: dict
        """

        leaf_nodes = {n.name: n for n in self.graph.values() if n.is_original and not n.children}  # {Name: Node}

        return leaf_nodes

    def has_completed(self):
        """Indicates whether this recipe has completed

        :returns: True if this recipe has completed, False otherwise
        :rtype: bool
        """

        if self.get_nodes_to_create():
            # If there are more nodes to create, then recipe has not completed
            return False

        for node_name in self._definition.get_topological_order():
            if node_name in self.graph:
                node = self.graph[node_name]
                if not node.is_completed():
                    # A node has not yet completed, so recipe has not completed
                    return False
            else:
                # For some weird reason, probably a bug, there is a missing node
                logger.error('Missing recipe node \'%s\'', node_name)
                return False

        return True
