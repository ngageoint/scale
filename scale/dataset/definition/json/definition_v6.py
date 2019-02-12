"""Manages the DataSet definition schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from data.interface.json.interface_v6 import INTERFACE_SCHEMA
from dataset.exceptions import InvalidDataSetDefinition, InvalidDataSetMemberDefinition, InvalidDataSetFileDefinition
from dataset.definition.definition import DataSetDefinition, DataSetMemberDefinition

SCHEMA_VERSION = '6'
DATASET_DEFINITION_SCHEMA = {
    'type': 'object',
    'required': ['version', 'parameters'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'The version of the dataset definition schema',
            'type': 'string',
        },
        'global_parameters': {
            'description': 'Each global parameter of the dataset. The names should be unique and not collide with any regular parameter names.',
            'type': 'array',
            'items': {
                'type': 'object',
                'description': 'A global dataset parameter',
                'required': ['name', 'input'],
                'additionalProperties': False,
                'properties': {
                    'name': {
                        'description': 'The name of the parameter',
                        'type': 'string',
                    },
                    'input': INTERFACE_SCHEMA,
                },
            },
        },
        'parameters': {
            'description': 'Name of the parameters of the dataset. A dataset will have n members of each parameter. The names should be unique and not collide with any global parameter names.',
            'type': 'array',
            'items': {
                    'type': 'string',
            },
        },
    },
}

DATASET_MEMBER_SCHEMA = {
    'type': 'object',
    'required': ['version', 'name', 'input'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'The version of the dataset member definition schema',
            'type': 'string',
        },
        'name': {
            'description': 'The name of the parameter this member matches',
            'type': 'string',
        },
        'input': INTERFACE_SCHEMA,
    },
}

def convert_definition_to_v6_json(definition):
    """Returns the v6 dataset definition JSON for the given definition

    :param definition: The dataset definition
    :type definition: :class:`??`
    :returns: The v6 dataset definition JSON
    :rtype: :class:`dataset.DataSetDefinition
    """

    def_dict = {
        'version': SCHEMA_VERSION,
        'global_parameters': definition['global_parameters'],
        'parameters': definition['parameters']
    }

    return DataSetDefinitionV6(definition=def_dict, do_validate=False)

def convert_member_definition_to_v6_json(definition):
    """
    Converts the the v6 dataset member definition JSON for the given definition

    :param definition: The dataset member definition
    :type definition: :class:`??`
    :returns: The v6 dataset member definition JSON
    :rtype: :class:`dataset.DataSetMemberDefinition
    """

    def_dict = {
        'version': SCHEMA_VERSION,
        'name': definition['name'],
        'input': definition['input']
    }

    return DataSetMemberDefinitionV6(definition=def_dict, do_validate=False).get_dict()

class DataSetDefinitionV6(object):
    """
    Represents the definition of a DataSet object

    :keyword definition: The dataset definition JSON dict
    :type definition: dict
    :keyword do_validate: Whether to perform validation on the JSON schema
    :type created_time: bool
    """
    def __init__(self, definition=None, do_validate=False):
        """Constructor
        """

        if not definition:
            definition = {}
        self._definition = definition

        if 'version' not in self._definition:
            self._definition['version'] = SCHEMA_VERSION

        self._populate_default_values()
        
        self._check_for_name_collisions()

        try:
            if do_validate:
                validate(self._definition, DATASET_DEFINITION_SCHEMA)
        except ValidationError as ex:
            raise InvalidDataSetDefinition('INVALID_DATASET_DEFINITION', 'Error validating against schema: %s' % unicode(ex))

    def get_definition(self):
        """Returns the definition

        :returns: The DataSetDefinition object
        :rtype: :class:`dataset.definition.definition.DataSetDefinition`
        """

        return DataSetDefinition(definition=self.get_dict())

    def get_dict(self):
        """Returns the dict of the definition
        """

        return self._definition

    def _populate_default_values(self):
        """Populates any missing JSON fields that have default values
        """

    def _check_for_name_collisions(self):
        """Ensures all global and regular parameter names are unique, and throws a
        :class:`data.dataset.exceptions.InvalidDataSetDefinition` if they are not unique.
        """

        names = []

        names.extend(self._definition['parameters'])
        
        names += [global_param['name'] for global_param in self._definition['global_parameters']

        if len(names) != len(set(names)):
            raise InvalidDataSetDefinition('NAME_COLLISION_ERROR','Parameter names must be unique.' )
                                                

class DataSetMemberDefinitionV6(object):
    """
    Represents the definition of a DataSet object

    :keyword definition: The definition of the data set member
    :type description: dict
    :keyword do_validate: Whether to perform validation on the JSON schema
    :type do_validate: bool
    """
    def __init__(self, definition=None, do_validate=False):
        """Constructor
        """

        if not definition:
            definition = {}
        self._definition = definition

        if 'version' not in self._definition:
            self._definition['version'] = SCHEMA_VERSION

        self._populate_default_values()

        try:
            if do_validate:
                validate(definition, DATASET_MEMBER_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidDataSetMemberDefinition('JSON_VALIDATION_ERROR', 'Error validating against schema: %s' % validation_error)

    def get_dict(self):
        """Returns the dict of the definition
        """

        return self._definition

    def get_member_definition(self):
        """Returns the DataSetMemberDefinitio"""

        return DataSetMemberDefinition(definition=self.get_dict())

    def _populate_default_values(self):
        """Populates any missing required valudes with defaults
        """
