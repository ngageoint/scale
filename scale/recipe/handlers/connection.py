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
