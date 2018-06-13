"""Defines the classes for handling a data parameter for an interface"""
from __future__ import unicode_literals

from abc import ABCMeta
from copy import copy

from data.interface.exceptions import InvalidInterface, InvalidInterfaceConnection
from util.validation import ValidationWarning


class Parameter(object):
    """Represents an interface parameter
    """

    __metaclass__ = ABCMeta

    def __init__(self, name, param_type, required=True):
        """Constructor

        :param name: The name of the parameter
        :type name: string
        :param param_type: The type of the parameter
        :type param_type: string
        :param required: Whether this parameter is required
        :type required: bool
        """

        self.name = name
        self.param_type = param_type
        self.required = required

    def copy(self):
        """Returns a copy of this parameter

        :returns: A copy of this parameter
        :rtype: :class:`data.interface.parameter.Parameter`
        """

        return copy(self)

    def validate(self):
        """Validates this parameter

        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.interface.exceptions.InvalidInterface`: If the interface is invalid
        """

        return []

    def validate_connection(self, connecting_parameter):
        """Validates that the given connecting parameter can be accepted by this parameter

        :param connecting_parameter: The parameter attempting to connect to this parameter
        :type connecting_parameter: :class:`data.interface.parameter.Parameter`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`data.interface.exceptions.InvalidInterfaceConnection`: If the interface connection is invalid
        """

        if self.param_type != connecting_parameter.param_type:
            msg = 'Parameter \'%s\' of type \'%s\' cannot accept type \'%s\''
            msg = msg % (self.name, self.param_type, connecting_parameter.param_type)
            raise InvalidInterfaceConnection('MISMATCHED_PARAM_TYPE', msg)

        if self.required and not connecting_parameter.required:
            msg = 'Parameter \'%s\' is required and cannot accept an optional value' % self.name
            raise InvalidInterfaceConnection('PARAM_REQUIRED', msg)

        return []


class FileParameter(Parameter):
    """Represents a file(s) parameter
    """

    PARAM_TYPE = 'file'

    def __init__(self, name, media_types, required=True, multiple=False):
        """Constructor

        :param name: The name of the parameter
        :type name: string
        :param media_types: The list of valid file media types
        :type media_types: list
        :param required: Whether this parameter is required
        :type required: bool
        :param multiple: Whether this parameter accepts multiple files
        :type multiple: bool
        """

        super(FileParameter, self).__init__(name, FileParameter.PARAM_TYPE, required=required)

        self.media_types = media_types
        self.multiple = multiple

    def validate_connection(self, connecting_parameter):
        """See :meth:`data.interface.parameter.Parameter.validate_connection`
        """

        warnings = super(FileParameter, self).validate_connection(connecting_parameter)

        if not self.multiple and connecting_parameter.multiple:
            msg = 'Parameter \'%s\' cannot accept multiple files' % self.name
            raise InvalidInterfaceConnection('NO_MULTIPLE_FILES', msg)

        mismatched_media_types = []
        for media_type in connecting_parameter.media_types:
            if media_type not in self.media_types:
                mismatched_media_types.append(media_type)
        if mismatched_media_types:
            msg = 'Parameter \'%s\' might not accept [%s]' % (self.name, ', '.join(mismatched_media_types))
            warnings.append(ValidationWarning('MISMATCHED_MEDIA_TYPES', msg))

        return warnings


class JsonParameter(Parameter):
    """Represents a JSON parameter
    """

    PARAM_TYPE = 'json'
    VALID_JSON_TYPES = ['array', 'boolean', 'integer', 'number', 'object', 'string']

    def __init__(self, name, json_type, required=True):
        """Constructor

        :param name: The name of the parameter
        :type name: string
        :param json_type: The JSON type
        :type json_type: string
        :param required: Whether this parameter is required
        :type required: bool
        """

        super(JsonParameter, self).__init__(name, JsonParameter.PARAM_TYPE, required=required)

        self.json_type = json_type

    def validate(self):
        """See :meth:`data.interface.parameter.Parameter.validate`
        """

        if self.json_type not in JsonParameter.VALID_JSON_TYPES:
            msg = 'Parameter \'%s\' has invalid JSON type \'%s\'' % (self.name, self.json_type)
            raise InvalidInterface('INVALID_JSON_TYPE', msg)

        return []

    def validate_connection(self, connecting_parameter):
        """See :meth:`data.interface.parameter.Parameter.validate_connection`
        """

        warnings = super(JsonParameter, self).validate_connection(connecting_parameter)

        if self.json_type != connecting_parameter.json_type:
            msg = 'Parameter \'%s\' of JSON type \'%s\' cannot accept JSON type \'%s\''
            msg = msg % (self.name, self.json_type, connecting_parameter.json_type)
            raise InvalidInterfaceConnection('MISMATCHED_JSON_TYPE', msg)

        return warnings
