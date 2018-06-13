"""Manages the v6 interface schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from data.interface.exceptions import InvalidInterface
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter


SCHEMA_VERSION = '6'


INTERFACE_SCHEMA = {
    'type': 'object',
    'required': ['files', 'json'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the interface schema',
            'type': 'string',
        },
        'files': {
            'description': 'The file-based inputs for this interface',
            'type': 'array',
            'items': {
                'description': 'A file input',
                'type': 'object',
                'required': ['name', 'media_types', 'required', 'multiple'],
                'additionalProperties': False,
                'properties': {
                    'name': {
                        'description': 'The unique name of the input',
                        'type': 'string',
                        'pattern': '^[a-zA-Z_-]+$',
                    },
                    'media_types': {
                        'description': 'The list of acceptable media types',
                        'type': 'array',
                        'items': {
                            'type': 'string',
                        },
                    },
                    'multiple': {
                        'description': 'Whether this input contains multiple files',
                        'type': 'boolean',
                    },
                    'required': {
                        'description': 'Whether this input is required',
                        'type': 'boolean',
                    },
                },
            },
        },
        'json': {
            'description': 'The JSON inputs for this interface',
            'type': 'array',
            'items': {
                'description': 'A JSON input',
                'type': 'object',
                'required': ['name', 'type', 'required'],
                'additionalProperties': False,
                'properties': {
                    'name': {
                        'description': 'The unique name of the input',
                        'type': 'string',
                        'pattern': '^[a-zA-Z_-]+$',
                    },
                    'type': {
                        'description': 'The JSON type accepted',
                        'enum': ['array', 'boolean', 'integer', 'number', 'object', 'string']
                    },
                    'required': {
                        'description': 'Whether this input is required',
                        'type': 'boolean',
                    },
                },
            },
        },
    },
}


def convert_interface_to_v6_json(interface):
    """Returns the v6 interface JSON for the given interface

    :param interface: The interface
    :type interface: :class:`data.interface.interface.Interface`
    :returns: The v6 interface JSON
    :rtype: :class:`data.interface.json.interface_v6.InterfaceV6`
    """

    files = []
    json = []

    for parameter in interface.parameters.values():
        if isinstance(parameter, FileParameter):
            file_dict = {'name': parameter.name, 'media_types': parameter.media_types, 'required': parameter.required,
                         'multiple': parameter.multiple}
            files.append(file_dict)
        elif isinstance(parameter, JsonParameter):
            json_dict = {'name': parameter.name, 'type': parameter.json_type, 'required': parameter.required}
            json.append(json_dict)

    interface_dict = {'version': '6', 'files': files, 'json': json}

    return InterfaceV6(interface=interface_dict, do_validate=False)


class InterfaceV6(object):
    """Represents a v6 interface JSON"""

    def __init__(self, interface=None, do_validate=False):
        """Creates a v6 interface JSON object from the given dictionary

        :param interface: The interface JSON dict
        :type interface: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`data.interface.exceptions.InvalidInterface`: If the given interface is invalid
        """

        if not interface:
            interface = {}
        self._interface = interface

        if 'version' not in self._interface:
            self._interface['version'] = SCHEMA_VERSION

        if self._interface['version'] != SCHEMA_VERSION:
            msg = '%s is an unsupported version number'
            raise InvalidInterface('INVALID_VERSION', msg % self._interface['version'])

        self._populate_default_values()

        try:
            if do_validate:
                validate(self._interface, INTERFACE_SCHEMA)
        except ValidationError as ex:
            raise InvalidInterface('INVALID_INTERFACE', 'Invalid interface: %s' % unicode(ex))

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._interface

    def get_interface(self):
        """Returns the interface represented by this JSON

        :returns: The interface
        :rtype: :class:`data.interface.interface.Interface`:
        """

        interface = Interface()

        for file_dict in self._interface['files']:
            file_param = FileParameter(file_dict['name'], file_dict['media_types'], file_dict['required'],
                                       file_dict['multiple'])
            interface.add_parameter(file_param)
        for json_dict in self._interface['json']:
            json_param = JsonParameter(json_dict['name'], json_dict['type'], json_dict['required'])
            interface.add_parameter(json_param)

        return interface

    def _populate_default_values(self):
        """Populates any missing required values with defaults
        """

        if 'files' not in self._interface:
            self._interface['files'] = []
        for file_dict in self._interface['files']:
            if 'media_types' not in file_dict:
                file_dict['media_types'] = []
            if 'multiple' not in file_dict:
                file_dict['multiple'] = False
            if 'required' not in file_dict:
                file_dict['required'] = True

        if 'json' not in self._interface:
            self._interface['json'] = []
        for json_dict in self._interface['json']:
            if 'required' not in json_dict:
                json_dict['required'] = True
