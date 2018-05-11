"""Defines the classes for representing nodes within a recipe definition"""
from __future__ import unicode_literals


class Node(object):
    """Represents a node within a recipe definition
    """

    def __init__(self, name):
        """Constructor

        :param name: The unique name of the node in the recipe graph
        :type name: string
        """

        self.name = name
        self.parents = {}  # {Name: Node}
        self.children = {}  # {Name: Node}

    # TODO: implement - will receive input interfaces in dict stored by node name
    def validate(self):
        """Validates this recipe definition

        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If the definition is invalid
        """

        return []


class JobNode(object):
    """Represents a job within a recipe definition
    """

    def __init__(self, name, job_type_name, job_type_version, revision_num):
        """Constructor

        :param name: The unique name of the node in the recipe graph
        :type name: string
        :param job_type_name: The name of the job type
        :type job_type_name: string
        :param job_type_version: The version of the job type
        :type job_type_version: string
        :param revision_num: The revision number of the job type
        :type revision_num: int
        """

        super(JobNode, self).__init__(name)

        self.job_type_name = job_type_name
        self.job_type_version = job_type_version
        self.revision_num = revision_num


class RecipeNode(object):
    """Represents a recipe within a recipe definition
    """

    def __init__(self, name, recipe_type_name, revision_num):
        """Constructor

        :param name: The unique name of the node in the recipe graph
        :type name: string
        :param recipe_type_name: The name of the recipe type
        :type recipe_type_name: string
        :param revision_num: The revision number of the recipe type
        :type revision_num: int
        """

        super(RecipeNode, self).__init__(name)

        self.recipe_type_name = recipe_type_name
        self.revision_num = revision_num
