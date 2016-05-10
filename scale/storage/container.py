"""Defines the methods for handling file systems in the container's local volume"""
from __future__ import unicode_literals

import os


SCALE_ROOT_PATH = '/scale'
SCALE_ROOT_WORKSPACE_MOUNT_PATH = os.path.join(SCALE_ROOT_PATH, 'workspace_mounts')


def get_workspace_mount_path(name):
    """Returns the absolute local path within the container for the remote mount for the workspace with the given name

    :param name: The name of the workspace
    :type name: string
    :returns: The absolute local path of the workspace's mount
    :rtype: string
    """

    return os.path.join(SCALE_ROOT_WORKSPACE_MOUNT_PATH, name)
