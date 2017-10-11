"""Defines an input file and its meta-data in an execution configuration"""
from __future__ import unicode_literals


class InputFile(object):
    """Defines an input file and its meta-data
    """

    def __init__(self, scale_file):
        """Creates an input file from a scale_file model

        :param scale_file: The scale_file model with its related workspace field populated
        :type scale_file: :class:`storage.models.ScaleFile`
        """

        self.id = scale_file.id
        self.file_type = scale_file.file_type
        self.workspace_name = scale_file.workspace.name
        self.workspace_path = scale_file.file_path
        self.is_deleted = scale_file.is_deleted
        self.local_file_name = None
