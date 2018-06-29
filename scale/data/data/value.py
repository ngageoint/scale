"""Defines the classes for handling a data value being passed to an interface"""
from __future__ import absolute_import
from __future__ import unicode_literals

from abc import ABCMeta
from copy import copy
from numbers import Number

from data.data.exceptions import InvalidData
from data.interface.parameter import FileParameter, JsonParameter


class DataValue(object):
    """Represents a data value for an interface parameter
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

    def copy(self):
        """Returns a copy of this value

        :returns: A copy of this value
        :rtype: :class:`data.data.value.DataValue`
        """

        return copy(self)

    def validate(self, parameter):
        """Validates this data value against its parameter

        :param parameter: The parameter to which this data is being passed
        :type parameter: :class:`data.interface.parameter.Parameter`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
        """

        if self.param_type != parameter.param_type:
            msg = 'Parameter \'%s\' of type \'%s\' cannot accept data of type \'%s\''
            msg = msg % (parameter.name, parameter.param_type, self.param_type)
            raise InvalidData('MISMATCHED_PARAM_TYPE', msg)

        return []


class FileValue(DataValue):
    """Represents a data value containing one or more files
    """

    def __init__(self, name, file_ids):
        """Constructor

        :param name: The name of the parameter
        :type name: string
        :param file_ids: The list of file IDs
        :type file_ids: list
        """

        super(FileValue, self).__init__(name, FileParameter.PARAM_TYPE)

        self.file_ids = file_ids

    def validate(self, parameter):
        """See :meth:`data.data.value.DataValue.validate`
        """

        warnings = super(FileValue, self).validate(parameter)

        if len(self.file_ids) == 0:
            raise InvalidData('NO_FILES', 'Parameter \'%s\' cannot accept zero files' % parameter.name)

        if len(self.file_ids) > 1 and not parameter.multiple:
            raise InvalidData('MULTIPLE_FILES', 'Parameter \'%s\' cannot accept multiple files' % parameter.name)

        return warnings


class JsonValue(DataValue):
    """Represents a JSON data value
    """

    def __init__(self, name, value):
        """Constructor

        :param name: The name of the parameter
        :type name: string
        :param value: The JSON value
        """

        super(JsonValue, self).__init__(name, JsonParameter.PARAM_TYPE)

        self.value = value

    def validate(self, parameter):
        """See :meth:`data.data.value.DataValue.validate`
        """

        warnings = super(JsonValue, self).validate(parameter)

        if parameter.json_type == 'array' and not isinstance(self.value, list):
            raise InvalidData('INVALID_JSON_TYPE', 'Parameter \'%s\' must receive an array' % parameter.name)
        elif parameter.json_type == 'boolean' and not isinstance(self.value, bool):
            raise InvalidData('INVALID_JSON_TYPE', 'Parameter \'%s\' must receive a boolean' % parameter.name)
        elif parameter.json_type == 'integer' and not isinstance(self.value, (int, long)):
            raise InvalidData('INVALID_JSON_TYPE', 'Parameter \'%s\' must receive an integer' % parameter.name)
        elif parameter.json_type == 'number' and not isinstance(self.value, Number):
            raise InvalidData('INVALID_JSON_TYPE', 'Parameter \'%s\' must receive a number' % parameter.name)
        elif parameter.json_type == 'object' and not isinstance(self.value, dict):
            raise InvalidData('INVALID_JSON_TYPE', 'Parameter \'%s\' must receive a JSON object' % parameter.name)
        elif parameter.json_type == 'string' and not isinstance(self.value, basestring):
            raise InvalidData('INVALID_JSON_TYPE', 'Parameter \'%s\' must receive a string' % parameter.name)

        return warnings
