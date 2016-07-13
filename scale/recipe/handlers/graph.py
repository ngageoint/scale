"""Defines the class for handling recipe graphs"""
from __future__ import unicode_literals

from recipe.handlers.connection import DependencyInputConnection, RecipeInputConnection
from recipe.handlers.node import RecipeNode


class RecipeGraph(object):
    """Represents a graph of recipe nodes
    """

    def __init__(self):
        """Constructor
        """

        self.inputs = {}  # {Input name: Input}
        self._nodes = {}  # {Job name: Node}
        self._root_nodes = {}  # {Job name: Node}

    def add_dependency(self, parent_job_name, child_job_name, connections):
        """Adds a dependency that one job has upon another job

        :param parent_job_name: The name of the parent job
        :type parent_job_name: string
        :param child_job_name: The name of the child job
        :type child_job_name: string
        :param connections: List of tuples where first item is parent output name and second item is child input name
        :type connections: [(string, string)]
        """

        parent_node = self.get_node(parent_job_name)
        child_node = self.get_node(child_job_name)
        dependency_connections = []
        for connection in connections:
            output_name = connection[0]
            input_name = connection[1]
            dependency_connection = DependencyInputConnection(input_name, parent_node, output_name)
            dependency_connections.append(dependency_connection)

        child_node.add_dependency(parent_node, dependency_connections)
        parent_node.add_child(child_node)
        if child_job_name in self._root_nodes:
            del self._root_nodes[child_job_name]

    def add_input(self, recipe_input):
        """Adds a recipe input to this graph

        :param recipe_input: The recipe input
        :type recipe_input: :class:`job.handlers.inputs.base_input.Input`
        """

        self.inputs[recipe_input.input_name] = recipe_input

    def add_job(self, job_name, job_type_name, job_type_version):
        """Adds a new job node to the graph

        :param job_name: The unique name of the job
        :type job_name: string
        :param job_type_name: The name of the job's type
        :type job_type_name: string
        :param job_type_version: The version of the job's type
        :type job_type_version: string
        """

        if job_name in self._nodes:
            raise Exception('Recipe cannot have duplicate job names')

        node = RecipeNode(job_name, job_type_name, job_type_version)
        self._nodes[job_name] = node
        self._root_nodes[job_name] = node

    def add_recipe_input_connection(self, recipe_input, job_name, job_input):
        """Adds a recipe input connection from the given recipe input to the given job input

        :param recipe_input: The name of the recipe input
        :type recipe_input: string
        :param job_name: The name of the job
        :type job_name: string
        :param job_input: The name of the job input
        :type job_input: string
        """

        if recipe_input not in self.inputs:
            raise Exception('Recipe input %s is not defined' % recipe_input)

        if job_name not in self._nodes:
            raise Exception('Recipe job %s is not defined' % job_name)

        input_conn = RecipeInputConnection(job_input, self.inputs[recipe_input])
        self.get_node(job_name).add_recipe_input(input_conn)

    def get_node(self, job_name):
        """Returns the node with the given job_name

        :param job_name: The job name
        :type job_name: string
        :returns: The node
        :rtype: :class:`recipe.handlers.node.RecipeNode`
        """

        if job_name not in self._nodes:
            raise Exception('Recipe job %s is not defined' % job_name)
        return self._nodes[job_name]

    def get_topological_order(self):
        """Returns the recipe job names in a valid topological ordering (dependency order)

        :returns: The list of job names in topological ordering
        :rtype: [string]
        """

        results = []
        perm_set = set()
        temp_set = set()
        unmarked_set = set(self._nodes.keys())
        while unmarked_set:
            job_name = unmarked_set.pop()
            node = self._nodes[job_name]
            self._get_topological_order_visit(node, results, perm_set, temp_set)
            unmarked_set = set(self._nodes.keys()) - perm_set
        return results

    def _get_topological_order_visit(self, node, results, perm_set, temp_set):
        """Recursive depth-first search algorithm for determining a topological ordering of the recipe jobs

        :param node: The job dictionary
        :type node: :class:`recipe.handlers.node.RecipeNode`
        :param results: The list of job names in topological order
        :type results: list
        :param perm_set: A permanent set of visited nodes (job names)
        :type perm_set: set
        :param temp_set: A temporary set of visited nodes (job names)
        :type temp_set: set
        """

        if node.job_name in temp_set:
            raise Exception('Recipe has cyclic dependencies')

        if node.job_name not in perm_set:
            temp_set.add(node.job_name)
            for child_node in node.children:
                self._get_topological_order_visit(child_node, results, perm_set, temp_set)
            perm_set.add(node.job_name)
            temp_set.remove(node.job_name)
            results.insert(0, node.job_name)
