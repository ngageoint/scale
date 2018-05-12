"""Defines the classes for handling a data parameter for an interface"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod


# TODO: implement parameter subclasses
class Parameter(object):
    """Represents an interface parameter
    """

    __metaclass__ = ABCMeta

    def __init__(self, name, param_type):
        """Constructor

        :param name: The name of the parameter
        :type name: string
        :param param_type: The type of the parameter
        :type param_type: string
        """

        self.name = name
        self.param_type = param_type

    @abstractmethod
    def copy(self):
        """Returns a copy of this parameter

        :returns: A copy of this parameter
        :rtype: :class:`data.interface.parameter.Parameter`
        """

        raise NotImplementedError()
