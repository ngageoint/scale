"""Defines the class for representing an instance of an executing recipe"""
from __future__ import absolute_import
from __future__ import unicode_literals

from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition
from recipe.instance.node import JobNode, RecipeNode


class Recipe(object):
    """Represents an executing recipe
    """

    def __init__(self, definition, recipe_nodes):
        """Constructor

        :param definition: The recipe definition
        :type definition: :class:`recipe.definition.node.Node`
        :param recipe_nodes: The list of RecipeNode models with related fields populated
        :type recipe_nodes: list
        """

        self._definition = definition
        self.graph = {}  # {Name: Node}

        # Create graph of recipe nodes
        recipe_node_dict = {recipe_node.node_name: recipe_node for recipe_node in recipe_nodes}
        for node_name in self._definition.get_topological_order():
            node_definition = self._definition.graph[node_name]
            recipe_node_model = recipe_node_dict[node_name]
            if node_definition.node_type == JobNodeDefinition.NODE_TYPE:
                node = JobNode(node_definition, recipe_node_model.job)
            elif node_definition.node_type == RecipeNodeDefinition.NODE_TYPE:
                node = RecipeNode(node_definition, recipe_node_model.sub_recipe)
            self.graph[node.name] = node
            for parent_name in node_definition.parents.keys():
                node.add_dependency(self.graph[parent_name])
