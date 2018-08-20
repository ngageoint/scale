"""Defines the JSON schema for describing the job configuration"""
from __future__ import unicode_literals

import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.execution.configuration.exceptions import InvalidExecutionConfiguration


logger = logging.getLogger(__name__)


SCHEMA_VERSION = '1.0'
MODE_RO = 'ro'
MODE_RW = 'rw'


EXE_CONFIG_SCHEMA = {
    'type': 'object',
    'required': ['job_task'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the job configuration schema',
            'type': 'string',
            'pattern': '^.{0,50}$',
        },
        'pre_task': {'$ref': '#/definitions/task'},
        'job_task': {'$ref': '#/definitions/task'},
        'post_task': {'$ref': '#/definitions/task'},
    },
    'definitions': {
        'task': {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'docker_params': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/docker_param',
                    },
                },
                'workspaces': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/workspace',
                    },
                },
            },
        },
        'workspace': {
            'type': 'object',
            'required': ['name', 'mode'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                },
                'mode': {
                    'type': 'string',
                    'enum': [MODE_RO, MODE_RW],
                },
            },
        },
        'docker_param': {
            'type': 'object',
            'required': ['flag', 'value'],
            'additionalProperties': False,
            'properties': {
                'flag': {
                    'type': 'string',
                },
                'value': {
                    'type': 'string',
                },
            },
        },
    },
}


class TaskWorkspace(object):
    """Represents a workspace needed by a job task
    """

    def __init__(self, name, mode):
        """Creates a task workspace
        :param name: The name of the workspace
        :type name: string
        :param mode: The mode to use for the workspace, either 'ro' or 'rw'
        :type mode: string
        """

        self.name = name
        self.mode = mode


