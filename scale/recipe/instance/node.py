"""Defines the classes for representing nodes within a recipe"""
from __future__ import unicode_literals

from abc import ABCMeta


class Node(object):
    """Represents a node within a recipe
    """

    __metaclass__ = ABCMeta

    def __init__(self, definition):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.NodeDefinition`
        """

        self._definition = definition

        self.name = self._definition.name
        self.parents = {}  # {Name: Node}
        self.children = {}  # {Name: Node}

    def add_dependency(self, node):
        """Adds a dependency that this node has on the given node

        :param node: The dependency node to add
        :type node: :class:`recipe.instance.node.Node`
        """

        self.parents[node.name] = node
        node.children[self.name] = self


class JobNode(Node):
    """Represents a job within a recipe
    """

    def __init__(self, definition, job):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.JobNodeDefinition`
        :param job: The job model
        :type job: :class:`job.models.Job`
        """

        super(JobNode, self).__init__(definition)

        self.job = job


class RecipeNode(Node):
    """Represents a recipe within a recipe
    """

    def __init__(self, definition, recipe):
        """Constructor

        :param definition: The definition of this node in the recipe
        :type definition: :class:`recipe.definition.node.RecipeNodeDefinition`
        :param recipe: The recipe model
        :type recipe: :class:`recipe.models.Recipe`
        """

        super(RecipeNode, self).__init__(definition)

        self.recipe = recipe
