"""Manages the v6 recipe diff schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from recipe.diff.exceptions import InvalidDiff


SCHEMA_VERSION = '6'


RECIPE_DIFF_SCHEMA = {
    'type': 'object',
    'required': ['version', 'can_be_reprocessed', 'reasons', 'nodes'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the recipe diff schema',
            'type': 'string',
        },
        'can_be_reprocessed': {
            'description': 'Whether this recipe type can be re-processed',
            'type': 'boolean',
        },
        'reasons': {
            'description': 'The reasons why the recipe type cannot be re-processed',
            'type': 'array',
            'items': {
                '$ref': '#/definitions/reason',
            },
        },
        'nodes': {
            'description': 'The diff for each node in the recipe graph',
            'type': 'object',
            'additionalProperties': {
                '$ref': '#/definitions/node'
            },
        },
    },
    'definitions': {
        'change': {
            'description': 'A change that occurred for this recipe node from previous revision to current revision',
            'type': 'object',
            'required': ['name', 'description'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'description': 'The unique name (key) of the change',
                    'type': 'string',
                },
                'description': {
                    'description': 'The human-readable description of the change',
                    'type': 'string',
                },
            },
        },
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
            'description': 'The diff for a node in the recipe graph',
            'type': 'object',
            'required': ['status', 'changes', 'reprocess_new_node', 'force_reprocess', 'dependencies', 'node_type'],
            'additionalProperties': False,
            'properties': {
                'status': {
                    'description': 'The diff status for this recipe node compared to the previous revision',
                    'enum': ['DELETED', 'UNCHANGED', 'CHANGED', 'NEW'],
                },
                'changes': {
                    'description': 'The changes for this recipe node from previous revision to current revision',
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/change',
                    },
                },
                'reprocess_new_node': {
                    'description': 'Whether this node will be re-processed',
                    'type': 'boolean',
                },
                'force_reprocess': {
                    'description': 'If true, this node will be re-processed even if its status is UNCHANGED',
                    'type': 'boolean',
                },
                'dependencies': {
                    'description': 'The other recipe nodes upon which this node is dependent',
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/dependency',
                    },
                },
                'prev_node_type': {
                    'description': 'The type of this node in the previous revision',
                    'enum': ['job', 'recipe'],
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
            'description': 'The diff details for a job node in the recipe graph',
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
                'prev_job_type_name': {
                    'description': 'The name of the job type in the previous revision',
                    'type': 'string',
                },
                'prev_job_type_version': {
                    'description': 'The version of the job type in the previous revision',
                    'type': 'string',
                },
                'prev_job_type_revision': {
                    'description': 'The revision of the job type in the previous revision',
                    'type': 'integer',
                },
            },
        },
        'recipe_node': {
            'description': 'The diff details for a recipe node in the recipe graph',
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
                'prev_recipe_type_name': {
                    'description': 'The name of the recipe type in the previous revision',
                    'type': 'string',
                },
                'prev_recipe_type_revision': {
                    'description': 'The revision of the recipe type in the previous revision',
                    'type': 'integer',
                },
            },
        },
        'reason': {
            'description': 'Explanation for why the recipe type cannot be reprocessed due to the diff changes',
            'type': 'object',
            'required': ['name', 'description'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'description': 'The unique name (key) of the reason',
                    'type': 'string',
                },
                'description': {
                    'description': 'The human-readable description of the reason',
                    'type': 'string',
                },
            },
        },
    },
}


# TODO: remove this once old recipe definitions are removed
def convert_diff_to_v6(graph_diff):
    """Returns the v6 recipe graph diff JSON for the given graph diff

    :param graph_diff: The recipe graph diff
    :type graph_diff: :class:`recipe.handlers.graph_delta.RecipeGraphDelta`
    :returns: The v6 recipe graph diff JSON
    :rtype: :class:`recipe.diff.json.diff_v6.RecipeDiffV6`
    """

    # Must grab job type revisions numbers from database
    from job.models import JobType
    revision_lookup = {}
    for job_type in JobType.objects.all():
        revision_lookup[job_type.name + ' ' + job_type.version] = job_type.revision_num

    reasons = []
    nodes = {}
    json_dict = {'version': '6', 'can_be_reprocessed': graph_diff.can_be_reprocessed, 'reasons': reasons,
                 'nodes': nodes}

    if not graph_diff.can_be_reprocessed:
        reasons.extend([{'name': r.name, 'description': r.description} for r in graph_diff.reasons])

    for recipe_node in graph_diff._graph_b._nodes.values():
        name = recipe_node.job_name
        force_reprocess = name in graph_diff._force_reprocess
        if name in graph_diff._new_nodes:
            status = 'NEW'
        elif name in graph_diff._identical_nodes:
            status = 'UNCHANGED'
        elif name in graph_diff._changed_nodes:
            status = 'CHANGED'
        else:
            continue
        reprocess_new_node = (status in ['NEW', 'CHANGED'] or force_reprocess) and graph_diff.can_be_reprocessed
        changes = []
        if status == 'CHANGED' and name in graph_diff._changes:
            changes.extend([{'name': c.name, 'description': c.description} for c in graph_diff._changes[name]])
        job_type_name = recipe_node.job_type_name
        job_type_version = recipe_node.job_type_version
        job_type = {'node_type': 'job', 'job_type_name': job_type_name, 'job_type_version': job_type_version,
                    'job_type_revision': revision_lookup[job_type_name + ' ' + job_type_version]}
        if status == 'CHANGED' and name in graph_diff._graph_a._nodes:
            prev_node = graph_diff._graph_a._nodes[name]
            if recipe_node.job_type_name != prev_node.job_type_name:
                job_type['prev_job_type_name'] = prev_node.job_type_name
            if recipe_node.job_type_version != prev_node.job_type_version:
                job_type['prev_job_type_version'] = prev_node.job_type_version
        dependencies = [{'name': p.job_name} for p in recipe_node.parents]
        job_node = {'reprocess_new_node': reprocess_new_node, 'force_reprocess': force_reprocess, 'status': status,
                    'changes': changes, 'node_type': job_type, 'dependencies': dependencies}
        nodes[name] = job_node

    for recipe_node in graph_diff._graph_a._nodes.values():
        name = recipe_node.job_name
        if name not in graph_diff._deleted_nodes:
            continue
        job_type_name = recipe_node.job_type_name
        job_type_version = recipe_node.job_type_version
        job_type = {'node_type': 'job', 'job_type_name': job_type_name, 'job_type_version': job_type_version,
                    'job_type_revision': revision_lookup[job_type_name + ' ' + job_type_version]}
        dependencies = [{'name': p.job_name} for p in recipe_node.parents]
        job_node = {'reprocess_new_node': False, 'force_reprocess': False, 'status': 'DELETED', 'changes': [],
                    'node_type': job_type, 'dependencies': dependencies}
        nodes[name] = job_node

    return RecipeDiffV6(diff=json_dict, do_validate=False)


def convert_recipe_diff_to_v6_json(recipe_diff):
    """Returns the v6 recipe diff JSON for the given recipe diff

    :param recipe_diff: The recipe diff
    :type recipe_diff: :class:`recipe.diff.diff.RecipeDiff`
    :returns: The v6 recipe diff JSON
    :rtype: :class:`recipe.diff.json.diff_v6.RecipeDiffV6`
    """

    reasons = [{'name': r.name, 'description': r.description} for r in recipe_diff.reasons]
    nodes_dict = {n.name: convert_node_diff_to_v6_json(n) for n in recipe_diff.graph.values()}
    json_dict = {'can_be_reprocessed': recipe_diff.can_be_reprocessed, 'reasons': reasons, 'nodes': nodes_dict}

    return RecipeDiffV6(diff=json_dict, do_validate=False)

def convert_node_diff_to_v6_json(node_diff):
    """Returns the v6 diff JSON dict for the given node diff

    :param node_diff: The node diff
    :type node_diff: :class:`recipe.diff.node.NodeDiff`
    :returns: The v6 diff JSON dict for the node
    :rtype: dict
    """

    changes = [{'name': c.name, 'description': c.description} for c in node_diff.changes]
    dependencies = [{'name': name} for name in node_diff.parents.keys()]

    node_dict = {'status': node_diff.status, 'changes': changes, 'reprocess_new_node': node_diff.reprocess_new_node,
                 'force_reprocess': node_diff.force_reprocess, 'dependencies': dependencies,
                 'node_type': node_diff.get_node_type_dict()}

    if node_diff.prev_node_type is not None:
        node_dict['prev_node_type'] = node_diff.prev_node_type

    return node_dict


class RecipeDiffV6(object):
    """Represents a v6 recipe graph diff JSON for the difference between two recipe graphs"""

    def __init__(self, diff=None, do_validate=False):
        """Creates a v6 recipe graph diff JSON object from the given dictionary

        :param diff: The recipe graph diff JSON dict
        :type diff: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`recipe.diff.exceptions.InvalidDiff`: If the given diff is invalid
        """

        if not diff:
            diff = {}
        self._diff = diff

        if 'version' not in self._diff:
            self._diff['version'] = SCHEMA_VERSION

        if self._diff['version'] != SCHEMA_VERSION:
            raise InvalidDiff('%s is an unsupported version number' % self._diff['version'])

        self._populate_default_values()

        try:
            if do_validate:
                validate(diff, RECIPE_DIFF_SCHEMA)
        except ValidationError as ex:
            raise InvalidDiff('Invalid recipe graph diff: %s' % unicode(ex))

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._diff

    def _populate_default_values(self):
        """Populates any missing required values with defaults
        """

        if 'can_be_reprocessed' not in self._diff:
            self._diff['can_be_reprocessed'] = True
        if 'reasons' not in self._diff:
            self._diff['reasons'] = []
        if 'nodes' not in self._diff:
            self._diff['nodes'] = {}