class ExecutionConfiguration(object):
    """Represents a job configuration
    """

    def __init__(self, configuration=None):
        """Creates a job configuration from the given JSON dict

        :param configuration: The JSON dictionary
        :type configuration: dict
        :raises :class:`job.execution.configuration.exceptions.InvalidExecutionConfiguration`: If the JSON is invalid
        """

        if not configuration:
            configuration = {'job_task': {'docker_params': []}}
        self._configuration = configuration
        self._pre_task_workspace_names = set()
        self._job_task_workspace_names = set()
        self._post_task_workspace_names = set()

        try:
            validate(configuration, EXE_CONFIG_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidExecutionConfiguration(validation_error)

        self._populate_default_values()

        if self._configuration['version'] != SCHEMA_VERSION:
            raise InvalidExecutionConfiguration('%s is an unsupported version number' % self._configuration['version'])

        self._validate_workspace_names()

    def add_job_task_workspace(self, name, mode):
        """Adds a needed workspace to this job's job task

        :param name: The name of the workspace
        :type name: string
        :param mode: The mode of the workspace, either MODE_RO or MODE_RW
        :type mode: string
        """

        if mode not in [MODE_RO, MODE_RW]:
            raise Exception('%s is not a valid mode' % mode)

        if name in self._job_task_workspace_names:
            raise InvalidExecutionConfiguration('Duplicate workspace %s in job task' % name)
        self._configuration['job_task']['workspaces'].append({'name': name, 'mode': mode})

    def add_post_task_workspace(self, name, mode):
        """Adds a needed workspace to this job's post task

        :param name: The name of the workspace
        :type name: string
        :param mode: The mode of the workspace, either MODE_RO or MODE_RW
        :type mode: string
        """

        if mode not in [MODE_RO, MODE_RW]:
            raise Exception('%s is not a valid mode' % mode)

        if name in self._post_task_workspace_names:
            raise InvalidExecutionConfiguration('Duplicate workspace %s in post task' % name)
        self._configuration['post_task']['workspaces'].append({'name': name, 'mode': mode})

    def add_pre_task_workspace(self, name, mode):
        """Adds a needed workspace to this job's pre task

        :param name: The name of the workspace
        :type name: string
        :param mode: The mode of the workspace, either MODE_RO or MODE_RW
        :type mode: string
        """

        if mode not in [MODE_RO, MODE_RW]:
            raise Exception('%s is not a valid mode' % mode)

        if name in self._pre_task_workspace_names:
            raise InvalidExecutionConfiguration('Duplicate workspace %s in pre task' % name)
        self._configuration['pre_task']['workspaces'].append({'name': name, 'mode': mode})

    def configure_workspace_docker_params(self, job_exe, workspaces, docker_volumes):
        """Configures the Docker parameters needed for each workspace in the job execution tasks. The given job
        execution must have been set to RUNNING status.

        :param job_exe: The job execution model (must not be queued) with related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        :param workspaces: A dict of all workspaces stored by name
        :type workspaces: {string: :class:`storage.models.Workspace`}
        :param docker_volumes: A list to add Docker volume names to
        :type docker_volumes: [string]

        :raises Exception: If the job execution is still queued
        """

        # Configure pre-task workspaces, any that need volumes will have them created
        created_workspaces = set()
        params = self._get_workspace_docker_params(job_exe, self.get_pre_task_workspaces(), workspaces, True,
                                                   docker_volumes)
        self.add_pre_task_docker_params(params)
        for task_workspace in self.get_pre_task_workspaces():
            created_workspaces.add(task_workspace.name)

        # Configure job-task workspaces, creating any volumes that were not created in a previous task
        workspaces_already_created = []
        workspaces_not_created = []
        for task_workspace in self.get_job_task_workspaces():
            if task_workspace.name in created_workspaces:
                workspaces_already_created.append(task_workspace)
            else:
                workspaces_not_created.append(task_workspace)
                created_workspaces.add(task_workspace.name)
        params = self._get_workspace_docker_params(job_exe, workspaces_already_created, workspaces, False,
                                                   docker_volumes)
        self.add_job_task_docker_params(params)
        params = self._get_workspace_docker_params(job_exe, workspaces_not_created, workspaces, True, docker_volumes)
        self.add_job_task_docker_params(params)

        # Configure post-task workspaces, creating any volumes that were not created in a previous task
        workspaces_already_created = []
        workspaces_not_created = []
        for task_workspace in self.get_post_task_workspaces():
            if task_workspace.name in created_workspaces:
                workspaces_already_created.append(task_workspace)
            else:
                workspaces_not_created.append(task_workspace)
                created_workspaces.add(task_workspace.name)
        params = self._get_workspace_docker_params(job_exe, workspaces_already_created, workspaces, False,
                                                   docker_volumes)
        self.add_post_task_docker_params(params)
        params = self._get_workspace_docker_params(job_exe, workspaces_not_created, workspaces, True, docker_volumes)
        self.add_post_task_docker_params(params)

    def get_job_task_workspaces(self):
        """Returns the workspaces needed for the job task

        :returns: The job task workspaces
        :rtype: [:class:`job.execution.configuration.json.exe_config_1_0.TaskWorkspace`]
        """

        workspaces = self._configuration['job_task']['workspaces']
        return [TaskWorkspace(workspace_dict['name'], workspace_dict['mode']) for workspace_dict in workspaces]

    def get_post_task_workspaces(self):
        """Returns the workspaces needed for the post task

        :returns: The post task workspaces
        :rtype: [:class:`job.execution.configuration.json.exe_config_1_0.TaskWorkspace`]
        """

        workspaces = self._configuration['post_task']['workspaces']
        return [TaskWorkspace(workspace_dict['name'], workspace_dict['mode']) for workspace_dict in workspaces]

    def get_pre_task_workspaces(self):
        """Returns the workspaces needed for the pre task

        :returns: The pre task workspaces
        :rtype: [:class:`job.execution.configuration.json.exe_config_1_0.TaskWorkspace`]
        """

        workspaces = self._configuration['pre_task']['workspaces']
        return [TaskWorkspace(workspace_dict['name'], workspace_dict['mode']) for workspace_dict in workspaces]

    def get_dict(self):
        """Returns the internal dictionary that represents this job configuration

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration

    def _populate_default_values(self):
        """Populates any missing JSON fields that have default values
        """

        if 'version' not in self._configuration:
            self._configuration['version'] = SCHEMA_VERSION

        if 'pre_task' not in self._configuration:
            self._configuration['pre_task'] = {}
        if 'docker_params' not in self._configuration['pre_task']:
            self._configuration['pre_task']['docker_params'] = []
        if 'workspaces' not in self._configuration['pre_task']:
            self._configuration['pre_task']['workspaces'] = []

        if 'docker_params' not in self._configuration['job_task']:
            self._configuration['job_task']['docker_params'] = []
        if 'workspaces' not in self._configuration['job_task']:
            self._configuration['job_task']['workspaces'] = []

        if 'post_task' not in self._configuration:
            self._configuration['post_task'] = {}
        if 'docker_params' not in self._configuration['post_task']:
            self._configuration['post_task']['docker_params'] = []
        if 'workspaces' not in self._configuration['post_task']:
            self._configuration['post_task']['workspaces'] = []

    def _validate_workspace_names(self):
        """Ensures that no tasks have duplicate workspace names

        :raises :class:`job.execution.configuration.exceptions.InvalidExecutionConfiguration`: If there is a duplicate
            workspace name
        """

        for workspace_dict in self._configuration['pre_task']['workspaces']:
            name = workspace_dict['name']
            if name in self._pre_task_workspace_names:
                raise InvalidExecutionConfiguration('Duplicate workspace %s in pre task' % name)
            self._pre_task_workspace_names.add(name)
        for workspace_dict in self._configuration['job_task']['workspaces']:
            name = workspace_dict['name']
            if name in self._job_task_workspace_names:
                raise InvalidExecutionConfiguration('Duplicate workspace %s in job task' % name)
            self._job_task_workspace_names.add(name)
        for workspace_dict in self._configuration['post_task']['workspaces']:
            name = workspace_dict['name']
            if name in self._post_task_workspace_names:
                raise InvalidExecutionConfiguration('Duplicate workspace %s in post task' % name)
            self._post_task_workspace_names.add(name)
