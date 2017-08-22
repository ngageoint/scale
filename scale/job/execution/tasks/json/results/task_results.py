"""Defines the JSON schema for describing task results"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.execution.exceptions import InvalidTaskResults
from util.parse import datetime_to_string


SCHEMA_VERSION = '1.0'


TASK_RESULTS_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the task results schema',
            'type': 'string',
            'pattern': '^.{0,50}$',
        },
        'tasks': {
            'description': 'The results for each task',
            'type': 'array',
            'items': {
                '$ref': '#/definitions/task',
            },
        },
    },
    'definitions': {
        'task': {
            'type': 'object',
            'required': ['task_id', 'type', 'was_launched'],
            'additionalProperties': False,
            'properties': {
                'task_id': {
                    'description': 'The ID of the task',
                    'type': 'string',
                },
                'type': {
                    'description': 'The type of the task',
                    'type': 'string',
                },
                'was_launched': {
                    'description': 'Whether the task was launched',
                    'type': 'boolean',
                },
                'launched': {
                    'description': 'When the task was launched',
                    'type': 'string',
                },
                'was_started': {
                    'description': 'Whether the task was started',
                    'type': 'boolean',
                },
                'started': {
                    'description': 'When the task was started',
                    'type': 'string',
                },
                'was_timed_out': {
                    'description': 'Whether the task was timed out',
                    'type': 'boolean',
                },
                'ended': {
                    'description': 'When the task ended',
                    'type': 'string',
                },
                'status': {
                    'description': 'The final status of the task',
                    'type': 'string',
                    'enum': ['FINISHED', 'FAILED', 'KILLED'],
                },
                'exit_code': {
                    'description': 'The exit code of the task',
                    'type': 'integer',
                },
            },
        },
    },
}


class TaskResults(object):
    """Represents the task results for a job execution
    """

    def __init__(self, task_results=None):
        """Creates task results from the given JSON dict

        :param task_results: The JSON dictionary
        :type task_results: dict
        :raises :class:`job.execution.exceptions.InvalidTaskResults`: If the JSON is invalid
        """

        if not task_results:
            task_results = {}
        self._task_results = task_results

        if 'version' not in self._task_results:
            self._task_results['version'] = SCHEMA_VERSION

        if self._task_results['version'] != SCHEMA_VERSION:
            raise InvalidTaskResults('%s is an unsupported version number' % self._task_results['version'])

        self._populate_default_values()

        try:
            validate(task_results, TASK_RESULTS_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidTaskResults(validation_error)

    def add_task_results(self, tasks):
        """Adds the given job execution tasks to the results

        :param tasks: The job execution tasks to add
        :type tasks: list
        """

        task_list = self._task_results['tasks']
        for task in tasks:
            task_dict = {'task_id': task.id, 'type': task.task_type, 'was_launched': task.has_been_launched}
            if task.has_been_launched:
                task_dict.update(launched=datetime_to_string(task.launched), was_started=task.has_started)
                if task.has_started:
                    task_dict.update(started=datetime_to_string(task.started), was_timed_out=task.has_timed_out,
                                     ended=datetime_to_string(task.ended), status=task.final_status)
                    if task.exit_code:
                        task_dict.update(exit_code=task.exit_code)
            task_list.append(task_dict)

    def get_dict(self):
        """Returns the internal dictionary that represents the task results

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._task_results

    def _populate_default_values(self):
        """Populates any missing JSON fields that have default values
        """

        if 'tasks' not in self._task_results:
            self._task_results['tasks'] = []
