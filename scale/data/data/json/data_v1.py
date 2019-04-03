"""Defines the data needed for executing a recipe"""
from __future__ import unicode_literals

from data.data.exceptions import InvalidData
from data.data.value import FileValue, JsonValue
from data.interface.interface import Interface


DEFAULT_VERSION = '1.0'


def convert_data_to_v1_json(data, interface):
    """Returns the v1 data JSON for the given data

    :param data: The data
    :type data: :class:`data.data.data.Data`
    :param interface: Interface to determine if we want to specify a single file directory or a single file
    :type interface: :class:`data.interface.interface.Interface`
    :returns: The v1 data JSON
    :rtype: :class:`data.data.json.data_v1.DataV1`
    """

    input_data = []

    for value in data.values.values():
        if isinstance(value, FileValue):
            multiple = False
            if interface and value.name in interface.parameters:
                multiple = interface.parameters[value.name].multiple
            if len(value.file_ids) > 1 or multiple:
                input_data.append({'name': value.name, 'file_ids': value.file_ids})
            elif len(value.file_ids) == 1:
                input_data.append({'name': value.name, 'file_id': value.file_ids[0]})
        elif isinstance(value, JsonValue):
            input_data.append({'name': value.name, 'value': value.value})

    data_dict = {'version': DEFAULT_VERSION, 'input_data': input_data}

    return DataV1(data=data_dict)

class DataV1(object):
    """Represents a v1 data JSON"""

    def __init__(self, data=None):
        """Creates a recipe data object from the given dictionary

        :param data: The data JSON dict
        :type data: dict

        :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
        """

        if not data:
            data = {}
        self.data_dict = data
        param_names = set()

        if 'version' not in self.data_dict:
            self.data_dict['version'] = DEFAULT_VERSION
        if not self.data_dict['version'] == '1.0':
            msg = 'Invalid data: %s is an unsupported version number'
            raise InvalidData('INVALID_VERSION', msg % self.data_dict['version'])

        # Be able to handle v1 job results (convert it into v1 job data)
        if 'output_data' in self.data_dict and 'input_data' not in self.data_dict:
            the_data_dict = self.data_dict['output_data']
            self.data_dict['input_data'] = the_data_dict
            del self.data_dict['output_data']

        if 'input_data' not in self.data_dict:
            self.data_dict['input_data'] = []
        for data_input in self.data_dict['input_data']:
            if not 'name' in data_input:
                raise InvalidData('INVALID_DATA', 'Invalid data: Every data input must have a "name" field')
            name = data_input['name']
            if name in param_names:
                raise InvalidData('INVALID_DATA', 'Invalid data: %s cannot be defined more than once' % name)
            else:
                param_names.add(name)

    def get_dict(self):
        """Returns the internal dictionary that represents this recipe data

        :returns: The internal dictionary
        :rtype: dict
        """

        return self.data_dict
