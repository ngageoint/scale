"""Defines the class for handling data"""
from __future__ import absolute_import
from __future__ import unicode_literals

from data.data.exceptions import InvalidData


class Data(object):
    """Represents a grouping of parameters with their provided data
    """

    def __init__(self):
        """Constructor
        """

        self.values = {}  # {Name: DataValue}

    def add_value(self, value):
        """Adds the data value

        :param value: The data value to add
        :type value: :class:`data.data.value.DataValue`

        :raises :class:`data.data.exceptions.InvalidData`: If the value is a duplicate
        """

        if value.name in self.values:
            raise InvalidData('DUPLICATE_VALUE', 'Duplicate value \'%s\'' % value.name)

        self.values[value.name] = value

    def add_value_from_output_data(self, input_name, output_name, output_data):
        """Adds an output value from the given output data to this data with the given input name. This is used to pass
        output data from a recipe node to the input data of another recipe node.

        :param input_name: The name of the input value to add
        :type input_name: string
        :param output_name: The name of the output value in the output data
        :type output_name: string
        :param output_data: The output data
        :type output_data: :class:`data.data.data.Data`

        :raises :class:`data.data.exceptions.InvalidData`: If the value is a duplicate
        """

        new_value = output_data.values[output_name].copy()
        new_value.name = input_name
        self.add_value(new_value)

    def validate(self, interface):
        """Validates this data against the given interface. Extra data values that cannot be passed to the interface
        will be removed.

        :param interface: The interface to which this data is being passed
        :type interface: :class:`data.interface.interface.Interface`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
        """

        warnings = []

        # Remove extra data values
        for data_value in self.values.values():
            if data_value.name not in interface.parameters:
                del self.values[data_value.name]

        # Check the data value being passed to each parameter
        for parameter in interface.parameters.values():
            if parameter.name in self.values:
                data_value = self.values[parameter.name]
                warnings.extend(data_value.validate(parameter))
            elif parameter.required:
                raise InvalidData('PARAM_REQUIRED', 'Parameter \'%s\' is required' % parameter.name)

        return warnings
