"""Defines the class for handling a data interface"""
from __future__ import unicode_literals


class Interface(object):
    """Represents a grouping of parameters
    """

    def __init__(self):
        """Constructor
        """

        pass

    # TODO: a general validate method for just this interface

    # TODO: a method to validate another interface being passed to this one (connection)

    # TODO: a method to validate data being passed to this one (ensure valid data)
    # - return warnings for "extra" arguments provided
