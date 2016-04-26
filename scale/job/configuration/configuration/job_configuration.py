"""Defines the JSON schema for describing the job configuration"""
from __future__ import unicode_literals

import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.configuration.exceptions import InvalidJobConfiguration


logger = logging.getLogger(__name__)


CURRENT_VERSION = '1.0'
MODE_RO = 'ro'
MODE_RW = 'rw'


JOB_CONFIGURATION_SCHEMA = {
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


class DockerParam(object):
    """Represents a Docker parameter
    """

    def __init__(self, flag, value):
        """Creates a Docker parameter

        :param flag: The Docker flag of the parameter
        :type flag: string
        :param value: The value being passed to the Docker parameter
        :type value: string
        """

        self.flag = flag
        self.value = value


class JobWorkspace(object):
    """Represents a workspace needed by a job task
    """

    def __init__(self, name, mode):
        """Creates a job workspace

        :param name: The name of the workspace
        :type name: string
        :param mode: The mode to use for the workspace, either 'ro' or 'rw'
        :type mode: string
        """

        self.name = name
        self.mode = mode


class JobConfiguration(object):
    """Represents a job configuration
    """

    def __init__(self, configuration=None):
        """Creates a job configuration from the given JSON dict

        :param configuration: The JSON dictionary
        :type configuration: dict
        :raises :class:`job.configuration.configuration.exceptions.InvalidJobConfiguration`: If the JSON is invalid
        """

        if not configuration:
            configuration = {'job_task': {'docker_params': []}}
        self._configuration = configuration
        self._pre_task_workspace_names = set()
        self._job_task_workspace_names = set()
        self._post_task_workspace_names = set()

        try:
            validate(configuration, JOB_CONFIGURATION_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidJobConfiguration(validation_error)

        self._populate_default_values()

        if self._configuration['version'] != CURRENT_VERSION:
            raise InvalidJobConfiguration('%s is an unsupported version number' % self._configuration['version'])
        self._validate_workspace_names()

    def add_job_task_docker_param(self, param):
        """Adds a Docker parameter to this job's job task

        :param param: The Docker parameter to add
        :type param: :class:`job.configuration.configuration.job_configuration.DockerParam`
        """

        self._configuration['job_task']['docker_params'].append({'flag': param.flag, 'value': param.value})

    def add_post_task_docker_param(self, param):
        """Adds a Docker parameter to this job's post task

        :param param: The Docker parameter to add
        :type param: :class:`job.configuration.configuration.job_configuration.DockerParam`
        """

        self._configuration['post_task']['docker_params'].append({'flag': param.flag, 'value': param.value})

    def add_pre_task_docker_param(self, param):
        """Adds a Docker parameter to this job's pre task

        :param param: The Docker parameter to add
        :type param: :class:`job.configuration.configuration.job_configuration.DockerParam`
        """

        self._configuration['pre_task']['docker_params'].append({'flag': param.flag, 'value': param.value})

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
            raise InvalidJobConfiguration('Duplicate workspace %s in job task' % name)
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
            raise InvalidJobConfiguration('Duplicate workspace %s in post task' % name)
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
            raise InvalidJobConfiguration('Duplicate workspace %s in pre task' % name)
        self._configuration['pre_task']['workspaces'].append({'name': name, 'mode': mode})

    def get_job_task_docker_params(self):
        """Returns the Docker parameters needed for the job task

        :returns: The job task Docker parameters
        :rtype: [:class:`job.configuration.configuration.job_configuration.DockerParam`]
        """

        params = []
        for param_dict in self._configuration['job_task']['docker_params']:
            param = DockerParam(param_dict['flag'], param_dict['value'])
            params.append(param)
        return params

    def get_post_task_docker_params(self):
        """Returns the Docker parameters needed for the post task

        :returns: The post task Docker parameters
        :rtype: [:class:`job.configuration.configuration.job_configuration.DockerParam`]
        """

        params = []
        for param_dict in self._configuration['post_task']['docker_params']:
            param = DockerParam(param_dict['flag'], param_dict['value'])
            params.append(param)
        return params

    def get_pre_task_docker_params(self):
        """Returns the Docker parameters needed for the pre task

        :returns: The pre task Docker parameters
        :rtype: [:class:`job.configuration.configuration.job_configuration.DockerParam`]
        """

        params = []
        for param_dict in self._configuration['pre_task']['docker_params']:
            param = DockerParam(param_dict['flag'], param_dict['value'])
            params.append(param)
        return params

    def get_job_task_workspaces(self):
        """Returns the workspaces needed for the job task

        :returns: The job task workspaces
        :rtype: [:class:`job.configuration.configuration.job_configuration.JobWorkspace`]
        """

        workspaces = []
        for workspace_dict in self._configuration['job_task']['workspaces']:
            workspace = JobWorkspace(workspace_dict['name'], workspace_dict['mode'])
            workspaces.append(workspace)
        return workspaces

    def get_post_task_workspaces(self):
        """Returns the workspaces needed for the post task

        :returns: The post task workspaces
        :rtype: [:class:`job.configuration.configuration.job_configuration.JobWorkspace`]
        """

        workspaces = []
        for workspace_dict in self._configuration['post_task']['workspaces']:
            workspace = JobWorkspace(workspace_dict['name'], workspace_dict['mode'])
            workspaces.append(workspace)
        return workspaces

    def get_pre_task_workspaces(self):
        """Returns the workspaces needed for the pre task

        :returns: The pre task workspaces
        :rtype: [:class:`job.configuration.configuration.job_configuration.JobWorkspace`]
        """

        workspaces = []
        for workspace_dict in self._configuration['pre_task']['workspaces']:
            workspace = JobWorkspace(workspace_dict['name'], workspace_dict['mode'])
            workspaces.append(workspace)
        return workspaces

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
            self._configuration['version'] = CURRENT_VERSION

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

        :raises :class:`job.configuration.configuration.exceptions.InvalidJobConfiguration`: If there is a duplicate
            workspace name
        """

        for workspace_dict in self._configuration['pre_task']['workspaces']:
            name = workspace_dict['name']
            if name in self._pre_task_workspace_names:
                raise InvalidJobConfiguration('Duplicate workspace %s in pre task' % name)
            self._pre_task_workspace_names.add(name)
        for workspace_dict in self._configuration['job_task']['workspaces']:
            name = workspace_dict['name']
            if name in self._job_task_workspace_names:
                raise InvalidJobConfiguration('Duplicate workspace %s in job task' % name)
            self._job_task_workspace_names.add(name)
        for workspace_dict in self._configuration['post_task']['workspaces']:
            name = workspace_dict['name']
            if name in self._post_task_workspace_names:
                raise InvalidJobConfiguration('Duplicate workspace %s in post task' % name)
            self._post_task_workspace_names.add(name)
