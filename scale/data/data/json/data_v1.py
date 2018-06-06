"""Defines the data needed for executing a recipe"""
from __future__ import unicode_literals

from data.data.exceptions import InvalidData


DEFAULT_VERSION = '1.0'


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
            msg = 'Invalid recipe data: %s is an unsupported version number'
            raise InvalidData('INVALID_VERSION', msg % self.data_dict['version'])

        if 'input_data' not in self.data_dict:
            self.data_dict['input_data'] = []
        for data_input in self.data_dict['input_data']:
            if not 'name' in data_input:
                raise InvalidData('INVALID_DATA', 'Invalid recipe data: Every data input must have a "name" field')
            name = data_input['name']
            if name in param_names:
                raise InvalidData('INVALID_DATA', 'Invalid recipe data: %s cannot be defined more than once' % name)
            else:
                param_names.add(name)

    def get_dict(self):
        """Returns the internal dictionary that represents this recipe data

        :returns: The internal dictionary
        :rtype: dict
        """

        return self.data_dict
