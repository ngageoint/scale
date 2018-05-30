"""Manages the v6 recipe diff schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from data.interface.json.interface_v6 import INTERFACE_SCHEMA, convert_interface_to_v6_json, InterfaceV6
from recipe.definition.connection import DependencyInputConnection, RecipeInputConnection
from recipe.definition.definition import RecipeDefinition
from recipe.definition.exceptions import InvalidDefinition
from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition
from util.rest import strip_schema_version


SCHEMA_VERSION = '6'


RECIPE_DEFINITION_SCHEMA = {
    'type': 'object',
    'required': ['version', 'input', 'nodes'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the recipe definition schema',
            'type': 'string',
        },
        'input': INTERFACE_SCHEMA,
        'nodes': {
            'description': 'Each node in the recipe graph',
            'type': 'object',
            'additionalProperties': {
                '$ref': '#/definitions/node'
            },
        },
    },
    'definitions': {
        'dependency': {
            'description': 'A dependency on another recipe node',
            'type': 'object',
            'required': ['name'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'description': 'The name of the recipe node',
                    'type': 'string',
                },
            },
        },
        'dependency_connection': {
            'description': 'A connection from a dependency node output to a node input',
            'type': 'object',
            'required': ['type', 'node', 'output'],
            'additionalProperties': False,
            'properties': {
                'type': {
                    'description': 'The name of the input connection type',
                    'enum': ['dependency'],
                },
                'node': {
                    'description': 'The name of the dependency node',
                    'type': 'string',
                },
                'output': {
                    'description': 'The name of the dependency node\'s output',
                    'type': 'string',
                },
            },
        },
        'node': {
            'description': 'A node in the recipe graph',
            'type': 'object',
            'required': ['dependencies', 'input', 'node_type'],
            'additionalProperties': False,
            'properties': {
                'dependencies': {
                    'description': 'The other recipe nodes upon which this node is dependent',
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/dependency',
                    },
                },
                'input': {
                    'description': 'Each input connection to the node',
                    'type': 'object',
                    'additionalProperties': {
                        'oneOf': [
                            {'$ref': '#/definitions/dependency_connection'},
                            {'$ref': '#/definitions/recipe_connection'},
                        ],
                    },
                },
                'node_type': {
                    'description': 'The type of the node',
                    'oneOf': [
                        {'$ref': '#/definitions/job_node'},
                        {'$ref': '#/definitions/recipe_node'},
                    ],
                },
            },
        },
        'job_node': {
            'description': 'A job node in the recipe graph',
            'type': 'object',
            'required': ['node_type', 'job_type_name', 'job_type_version', 'job_type_revision'],
            'additionalProperties': False,
            'properties': {
                'node_type': {
                    'description': 'The name of the node type',
                    'enum': ['job'],
                },
                'job_type_name': {
                    'description': 'The name of the job type',
                    'type': 'string',
                },
                'job_type_version': {
                    'description': 'The version of the job type',
                    'type': 'string',
                },
                'job_type_revision': {
                    'description': 'The revision of the job type',
                    'type': 'integer',
                },
            },
        },
        'recipe_connection': {
            'description': 'A connection from a recipe input to a node input',
            'type': 'object',
            'required': ['type', 'input'],
            'additionalProperties': False,
            'properties': {
                'type': {
                    'description': 'The name of the input connection type',
                    'enum': ['recipe'],
                },
                'input': {
                    'description': 'The name of the recipe input',
                    'type': 'string',
                },
            },
        },
        'recipe_node': {
            'description': 'A recipe node in the recipe graph',
            'type': 'object',
            'required': ['node_type', 'recipe_type_name', 'recipe_type_revision'],
            'additionalProperties': False,
            'properties': {
                'node_type': {
                    'description': 'The name of the node type',
                    'enum': ['recipe'],
                },
                'recipe_type_name': {
                    'description': 'The name of the recipe type',
                    'type': 'string',
                },
                'recipe_type_revision': {
                    'description': 'The revision of the recipe type',
                    'type': 'integer',
                },
            },
        },
    },
}


def convert_recipe_definition_to_v6_json(definition):
    """Returns the v6 recipe definition JSON for the given recipe definition

    :param definition: The recipe definition
    :type definition: :class:`recipe.definition.definition.RecipeDefinition`
    :returns: The v6 recipe definition JSON
    :rtype: :class:`recipe.definition.json.definition_v6.RecipeDefinitionV6`
    """

    nodes_dict = {n.name: convert_node_to_v6_json(n) for n in definition.graph.values()}
    json_dict = {'version': '6', 'input': convert_interface_to_v6_json(definition.input_interface).get_dict(),
                 'nodes': nodes_dict}

    return RecipeDefinitionV6(definition=json_dict, do_validate=False)


def convert_node_to_v6_json(node):
    """Returns the v6 JSON dict for the given node

    :param node: The node
    :type node: :class:`recipe.definition.node.NodeDefinition`
    :returns: The v6 JSON dict for the node
    :rtype: dict
    """

    dependencies = [{'name': name} for name in node.parents.keys()]

    input_dict = {}
    for connection in node.connections.values():
        if isinstance(connection, DependencyInputConnection):
            conn_dict = {'type': 'dependency', 'node': connection.node_name, 'output': connection.output_name}
        elif isinstance(connection, RecipeInputConnection):
            conn_dict = {'type': 'recipe', 'input': connection.recipe_input_name}
        input_dict[connection.input_name] = conn_dict

    if isinstance(node, JobNodeDefinition):
        node_type_dict = {'node_type': 'job', 'job_type_name': node.job_type_name,
                          'job_type_version': node.job_type_version, 'job_type_revision': node.revision_num}
    elif isinstance(node, RecipeNodeDefinition):
        node_type_dict = {'node_type': 'recipe', 'recipe_type_name': node.recipe_type_name,
                          'recipe_type_revision': node.revision_num}

    node_dict = {'dependencies': dependencies, 'input': input_dict, 'node_type': node_type_dict}

    return node_dict


class RecipeDefinitionV6(object):
    """Represents a v6 recipe definition JSON"""

    def __init__(self, definition=None, do_validate=False):
        """Creates a v6 recipe definition JSON object from the given dictionary

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
            self._definition['version'] = SCHEMA_VERSION

        if self._definition['version'] != SCHEMA_VERSION:
            msg = '%s is an unsupported version number'
            raise InvalidDefinition('INVALID_VERSION', msg % self._definition['version'])

        self._populate_default_values()

        try:
            if do_validate:
                validate(self._definition, RECIPE_DEFINITION_SCHEMA)
        except ValidationError as ex:
            raise InvalidDefinition('INVALID_DEFINITION', 'Invalid recipe definition: %s' % unicode(ex))

    def get_definition(self):
        """Returns the recipe definition represented by this JSON

        :returns: The recipe definition
        :rtype: :class:`recipe.definition.definition.RecipeDefinition`:
        """

        interface_json = InterfaceV6(self._definition['input'], do_validate=False)
        interface = interface_json.get_interface()
        definition = RecipeDefinition(interface)

        # Add all nodes to definition first
        for node_name, node_dict in self._definition['nodes'].items():
            node_type_dict = node_dict['node_type']
            if node_type_dict['node_type'] == 'job':
                definition.add_job_node(node_name, node_type_dict['job_type_name'], node_type_dict['job_type_version'],
                                        node_type_dict['job_type_revision'])
            elif node_type_dict['node_type'] == 'recipe':
                definition.add_recipe_node(node_name, node_type_dict['recipe_type_name'],
                                           node_type_dict['recipe_type_revision'])

        # Now add dependencies and connections
        for node_name, node_dict in self._definition['nodes'].items():
            for dependency_dict in node_dict['dependencies']:
                definition.add_dependency(dependency_dict['name'], node_name)
            for conn_name, conn_dict in node_dict['input'].items():
                if conn_dict['type'] == 'recipe':
                    definition.add_recipe_input_connection(node_name, conn_name, conn_dict['input'])
                elif conn_dict['type'] == 'dependency':
                    definition.add_dependency_input_connection(node_name, conn_name, conn_dict['node'],
                                                               conn_dict['output'])

        return definition

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._definition

    def _populate_default_values(self):
        """Populates any missing required values with defaults
        """

        if 'input' not in self._definition:
            self._definition['input'] = {}
        if 'nodes' not in self._definition:
            self._definition['nodes'] = {}

        # Populate defaults for input interface
        interface_json = InterfaceV6(self._definition['input'], do_validate=False)
        self._definition['input'] = strip_schema_version(interface_json.get_dict())
