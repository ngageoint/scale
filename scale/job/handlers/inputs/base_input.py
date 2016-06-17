"""Defines the base class for handling inputs"""
from __future__ import unicode_literals

from abc import ABCMeta


class Input(object):
    """Abstract base class that represents an input
    """

    __metaclass__ = ABCMeta

    def __init__(self, input_name, input_type, required):
        """Constructor

        :param input_name: The name of the input
        :type input_name: str
        :param input_type: The type of the input
        :type input_type: str
        :param required: Whether the input is required
        :type required: bool
        """

        self.input_name = input_name
        self.input_type = input_type
        self.required = required
