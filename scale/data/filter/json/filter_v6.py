"""Manages the v6 data filter schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from data.filter.filter import DataFilter
from data.filter.exceptions import InvalidDataFilter


SCHEMA_VERSION = '6'


DATA_FILTER_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the data filter schema',
            'type': 'string',
        },
        'filters': {
            'description': 'Defines filters to run on data parameters',
            'type': 'array',
            'minItems': 0,
            'items': {
                'type': 'object',
                'description': 'A configuration for a data filter',
                'required': ['name', 'type', 'condition', 'values'],
                'additionalProperties': False,
                'properties': {
                    'name': {
                        'description': 'The name of the parameter this filter runs against. Multiple filters can run on the same parameter.',
                        'type': 'string',
                    },
                    'type': {
                        'description': 'Type of parameter this filter runs against.',
                        'enum': ['array', 'boolean', 'integer', 'number', 'object', 'string', 'filename', 'media-type', 'data-type', 'meta-data'],
                    },
                    'condition': {
                        'description': 'Condition to test data value against.',
                        'enum': ['<', '<=', '>','>=', '==', '!=', 'between', 'in', 'not in', 'contains', 'subset of', 'superset of'],
                    },
                    'values': {
                        'description': 'List of values to compare data against. May be any type.',
                        'type': 'array',
                        'minItems': 1,
                    },
                    'fields': {
                        'description': 'List of key paths to fields with each path being a list of keys in an object or file meta-data',
                        'type': 'array',
                        'minItems': 1,
                        'items': {
                            'type': 'array',
                            'minItems': 1,
                            'items': {
                                'type': 'string',
                            },
                        },
                    },
                    'all_fields': {
                        'description': 'Specifies whether all fields need to pass for filter to pass. Defaults to True.',
                        'type': 'boolean',
                    },
                    'all_files': {
                        'description': 'Specifies whether all files need to pass for filter to pass. Defaults to False.',
                        'type': 'boolean',
                    },
                },
            },
        },
        'all': {
            'description': 'Specifies whether all filters must pass. Defaults to True.',
            'type': 'boolean',
        },
    },
}


def convert_filter_to_v6_json(data_filter):
    """Returns the v6 data filter JSON for the given data filter

    :param data_filter: The data
    :type data_filter: :class:`data.filter.filter.DataFilter`
    :returns: The v6 data filter JSON
    :rtype: :class:`data.filter.json.filter_v6.DataFilterV6`
    """

    filter_dict = {'version': SCHEMA_VERSION}

    filter_dict['filters'] = data_filter.filter_list
    filter_dict['all'] = data_filter.all

    return DataFilterV6(data_filter=filter_dict, do_validate=False)


class DataFilterV6(object):
    """Represents a v6 data filter JSON"""

    def __init__(self, data_filter=None, do_validate=False):
        """Creates a v6 data filter JSON object from the given dictionary

        :param data_filter: The data filter JSON dict
        :type data_filter: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`data.filter.exceptions.InvalidDataFilter`: If the given data filter is invalid
        """

        if not data_filter:
            data_filter = {'filters': [], 'all': True}
        self._data_filter = data_filter

        if 'version' not in self._data_filter:
            self._data_filter['version'] = SCHEMA_VERSION
            
        if self._data_filter['version'] != SCHEMA_VERSION:
            msg = '%s is an unsupported version number'
            raise InvalidDataFilter('INVALID_VERSION', msg % self._data_filter['version'])

        if 'all' not in self._data_filter:
            self._data_filter['all'] = True
            
        if 'filters' not in self._data_filter:
            self._data_filter['filters'] = []
            
        try:
            if do_validate:
                validate(self._data_filter, DATA_FILTER_SCHEMA)
                for f in data_filter['filters']:
                    DataFilter.validate_filter(f)
        except ValidationError as ex:
            raise InvalidDataFilter('INVALID_DATA_FILTER', 'Invalid data filter: %s' % unicode(ex))

    def get_filter(self):
        """Returns the data filter represented by this JSON

        :returns: The data filter
        :rtype: :class:`data.filter.filter.DataFilter`:
        """

        data_filter = DataFilter([], self._data_filter['all'])

        for f in self._data_filter['filters']:
            data_filter.add_filter(f)

        return data_filter

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._data_filter
