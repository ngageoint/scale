"""Manages the DataSet definition schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError


from data.interface.json.interface_v6 import INTERFACE_SCHEMA
from dataset.exceptions import InvalidDataSetDefinition, InvalidDataSetMemberDefinition, InvalidDataSetFileDefinition
from dataset.definition.definition import DataSetDefinition

FILTER_DEFINITION = {}

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
        'parameters': {
            'description': 'Each parameter of the dataset',
            'type': 'object',
            'additionalProperties': {
                '$ref': '#/definitions/parameter',
            },
        },
    },
    'definitions': {
        'parameter': {
          'description': 'A parameter of a dataset',
          'type': 'object',
          'required': ['param_type'],
          'additionalProperties': False,
          'properties': {
              'name': {
                'description': 'The name of the parameter',
                'type': 'string',
              },
              'param_type': {
                  'description': 'The type of parameter',
                  'oneOf':[
                      {'$ref': '#/definitions/global_parameter'},
                      {'$ref': '#/definitions/member_parameter'},
                  ],
              },
          },
        },
        'global_parameter': {
            'description': 'A global (not tied to individual members) parameter of a dataset.',
            'type': 'object',
            'required': ['param_type'],
            'additionalProperties': False,
            'properties': {
                'param_type': {
                    'description': 'The type of parameter',
                    'enum': ['global'],
                },
                # 'input': INTERFACE_SCHEMA,
            },
        },
        'member_parameter': {
            'description': 'A member (defined by a dataset_member) parameter of a dataset',
            'type': 'object',
            'required': ['param_type'],
            'additionalProperties': False,
            'properties': {
                'param_type': {
                    'description': 'The type of parameter',
                    'enum': ['member'],
                },
                # 'input': INTERFACE_SCHEMA,
            },
        },
    },
}

DATASET_MEMBER_SCHEMA = {
    'type': 'object',
    'required': ['version', 'param_name', 'filter'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'The version of the dataset member definition schema',
            'type': 'string',
        },
        'param_name': {
            'description': 'The name of the parameter this member matches',
            'type': 'string',
        },
        'filter': FILTER_DEFINITION,
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
        'param_name': definition['param_name'],
        'filter': definition['filter']
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

        try:
            if do_validate:
                validate(self._definition, DATASET_DEFINITION_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidDataSetDefinition('INVALID_DATASET_DEFINITION', 'Error validating against schema: %s' % validation_error)

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

    def _populate_default_values(self):
        """Populates any missing required valudes with defaults
        """

class DataSetFileDefinitionV6(object):
    """
    Represents the definition of a DataSetFile object

    """
    def __init__(self, definition=None, do_validate=True):
        """Constructor
        """

        if not definition:
            definition = {}
        self._definition = definition

        if 'version' not in self._definition:
            self._definition['version'] = SCHEMA_VERSION

        self._populate_default_values()

        # try:
        #     if do_validate:
        #         validate(definition, DATASET_FILE_SCHEMA)
        # except ValidationError as validation_error:
        #     raise InvalidDataSetFileDefinition('JSON_VALIDATION_ERROR', 'Error validating against schema: %s' % validation_error)

    def get_dict(self):
        """Returns the dict of the definition
        """

        return self._definition

    def _populate_default_values(self):
        """Populates any missing required valudes with defaults
        """


