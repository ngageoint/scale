"""Defines the class for handling files inputs"""
from __future__ import unicode_literals

from job.handlers.inputs.base_input import Input


class FilesInput(Input):
    """Represents a multiple file input
    """

    def __init__(self, input_name):
        """Constructor

        :param input_name: The name of the input
        :type input_name: str
        """

        super(FilesInput, self).__init__(input_name, 'files')
