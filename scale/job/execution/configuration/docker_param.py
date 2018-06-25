"""Defines a Docker parameter that is set for a task"""
from __future__ import unicode_literals


class DockerParameter(object):
    """Represents a Docker parameter set for a task
    """

    def __init__(self, flag, value):
        """Creates a Docker parameter

        :param flag: The Docker flag of the parameter
        :type flag: string
        :param value: The value being passed to the Docker parameter
        :type value: string
        """

        self.flag = flag
        self.value = value
