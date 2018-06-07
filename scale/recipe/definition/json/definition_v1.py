"""Defines the class for managing a recipe definition"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from recipe.definition.exceptions import InvalidDefinition


DEFAULT_VERSION = '1.0'


RECIPE_DEFINITION_SCHEMA = {
    'type': 'object',
    'required': [
        'jobs',
    ],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the recipe definition schema',
            'type': 'string',
            'pattern': '^.{0,50}$',
        },
        'input_data': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/input_data_item',
            },
        },
        'jobs': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/job_item',
            },
        },
    },
    'definitions': {
        'input_data_item': {
            'type': 'object',
            'required': [
                'name', 'type',
            ],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z0-9\\-_ ]{0,255}$',
                },
                'type': {
                    'type': 'string',
                    'enum': [
                        'file', 'files', 'property',
                    ],
                },
                'required': {
                    'type': 'boolean',
                },
                'media_types': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                    },
                },
            },
        },
        'job_item': {
            'type': 'object',
            'required': [
                'name',
                'job_type',
            ],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z0-9\\-_ ]{1,255}$',
                },
                'job_type': {
                    'type': 'object',
                    'required': [
                        'name', 'version',
                    ],
                    'additionalProperties': False,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'pattern': '^[a-zA-Z0-9\\-_ ]{1,255}$',
                        },
                        'version': {
                            'type': 'string',
                        },
                    },
                },
                'recipe_inputs': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/recipe_input_item',
                    },
                },
                'dependencies': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/dependency_item',
                    },
                },
            },
        },
        'recipe_input_item': {
            'type': 'object',
            'required': [
                'recipe_input', 'job_input',
            ],
            'additionalProperties': False,
            'properties': {
                'recipe_input': {
                    'type': 'string',
                },
                'job_input': {
                    'type': 'string',
                },
            },
        },
        'dependency_item': {
            'type': 'object',
            'required': [
                'name',
            ],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                },
                'connections': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/connection_item',
                    },
                },
            },
        },
        'connection_item': {
            'type': 'object',
            'required': [
                'output', 'input',
            ],
            'additionalProperties': False,
            'properties': {
                'output': {
                    'type': 'string',
                },
                'input': {
                    'type': 'string',
                },
            },
        },
    },
}


class RecipeDefinitionV1(object):
    """Represents a v1 recipe definition JSON"""

    def __init__(self, definition=None, do_validate=False):
        """Creates a v1 recipe definition JSON object from the given dictionary

        :param definition: The recipe definition JSON dict
        :type definition: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`recipe.definition.exceptions.InvalidDdefinition`: If the given definition is invalid
        """

        if not definition:
            definition = {}
        self._definition = definition

        if 'version' not in self._definition:
            self._definition['version'] = DEFAULT_VERSION

        if self._definition['version'] != DEFAULT_VERSION:
            msg = '%s is an unsupported version number'
            raise InvalidDefinition('INVALID_VERSION', msg % self._definition['version'])

        self._populate_default_values()

        try:
            if do_validate:
                validate(definition, RECIPE_DEFINITION_SCHEMA)
        except ValidationError as ex:
            raise InvalidDefinition('INVALID_DEFINITION', 'Invalid recipe definition: %s' % unicode(ex))

    def get_dict(self):
        """Returns the internal dictionary that represents this recipe definition

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition

    def _populate_default_values(self):
        """Goes through the definition and populates any missing values with defaults
        """

        if 'input_data' not in self._definition:
            self._definition['input_data'] = []
        for input_dict in self._definition['input_data']:
            if 'required' not in input_dict:
                input_dict['required'] = True

        for job_dict in self._definition['jobs']:
            if 'recipe_inputs' not in job_dict:
                job_dict['recipe_inputs'] = []
            if 'dependencies' not in job_dict:
                job_dict['dependencies'] = []
            for dependency_dict in job_dict['dependencies']:
                if 'connections' not in dependency_dict:
                    dependency_dict['connections'] = []
