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
