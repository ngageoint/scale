"""Defines the exceptions related to files and storage methods"""
from __future__ import unicode_literals

from error.exceptions import ScaleError


class ArchivedWorkspace(Exception):
    """Exception indicating an attempt was made to store or retrieve a file with an archived (no longer active)
    workspace
    """

    pass


class DeletedFile(ScaleError):
    """Error class indicating an attempt was made to retrieve a deleted file (a file whose is_deleted flag is true in
    the database)
    """

    def __init__(self, file_name):
        """Constructor

        :param file_name: The name of deleted file
        :type file_name: string
        """

        super(DeletedFile, self).__init__(8, 'deleted-file')
        self.file_name = file_name

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return '%s has been deleted. The job cannot run without the file.' % self.file_name


class InvalidDataTypeTag(Exception):
    """Exception indicating an attempt to add an invalid data type tag to a file
    """

    pass


class MissingFile(ScaleError):
    """Error class indicating an attempt was made to retrieve a missing file
    """

    def __init__(self, file_name):
        """Constructor

        :param file_name: The name of missing file
        :type file_name: string
        """

        super(MissingFile, self).__init__(9, 'missing-file')
        self.file_name = file_name

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        msg = '%s is missing from its expected workspace location. The job cannot run without the file.'
        return msg % self.file_name


class MissingVolumeMount(Exception):
    """Exception indicating that a workspace required a volume file system mount in order to perform an operation and
    the required volume mount was missing
    """

    pass
