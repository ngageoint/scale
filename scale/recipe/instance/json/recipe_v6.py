"""Manages the v6 recipe instance schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition
from recipe.instance.exceptions import InvalidRecipe


SCHEMA_VERSION = '6'


RECIPE_INSTANCE_SCHEMA = {
    'type': 'object',
    'required': ['version', 'nodes'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the recipe instance schema',
            'type': 'string',
        },
        'nodes': {
            'description': 'The details for each node in the recipe',
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
        'node': {
            'description': 'The details for a node in the recipe',
            'type': 'object',
            'required': ['dependencies', 'node_type'],
            'additionalProperties': False,
            'properties': {
                'dependencies': {
                    'description': 'The other recipe nodes upon which this node is dependent',
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/dependency',
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
            'description': 'The details for a job node in the recipe',
            'type': 'object',
            'required': ['node_type', 'job_type_name', 'job_type_version', 'job_type_revision', 'job_id', 'status'],
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
                'job_id': {
                    'description': 'The unique ID of the job',
                    'type': 'integer',
                },
                'status': {
                    'description': 'The status of the job',
                    'type': 'string',
                },
            },
        },
        'recipe_node': {
            'description': 'The details for a sub-recipe node in the recipe',
            'type': 'object',
            'required': ['node_type', 'recipe_type_name', 'recipe_type_revision', 'recipe_id', 'is_completed',
                         'jobs_total', 'jobs_pending', 'jobs_blocked', 'jobs_queued', 'jobs_running', 'jobs_failed',
                         'jobs_completed', 'jobs_canceled'],
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
                'recipe_id': {
                    'description': 'The unique ID of the sub-recipe',
                    'type': 'integer',
                },
                'is_completed': {
                    'description': 'Whether this sub-recipe has completed',
                    'type': 'boolean',
                },
                'jobs_total': {
                    'description': 'The total number of jobs in this sub-recipe',
                    'type': 'integer',
                },
                'jobs_pending': {
                    'description': 'The number of PENDING jobs in this sub-recipe',
                    'type': 'integer',
                },
                'jobs_blocked': {
                    'description': 'The number of BLOCKED jobs in this sub-recipe',
                    'type': 'integer',
                },
                'jobs_queued': {
                    'description': 'The number of QUEUED jobs in this sub-recipe',
                    'type': 'integer',
                },
                'jobs_running': {
                    'description': 'The number of RUNNING jobs in this sub-recipe',
                    'type': 'integer',
                },
                'jobs_failed': {
                    'description': 'The number of FAILED jobs in this sub-recipe',
                    'type': 'integer',
                },
                'jobs_completed': {
                    'description': 'The number of COMPLETED jobs in this sub-recipe',
                    'type': 'integer',
                },
                'jobs_canceled': {
                    'description': 'The number of CANCELED jobs in this sub-recipe',
                    'type': 'integer',
                },
            },
        },
    },
}


def convert_recipe_to_v6_json(recipe):
    """Returns the v6 recipe JSON for the given recipe instance

    :param recipe: The recipe instance
    :type recipe: :class:`recipe.instance.recipe.RecipeInstance`
    :returns: The v6 recipe JSON
    :rtype: :class:`recipe.instance.json.recipe_v6.RecipeInstanceV6`
    """

    json_dict = {'nodes': {n.name: convert_node_to_v6_json(n) for n in recipe.graph.values()}}

    return RecipeInstanceV6(json=json_dict, do_validate=False)

def convert_node_to_v6_json(node):
    """Returns the v6 JSON dict for the given node instance

    :param node: The node instance
    :type node: :class:`recipe.instance.node.NodeInstance`
    :returns: The v6 JSON dict for the node
    :rtype: dict
    """

    dependencies = [{'name': name} for name in node.parents.keys()]
    node_def = node.definition

    if node.node_type == JobNodeDefinition.NODE_TYPE:
        node_type_dict = {'node_type': 'job', 'job_type_name': node_def.job_type_name,
                          'job_type_version': node_def.job_type_version, 'job_type_revision': node_def.revision_num,
                          'job_id': node.job.id, 'status': node.job.status}
    elif node.node_type == RecipeNodeDefinition.NODE_TYPE:
        node_type_dict = {'node_type': 'recipe', 'recipe_type_name': node_def.recipe_type_name,
                          'recipe_type_revision': node_def.revision_num, 'recipe_id': node.recipe.id,
                          'is_completed': node.recipe.is_completed, 'jobs_total': node.recipe.jobs_total,
                          'jobs_pending': node.recipe.jobs_pending, 'jobs_blocked': node.recipe.jobs_blocked,
                          'jobs_queued': node.recipe.jobs_queued, 'jobs_running': node.recipe.jobs_running,
                          'jobs_failed': node.recipe.jobs_failed, 'jobs_completed': node.recipe.jobs_completed,
                          'jobs_canceled': node.recipe.jobs_canceled}

    return {'dependencies': dependencies, 'node_type': node_type_dict}


class RecipeInstanceV6(object):
    """Represents a v6 recipe instance JSON"""

    def __init__(self, json=None, do_validate=False):
        """Creates a v6 recipe instance JSON object from the given dictionary

        :param json: The recipe instance JSON dict
        :type json: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`recipe.instance.exceptions.InvalidRecipe`: If the given recipe instance is invalid
        """

        if not json:
            json = {}
        self._json = json

        if 'version' not in self._json:
            self._json['version'] = SCHEMA_VERSION

        if self._json['version'] != SCHEMA_VERSION:
            raise InvalidRecipe('%s is an unsupported version number' % self._json['version'])

        self._populate_default_values()

        try:
            if do_validate:
                validate(self._json, RECIPE_INSTANCE_SCHEMA)
        except ValidationError as ex:
            raise InvalidRecipe('Invalid recipe instance: %s' % unicode(ex))

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._json

    def _populate_default_values(self):
        """Populates any missing required values with defaults
        """

        if 'nodes' not in self._json:
            self._json['nodes'] = {}
