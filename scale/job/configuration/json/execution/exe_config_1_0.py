"""Defines the JSON schema for describing the job configuration"""
from __future__ import unicode_literals

import logging

from django.conf import settings
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.exceptions import InvalidExecutionConfiguration
from job.configuration.job_parameter import DockerParam, TaskWorkspace
from job.execution.container import get_workspace_volume_name
from storage.container import get_workspace_volume_path


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


class ExecutionConfiguration(object):
    """Represents a job configuration
    """

    def __init__(self, configuration=None):
        """Creates a job configuration from the given JSON dict

        :param configuration: The JSON dictionary
        :type configuration: dict
        :raises :class:`job.configuration.exceptions.InvalidExecutionConfiguration`: If the JSON is invalid
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

    def add_job_task_docker_params(self, params):
        """Adds the given Docker parameters to this job's job task

        :param params: The Docker parameters to add
        :type params: [:class:`job.configuration.job_parameter.DockerParam`]
        """

        for param in params:
            self._configuration['job_task']['docker_params'].append({'flag': param.flag, 'value': param.value})

    def add_post_task_docker_params(self, params):
        """Adds the given Docker parameters to this job's post task

        :param params: The Docker parameters to add
        :type params: [:class:`job.configuration.job_parameter.DockerParam`]
        """

        for param in params:
            self._configuration['post_task']['docker_params'].append({'flag': param.flag, 'value': param.value})

    def add_pre_task_docker_params(self, params):
        """Adds the given Docker parameters to this job's pre task

        :param params: The Docker parameters to add
        :type params: [:class:`job.configuration.job_parameter.DockerParam`]
        """

        for param in params:
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

    def configure_logging_docker_params(self, job_exe):
        """Configures the Docker parameters needed for job execution logging

        :param job_exe: The job execution model (must not be queued) with related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`

        :raises Exception: If the job execution is still queued
        """

        es_urls = None
        # Use connection pool to get up-to-date list of elasticsearch nodes
        if settings.ELASTICSEARCH:
            hosts = [host.host for host in settings.ELASTICSEARCH.transport.connection_pool.connections]
            es_urls = ','.join(hosts)

        if settings.LOGGING_ADDRESS is not None:
            log_driver = DockerParam('log-driver', 'syslog')
            # Must explicitly specify RFC3164 to ensure compatability with logstash in Docker 1.11+
            syslog_format = DockerParam('log-opt', 'syslog-format=rfc3164')
            log_address = DockerParam('log-opt', 'syslog-address=%s' % settings.LOGGING_ADDRESS)
            if not job_exe.is_system:
                pre_task_tag = DockerParam('log-opt', 'tag=%s' % job_exe.get_pre_task_id())
                self.add_pre_task_docker_params([log_driver, syslog_format, log_address, pre_task_tag])
                post_task_tag = DockerParam('log-opt', 'tag=%s' % job_exe.get_post_task_id())
                # Post task needs ElasticSearch URL to grab logs for old artifact registration
                es_urls = DockerParam('env', 'SCALE_ELASTICSEARCH_URLS=%s' % es_urls)
                self.add_post_task_docker_params([log_driver, syslog_format, log_address, post_task_tag, es_urls])
            job_task_tag = DockerParam('log-opt', 'tag=%s' % job_exe.get_job_task_id())
            self.add_job_task_docker_params([log_driver, syslog_format, log_address, job_task_tag])

    def get_job_task_docker_params(self):
        """Returns the Docker parameters needed for the job task

        :returns: The job task Docker parameters
        :rtype: [:class:`job.configuration.job_parameter.DockerParam`]
        """

        params = self._configuration['job_task']['docker_params']
        return [DockerParam(param_dict['flag'], param_dict['value']) for param_dict in params]

    def get_post_task_docker_params(self):
        """Returns the Docker parameters needed for the post task

        :returns: The post task Docker parameters
        :rtype: [:class:`job.configuration.job_parameter.DockerParam`]
        """

        params = self._configuration['post_task']['docker_params']
        return [DockerParam(param_dict['flag'], param_dict['value']) for param_dict in params]

    def get_pre_task_docker_params(self):
        """Returns the Docker parameters needed for the pre task

        :returns: The pre task Docker parameters
        :rtype: [:class:`job.configuration.job_parameter.DockerParam`]
        """

        params = self._configuration['pre_task']['docker_params']
        return [DockerParam(param_dict['flag'], param_dict['value']) for param_dict in params]

    def get_job_task_workspaces(self):
        """Returns the workspaces needed for the job task

        :returns: The job task workspaces
        :rtype: [:class:`job.configuration.job_parameter.TaskWorkspace`]
        """

        workspaces = self._configuration['job_task']['workspaces']
        return [TaskWorkspace(workspace_dict['name'], workspace_dict['mode']) for workspace_dict in workspaces]

    def get_post_task_workspaces(self):
        """Returns the workspaces needed for the post task

        :returns: The post task workspaces
        :rtype: [:class:`job.configuration.job_parameter.TaskWorkspace`]
        """

        workspaces = self._configuration['post_task']['workspaces']
        return [TaskWorkspace(workspace_dict['name'], workspace_dict['mode']) for workspace_dict in workspaces]

    def get_pre_task_workspaces(self):
        """Returns the workspaces needed for the pre task

        :returns: The pre task workspaces
        :rtype: [:class:`job.configuration.job_parameter.TaskWorkspace`]
        """

        workspaces = self._configuration['pre_task']['workspaces']
        return [TaskWorkspace(workspace_dict['name'], workspace_dict['mode']) for workspace_dict in workspaces]

    def get_dict(self):
        """Returns the internal dictionary that represents this job configuration

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration

    def _get_workspace_docker_params(self, job_exe, task_workspaces, workspaces, volume_create, docker_volumes):
        """Returns the Docker parameters needed for the given task workspaces

        :param job_exe: The job execution model (must not be queued) with related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        :param task_workspaces: List of the task workspaces
        :type task_workspaces: [:class:`job.configuration.job_parameter.TaskWorkspace`]
        :param workspaces: A dict of all workspaces stored by name
        :type workspaces: {string: :class:`storage.models.Workspace`}
        :param volume_create: Indicates if new volumes need to be created for these workspaces
        :type volume_create: bool
        :param docker_volumes: A list to add Docker volume names to
        :type docker_volumes: [string]
        :returns: The Docker parameters needed by the given workspaces
        :rtype: [:class:`job.configuration.job_parameter.DockerParam`]

        :raises Exception: If the job execution is still queued
        """

        params = []
        for task_workspace in task_workspaces:
            name = task_workspace.name
            mode = task_workspace.mode
            if name in workspaces:
                workspace = workspaces[name]
                if workspace.volume:
                    vol = workspace.volume
                    if vol.host:
                        # Host mount is special, no volume name, just the host mount path
                        volume_name = vol.remote_path
                    elif volume_create:
                        # Create job_exe workspace volume for first time
                        volume_create_cmd = '$(docker volume create --driver=%s --name=%s %s)'
                        volume_name = get_workspace_volume_name(job_exe, name)
                        docker_volumes.append(volume_name)
                        volume_name = volume_create_cmd % (vol.driver, volume_name, vol.remote_path)
                    else:
                        # Volume already created, re-use name
                        volume_name = get_workspace_volume_name(job_exe, name)
                    workspace_volume = '%s:%s:%s' % (volume_name, get_workspace_volume_path(name), mode)
                    params.append(DockerParam('volume', workspace_volume))
        return params

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

        :raises :class:`job.configuration.exceptions.InvalidExecutionConfiguration`: If there is a duplicate
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
