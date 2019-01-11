"""Defines the class that represents a dataset"""
from __future__ import unicode_literals

class DataSetDefinition(object):
    """Represents the dataset definition
    """

    def __init__(self, definition, do_validate=True):
        """Constructor

        :param definition: dict definition
        :type definition: dict
        """
        self._definition = definition

    def get_dict(self):
        """Returns the internal dictionary that represents this datasets definition

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition
