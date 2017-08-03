"""Defines a workspace that is needed by a task"""
from __future__ import unicode_literals


class Workspace(object):
    """Represents a workspace needed by a task
    """

    def __init__(self, name, mode, volume_name=None):
        """Creates a task workspace

        :param name: The name of the workspace
        :type name: string
        :param mode: The mode to use for the workspace, either 'ro' or 'rw'
        :type mode: string
        :param volume_name: The name to use for the workspace's volume
        :type volume_name: string
        """

        self.name = name
        self.mode = mode
        self.volume_name = volume_name
