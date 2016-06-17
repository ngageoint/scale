"""Defines the class for handling property inputs"""
from __future__ import unicode_literals

from job.handlers.inputs.base_input import Input


class PropertyInput(Input):
    """Represents a property input
    """

    def __init__(self, input_name, required):
        """Constructor

        :param input_name: The name of the input
        :type input_name: str
        :param required: Whether the input is required
        :type required: bool
        """

        super(PropertyInput, self).__init__(input_name, 'property', required)
