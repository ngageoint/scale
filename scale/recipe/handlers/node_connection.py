"""Defines the classes for handling recipe node connections"""
from __future__ import unicode_literals

from abc import ABCMeta


class NodeInputConnection(object):
    """Abstract base class that represents a connection to a recipe node input
    """

    __metaclass__ = ABCMeta

    def __init__(self, input_name):
        """Constructor

        :param input_name: The name of the node's input
        :type input_name: str
        """

        self.input_name = input_name


class DependencyInputConnection(NodeInputConnection):
    """Represents a connection from one node's output to another node's input
    """

    def __init__(self, input_name, node, output_name):
        """Constructor

        :param input_name: The name of the node's input
        :type input_name: str
        :param node: The dependency node providing its output
        :type node: :class:`recipe.handlers.node.RecipeNode`
        :param output_name: The name of the dependency node's output
        :type output_name: str
        """

        super(DependencyInputConnection, self).__init__(input_name)

        self.node = node
        self.output_name = output_name


class RecipeInputConnection(NodeInputConnection):
    """Represents a connection from a recipe's input to a node's input
    """

    def __init__(self, input_name, recipe_input):
        """Constructor

        :param input_name: The name of the node's input
        :type input_name: str
        :param recipe_input: The recipe input
        :type recipe_input: :class:`job.handlers.inputs.base_input.Input`
        """

        super(RecipeInputConnection, self).__init__(input_name)

        self.recipe_input = recipe_input
