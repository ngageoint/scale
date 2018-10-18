"""Manages the v6 data filter schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from data.filter.filter import DataFilter
from data.filter.exceptions import InvalidDataFilter


SCHEMA_VERSION = '6'


# TODO: design and implement
DATA_FILTER_SCHEMA = {
    'type': 'object',
    'required': [],
    'additionalProperties': False,
    'properties': {
    },
}


# TODO: implement
def convert_filter_to_v6_json(data_filter):
    """Returns the v6 data filter JSON for the given data filter

    :param data_filter: The data
    :type data_filter: :class:`data.filter.filter.DataFilter`
    :returns: The v6 data filter JSON
    :rtype: :class:`data.filter.json.filter_v6.DataFilterV6`
    """

    filter_dict = {'version': SCHEMA_VERSION}

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
            data_filter = {}
        self._data_filter = data_filter

        if 'version' not in self._data_filter:
            self._data_filter['version'] = SCHEMA_VERSION

        try:
            if do_validate:
                validate(self._data_filter, DATA_FILTER_SCHEMA)
        except ValidationError as ex:
            raise InvalidDataFilter('INVALID_DATA_FILTER', 'Invalid data filter: %s' % unicode(ex))

    # TODO: implement
    def get_filter(self):
        """Returns the data filter represented by this JSON

        :returns: The data filter
        :rtype: :class:`data.filter.filter.DataFilter`:
        """

        data_filter = DataFilter(True)

        return data_filter

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._data_filter
