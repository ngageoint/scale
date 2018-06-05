"""Manages the v6 data schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from data.data.data import Data
from data.data.exceptions import InvalidData
from data.data.value import FileValue, JsonValue


SCHEMA_VERSION = '6'


DATA_SCHEMA = {
    'type': 'object',
    'required': ['files', 'json'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the data schema',
            'type': 'string',
        },
        'files': {
            'description': 'The file values (lists of file IDs) in this data',
            'type': 'object',
            'additionalProperties': {
                'type': 'array',
                'minItems': 1,
                'items': {
                    'type': 'integer',
                },
            },
        },
        'json': {
            'description': 'The JSON values in this data',
            'type': 'object',
            'additionalProperties': True,
        },
    },
}


def convert_data_to_v6_json(data):
    """Returns the v6 data JSON for the given interface

    :param data: The data
    :type data: :class:`data.data.data.Data`
    :returns: The v6 data JSON
    :rtype: :class:`data.data.json.data_v6.DataV6`
    """

    files = {}
    json = {}

    for value in data.values.values():
        if isinstance(value, FileValue):
            files[value.name] = value.file_ids
        elif isinstance(value, JsonValue):
            json[value.name] = value.value

    data_dict = {'version': '6', 'files': files, 'json': json}

    return DataV6(data=data_dict, do_validate=False)


class DataV6(object):
    """Represents a v6 data JSON"""

    def __init__(self, data=None, do_validate=False):
        """Creates a v6 data JSON object from the given dictionary

        :param data: The data JSON dict
        :type data: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`data.data.exceptions.InvalidData`: If the given data is invalid
        """

        if not data:
            data = {}
        self._data = data

        if 'version' not in self._data:
            self._data['version'] = SCHEMA_VERSION

        if self._data['version'] != SCHEMA_VERSION:
            raise InvalidData('INVALID_VERSION', '%s is an unsupported version number' % self._data['version'])

        self._populate_default_values()

        try:
            if do_validate:
                validate(self._data, DATA_SCHEMA)
        except ValidationError as ex:
            raise InvalidData('INVALID_DATA', 'Invalid interface: %s' % unicode(ex))

    def get_data(self):
        """Returns the data represented by this JSON

        :returns: The data
        :rtype: :class:`data.data.data.Data`:
        """

        data = Data()

        for name, file_ids in self._data['files'].items():
            file_value = FileValue(name, file_ids)
            data.add_value(file_value)
        for name, json in self._data['json'].items():
            json_value = JsonValue(name, json)
            data.add_value(json_value)

        return data

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._data

    def _populate_default_values(self):
        """Populates any missing required values with defaults
        """

        if 'files' not in self._data:
            self._data['files'] = {}
        if 'json' not in self._data:
            self._data['json'] = {}
