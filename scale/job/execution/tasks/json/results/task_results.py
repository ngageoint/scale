"""Defines the JSON schema for describing task results"""
from __future__ import unicode_literals

from django.utils import dateparse
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

    def __init__(self, task_results=None, do_validate=True):
        """Creates task results from the given JSON dict

        :param task_results: The JSON dictionary
        :type task_results: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool
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
            if do_validate:
                validate(task_results, TASK_RESULTS_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidTaskResults(validation_error)

    def add_task_results(self, tasks):
        """Adds the given job execution tasks to the results

        :param tasks: The job execution tasks to add
        :type tasks: :func:`list`
        """

        task_list = self._task_results['tasks']
        for task in tasks:
            task_dict = {'task_id': task.id, 'type': task.task_type, 'was_launched': task.has_been_launched}
            if task.has_been_launched:
                task_dict.update(launched=datetime_to_string(task.launched), was_started=task.has_started)
                if task.has_started:
                    task_dict.update(started=datetime_to_string(task.started), was_timed_out=task.has_timed_out,
                                     ended=datetime_to_string(task.ended), status=task.final_status)
                    if task.exit_code is not None:
                        task_dict.update(exit_code=task.exit_code)
            task_list.append(task_dict)

    def get_dict(self):
        """Returns the internal dictionary that represents the task results

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._task_results

    def get_task_ended(self, task_type):
        """Returns the end time for the given task type, possibly None

        :param task_type: The task type
        :type task_type: string
        :returns: The task end time
        :rtype: :class:`datetime.datetime`:
        """

        for task_dict in self._task_results['tasks']:
            if task_dict['type'] == task_type:
                if 'ended' in task_dict:
                    return dateparse.parse_datetime(task_dict['ended'])
        return None

    def get_task_run_length(self, task_type):
        """Returns the run time length for the given task type, possibly None

        :param task_type: The task type
        :type task_type: string
        :returns: The task run time length
        :rtype: :class:`datetime.timedelta`:
        """

        for task_dict in self._task_results['tasks']:
            if task_dict['type'] == task_type:
                if 'started' in task_dict and 'ended' in task_dict:
                    started = dateparse.parse_datetime(task_dict['started'])
                    ended = dateparse.parse_datetime(task_dict['ended'])
                    return ended - started
        return None

    def get_task_started(self, task_type):
        """Returns the start time for the given task type, possibly None

        :param task_type: The task type
        :type task_type: string
        :returns: The task start time
        :rtype: :class:`datetime.datetime`:
        """

        for task_dict in self._task_results['tasks']:
            if task_dict['type'] == task_type:
                if 'started' in task_dict:
                    return dateparse.parse_datetime(task_dict['started'])
        return None

    def _populate_default_values(self):
        """Populates any missing JSON fields that have default values
        """

        if 'tasks' not in self._task_results:
            self._task_results['tasks'] = []
