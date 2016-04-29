"""Defines the exceptions related to files and storage methods"""
from __future__ import unicode_literals


class ArchivedWorkspace(Exception):
    """Exception indicating an attempt was made to store or retrieve a file with an archived (no longer active)
    workspace
    """

    pass


class DeletedFile(Exception):
    """Exception indicating an attempt was made to retrieve a deleted file
    """

    pass


class DuplicateFile(Exception):
    """Exception indicating an attempt was made to store a file with a duplicate name
    """

    pass


class InvalidDataTypeTag(Exception):
    """Exception indicating an attempt to add an invalid data type tag to a file
    """

    pass


class MissingRemoteMount(Exception):
    """Exception indicating that a workspace required a remote file system mount in order to perform an operation and
    the required mount was missing
    """

    pass


class NfsError(Exception):
    """Exception indicating that an error occurred with NFS (Network File System)
    """

    pass
