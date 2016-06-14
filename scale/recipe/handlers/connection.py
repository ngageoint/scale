"""Defines the classes for handling recipe node connections"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod


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

    @abstractmethod
    def add_input_to_job_data(self, job_data, recipe_data, parent_results):
        """Adds the data for this input to the given job data

        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param recipe_data: The recipe data
        :type recipe_data: :class:`recipe.configuration.data.recipe_data.RecipeData`
        :param parent_results: The results of each parent job stored by job name
        :type parent_results: {str: :class:`job.configuration.results.job_results.JobResults`}
        """

        raise NotImplementedError()

    @abstractmethod
    def is_equal_to(self, connection, matched_recipe_inputs, matched_job_names):
        """Returns true if and only if the given node input connection is equal to this one. This is used for checking
        the equality of two inputs across two different recipe graphs. Since the different graphs may have different
        recipe inputs or different job names for the same node, dicts of matched recipe inputs and job names between the
        graphs are provided.

        :param connection: The node input connection
        :type connection: :class:`recipe.handlers.connection.NodeInputConnection`
        :param matched_recipe_inputs: Dict matching recipe input names (connection is the key, self is the value)
        :type matched_recipe_inputs: {string: string}
        :param matched_job_names: Dict matching job names for identical nodes (connection is the key, self is the value)
        :type matched_job_names: {string: string}
        :returns: True if the connections are equal, False otherwise
        :rtype: bool
        """

        raise NotImplementedError()


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

    def add_input_to_job_data(self, job_data, recipe_data, parent_results):
        """See :meth:`recipe.handlers.connection.NodeInputConnection.add_input_to_job_data`
        """

        parent_results = parent_results[self.node.job_name]
        parent_results.add_output_to_data(self.output_name, job_data, self.input_name)

    def is_equal_to(self, connection, matched_recipe_inputs, matched_job_names):
        """See :meth:`recipe.handlers.connection.NodeInputConnection.is_equal_to`
        """

        if not isinstance(connection, DependencyInputConnection):
            return False

        same_input_name = self.input_name == connection.input_name
        same_job_name = self.node.job_name == matched_job_names[connection.node.job_name]
        same_output_name = self.output_name == connection.output_name

        return same_input_name and same_job_name and same_output_name


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

    def add_input_to_job_data(self, job_data, recipe_data, parent_results):
        """See :meth:`recipe.handlers.connection.NodeInputConnection.add_input_to_job_data`
        """

        recipe_data.add_input_to_data(self.recipe_input.input_name, job_data, self.input_name)

    def is_equal_to(self, connection, matched_recipe_inputs, matched_job_names):
        """See :meth:`recipe.handlers.connection.NodeInputConnection.is_equal_to`
        """

        if not isinstance(connection, RecipeInputConnection):
            return False

        same_input_name = self.input_name == connection.input_name
        matched_recipe_input_name = matched_recipe_inputs[connection.recipe_input.input_name]
        same_recipe_input_name = self.recipe_input.input_name == matched_recipe_input_name
        return same_input_name and same_recipe_input_name
