"""Defines the class for handling recipe nodes"""
from __future__ import unicode_literals


class RecipeNode(object):
    """Represents a node in a recipe
    """

    def __init__(self, job_name, job_type_name, job_type_version):
        """Constructor

        :param job_name: The unique name of the node's job
        :type job_name: str
        :param job_type_name: The name of the node's job type
        :type job_type_name: str
        :param job_type_version: The version of the node's job type
        :type job_type_version: str
        """

        self.job_name = job_name
        self.job_type_name = job_type_name
        self.job_type_version = job_type_version
        self._parents = []
        self._children = []
        self._inputs = {}  # {Input name: NodeInputConnection}

    def add_child(self, child_node):
        """Adds a child node that is dependent on this node

        :param child_node: The child node to add
        :type child_node: :class:`recipe.handlers.node.RecipeNode`
        """

        self._children.append(child_node)

    def add_dependency(self, parent_node, connections):
        """Adds a parent node upon which this node is dependent

        :param parent_node: The parent node to add
        :type parent_node: :class:`recipe.handlers.node.RecipeNode`
        :param connections: The connections to the parent's outputs
        :type connections: [:class:`recipe.handlers.connection.DependencyInputConnection`]
        """

        self._parents.append(parent_node)
        for connection in connections:
            self._inputs[connection.input_name] = connection

    def add_recipe_input(self, recipe_input):
        """Adds a recipe input connection to this node

        :param recipe_input: The recipe input connection
        :type recipe_input: :class:`recipe.handlers.connection.RecipeInputConnection`
        """

        self._inputs[recipe_input.input_name] = recipe_input
