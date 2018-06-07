"""Defines the class for managing a recipe definition"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from data.interface.parameter import FileParameter, JsonParameter
from recipe.definition.connection import DependencyInputConnection, RecipeInputConnection
from recipe.definition.exceptions import InvalidDefinition
from recipe.definition.node import JobNodeDefinition


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


def convert_recipe_definition_to_v1_json(definition):
    """Returns the v1 recipe definition JSON for the given recipe definition

    :param definition: The recipe definition
    :type definition: :class:`recipe.definition.definition.RecipeDefinition`
    :returns: The v1 recipe definition JSON
    :rtype: :class:`recipe.definition.json.definition_v1.RecipeDefinitionV1`
    """

    input_data = []
    for parameter in definition.input_interface.parameters.values():
        input_data_dict = {'name': parameter.name, 'required': parameter.required}
        if parameter.param_type == FileParameter.PARAM_TYPE:
            input_data_dict['type'] = 'files' if parameter.multiple else 'file'
            input_data_dict['media_types'] = parameter.media_types
        elif parameter.param_type == JsonParameter.PARAM_TYPE and parameter.json_type == 'string':
            input_data_dict['type'] = 'property'
        if 'type' in input_data_dict:
            input_data.append(input_data_dict)

    jobs = []
    for node in definition.graph.values():
        if node.node_type == JobNodeDefinition.NODE_TYPE:
            jobs.append(convert_job_to_v1_json(node))

    json_dict = {'version': DEFAULT_VERSION, 'input_data': input_data, 'jobs': jobs}

    return RecipeDefinitionV1(definition=json_dict, do_validate=False)


def convert_job_to_v1_json(node):
    """Returns the v1 JSON dict for the given job node

    :param node: The job node
    :type node: :class:`recipe.definition.node.JobNodeDefinition`
    :returns: The v1 JSON dict for the node
    :rtype: dict
    """

    dependency_names = set()
    dependencies = []
    connections = {}  # {Dependency name: [Connection]}
    recipe_inputs = []
    for conn in node.connections.values():
        if isinstance(conn, DependencyInputConnection):
            conn_dict = {'output': conn.output_name, 'input': conn.input_name}
            if conn.node_name not in connections:
                connections[conn.node_name] = []
            connections[conn.node_name].append(conn_dict)
        elif isinstance(conn, RecipeInputConnection):
            recipe_inputs.append({'recipe_input': conn.recipe_input_name, 'job_input': conn.input_name})

    for d_name, conns in connections.items():
        dependencies.append({'name': d_name, 'connections': conns})
        dependency_names.add(d_name)
    for d_name in node.parents.keys():
        if d_name not in dependency_names:
            dependencies.append({'name': d_name, 'connections': []})
            dependency_names.add(d_name)

    job_dict = {'name': node.name, 'job_type': {'name': node.job_type_name, 'version': node.job_type_version},
                'dependencies': dependencies, 'recipe_inputs': recipe_inputs}

    return job_dict


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

        if 'jobs' not in self._definition:
            self._definition['jobs'] = []
        for job_dict in self._definition['jobs']:
            if 'recipe_inputs' not in job_dict:
                job_dict['recipe_inputs'] = []
            if 'dependencies' not in job_dict:
                job_dict['dependencies'] = []
            for dependency_dict in job_dict['dependencies']:
                if 'connections' not in dependency_dict:
                    dependency_dict['connections'] = []
