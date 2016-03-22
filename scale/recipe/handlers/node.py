"""Defines the class for handling recipe nodes"""
from __future__ import unicode_literals


class RecipeNode(object):
    """Represents a node in a recipe
    """

    def __init__(self, job_name, job_type_name, job_type_version):
        """Constructor

        :param job_name: The recipe definition
        :type job_name: str

        :raises InvalidDefinition: If the given definition is invalid
        """

        self._definition = definition
