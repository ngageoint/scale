"""Manages the v6 recipe graph diff schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from recipe.diff.exceptions import InvalidDiff


SCHEMA_VERSION = '6'


RECIPE_GRAPH_DIFF_SCHEMA = {
    'type': 'object',
    'required': ['version', 'can_be_reprocessed', 'reasons', 'jobs'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the recipe graph diff schema',
            'type': 'string',
        },
        'can_be_reprocessed': {
            'description': 'Whether this recipe type can be re-processed',
            'type': 'boolean',
        },
        'reasons': {
            'description': 'The reasons why the recipe type cannot be re-processed',
            'type': ['array'],
            'items': {
                '$ref': '#/definitions/reason',
            },
        },
        'jobs': {
            'description': 'The diff for each job in the recipe graph',
            'type': ['array'],
            'items': {
                '$ref': '#/definitions/job',
            },
        },
    },
    'definitions': {
        'change': {
            'description': 'A change that occurred for this recipe job from previous revision to current revision',
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
            'description': 'A dependency on another recipe job',
            'type': 'object',
            'required': ['name'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'description': 'The name of the recipe job',
                    'type': 'string',
                },
            },
        },
        'job': {
            'description': 'The diff for a job in the recipe graph',
            'type': 'object',
            'required': ['name', 'will_be_reprocessed', 'force_reprocess', 'status', 'changes', 'job_type',
                         'dependencies'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'description': 'The name of the recipe job',
                    'type': 'string',
                },
                'will_be_reprocessed': {
                    'description': 'Whether this job will be re-processed (have a new job created)',
                    'type': 'boolean',
                },
                'force_reprocess': {
                    'description': 'If true, this job will be re-processed even if its status is UNCHANGED',
                    'type': 'boolean',
                },
                'status': {
                    'description': 'The diff status for this recipe job compared to the previous revision',
                    'type': 'string',
                    'enum': ['DELETED', 'UNCHANGED', 'CHANGED', 'NEW'],
                },
                'changes': {
                    'description': 'The reasons why the recipe type cannot be re-processed',
                    'type': ['array'],
                    'items': {
                        '$ref': '#/definitions/change',
                    },
                },
                'job_type': {
                    '$ref': '#/definitions/job_type',
                },
                'dependencies': {
                    'description': 'The other recipe jobs upon which this job is dependent',
                    'type': ['array'],
                    'items': {
                        '$ref': '#/definitions/dependency',
                    },
                },
            },
        },
        'job_type': {
            'description': 'Describes the job type of the recipe job',
            'type': 'object',
            'required': ['name', 'version'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'description': 'The name of the job type',
                    'type': 'string',
                },
                'version': {
                    'description': 'The version of the job type',
                    'type': 'string',
                },
                'prev_name': {
                    'description': 'The name of the job type in the previous revision',
                    'type': 'string',
                },
                'prev_version': {
                    'description': 'The version of the job type in the previous revision',
                    'type': 'string',
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


def convert_diff_to_v6(graph_diff):
    """Returns the v6 recipe graph diff JSON for the given graph diff

    :param graph_diff: The recipe graph diff
    :type graph_diff: :class:`recipe.handlers.graph_delta.RecipeGraphDelta`
    :returns: The v6 recipe graph diff JSON
    :rtype: :class:`recipe.diff.json.diff_v6.RecipeGraphDiffV6`
    """

    reasons = []
    jobs = []
    json_dict = {'version': '6', 'can_be_reprocessed': graph_diff.can_be_reprocessed, 'reasons': reasons, 'jobs': jobs}

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
        will_be_reprocessed = (status in ['NEW', 'CHANGED'] or force_reprocess) and graph_diff.can_be_reprocessed
        changes = []
        if status == 'CHANGED' and name in graph_diff._changes:
            changes.extend([{'name': c.name, 'description': c.description} for c in graph_diff._changes[name]])
        job_type = {'name': recipe_node.job_type_name, 'version': recipe_node.job_type_version}
        if status == 'CHANGED' and name in graph_diff._graph_a._nodes:
            prev_node = graph_diff._graph_a._nodes[name]
            if recipe_node.job_type_name != prev_node.job_type_name:
                job_type['prev_name'] = prev_node.job_type_name
            if recipe_node.job_type_version != prev_node.job_type_version:
                job_type['prev_version'] = prev_node.job_type_version
        dependencies = [{'name': p.job_name} for p in recipe_node.parents]
        job = {'name': name, 'will_be_reprocessed': will_be_reprocessed, 'force_reprocess': force_reprocess,
               'status': status, 'changes': changes, 'job_type': job_type, 'dependencies': dependencies}
        jobs.append(job)

    for recipe_node in graph_diff._graph_a._nodes.values():
        name = recipe_node.job_name
        if name not in graph_diff._deleted_nodes:
            continue
        job_type = {'name': recipe_node.job_type_name, 'version': recipe_node.job_type_version}
        dependencies = [{'name': p.job_name} for p in recipe_node.parents]
        job = {'name': name, 'will_be_reprocessed': False, 'force_reprocess': False,
               'status': 'DELETED', 'changes': [], 'job_type': job_type, 'dependencies': dependencies}
        jobs.append(job)

    return RecipeGraphDiffV6(diff=json_dict, do_validate=False)


class RecipeGraphDiffV6(object):
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
                validate(diff, RECIPE_GRAPH_DIFF_SCHEMA)
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
        if 'jobs' not in self._diff:
            self._diff['jobs'] = []
