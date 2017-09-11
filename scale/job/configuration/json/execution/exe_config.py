"""Defines the JSON schema for describing the execution configuration"""
from __future__ import unicode_literals

import logging
from copy import deepcopy

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.docker_param import DockerParameter
from job.configuration.exceptions import InvalidExecutionConfiguration
from job.configuration.json.execution import exe_config_1_1 as previous_version
from job.configuration.volume import Volume, MODE_RO, MODE_RW
from job.configuration.workspace import TaskWorkspace
from node.resources.node_resources import NodeResources
from node.resources.resource import ScalarResource

logger = logging.getLogger(__name__)


SCHEMA_VERSION = '2.0'


EXE_CONFIG_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the execution configuration schema',
            'type': 'string',
            'pattern': '^.{0,50}$',
        },
        'input_files': {
            'description': 'The input files and meta-data for this job execution',
            'type': 'object',
            'additionalProperties': {
                'type': 'array',
                'items': {
                    '$ref': '#/definitions/input_file',
                },
            },
        },
        'output_workspaces': {
            'description': 'The output parameters each mapped to their output workspace',
            'type': 'object',
            'additionalProperties': {
                'type': 'string',
            },
        },
        'tasks': {
            'description': 'The execution configuration for each task',
            'type': 'array',
            'items': {
                '$ref': '#/definitions/task',
            },
        },
    },
    'definitions': {
        'input_file': {
            'type': 'object',
            'required': ['id', 'type', 'workspace_name', 'workspace_path', 'is_deleted'],
            'additionalProperties': False,
            'properties': {
                'id': {
                    'type': 'integer',
                },
                'type': {
                    'type': 'string',
                    'enum': ['SOURCE', 'PRODUCT'],
                },
                'workspace_name': {
                    'type': 'string',
                },
                'workspace_path': {
                    'type': 'string',
                },
                'local_file_name': {
                    'type': 'string',
                },
                'is_deleted': {
                    'type': 'boolean',
                },
            },
        },
        'task': {
            'type': 'object',
            'required': ['type', 'args'],
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
                'resources': {
                    'description': 'The resources allocated to the task',
                    'type': 'object',
                    'additionalProperties': {
                        'type': 'number',
                    },
                },
                'args': {
                    'description': 'The command argument string for this task',
                    'type': 'string',
                },
                'env_vars': {
                    'description': 'The environment variables for this task',
                    'type': 'object',
                    'additionalProperties': {
                        'type': 'string',
                    },
                },
                'workspaces': {
                    'description': 'The workspaces available to this task',
                    'type': 'object',
                    'additionalProperties': {
                        '$ref': '#/definitions/workspace'
                    },
                },
                'mounts': {
                    'description': 'The mounts for this task',
                    'type': 'object',
                    'additionalProperties': {
                        'anyOf': [
                            {'type': 'string'},
                            {'type': 'null'}
                        ],
                    },
                },
                'settings': {
                    'description': 'The settings for this task',
                    'type': 'object',
                    'additionalProperties': {
                        'anyOf': [
                            {'type': 'string'},
                            {'type': 'null'}
                        ],
                    },
                },
                'volumes': {
                    'description': 'The workspaces available to this task',
                    'type': 'object',
                    'additionalProperties': {
                        '$ref': '#/definitions/volume'
                    },
                },
                'docker_params': {
                    'description': 'The Docker parameters that will be set for this task',
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/docker_param',
                    },
                },
            },
        },
        'workspace': {
            'type': 'object',
            'required': ['mode'],
            'additionalProperties': False,
            'properties': {
                'volume_name': {
                    'type': 'string',
                },
                'mode': {
                    'type': 'string',
                    'enum': [MODE_RO, MODE_RW],
                },
            },
        },
        'volume': {
            'type': 'object',
            'required': ['container_path', 'mode', 'type'],
            'additionalProperties': False,
            'properties': {
                'container_path': {
                    'type': 'string',
                },
                'mode': {
                    'type': 'string',
                    'enum': [MODE_RO, MODE_RW],
                },
                'type': {
                    'type': 'string',
                    'enum': ['host', 'volume'],
                },
                'host_path': {
                    'type': 'string',
                },
                'driver': {
                    'type': 'string',
                },
                'driver_opts': {
                    'type': 'object',
                    'additionalProperties': {
                        'type': 'string',
                    },
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
    """Represents a job execution configuration
    """

    def __init__(self, configuration=None, do_validate=True):
        """Creates an execution configuration from the given JSON dict

        :param configuration: The JSON dictionary
        :type configuration: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`job.configuration.exceptions.InvalidExecutionConfiguration`: If the JSON is invalid
        """

        if not configuration:
            configuration = {}
        self._configuration = configuration

        if 'version' not in self._configuration:
            self._configuration['version'] = SCHEMA_VERSION

        if self._configuration['version'] != SCHEMA_VERSION:
            self._configuration = ExecutionConfiguration._convert_configuration(configuration)

        self._populate_default_values()

        try:
            if do_validate:
                validate(configuration, EXE_CONFIG_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidExecutionConfiguration(validation_error)

    def add_to_task(self, task_type, args=None, docker_params=None, env_vars=None, mount_volumes=None, resources=None,
                    settings=None, wksp_volumes=None, workspaces=None):
        """Adds the given parameters to the task with the given type. The task with the given type must already exist. A
        mount volume of None indicates a required mount that is missing. A setting value of None indicates a required
        setting that is missing.

        :param task_type: The task type to add the parameters to
        :type task_type: string
        :param args: The command arguments for the task
        :type args: string
        :param docker_params: The Docker parameters
        :type docker_params: list
        :param env_vars: A dict of env var names and values to add to the task
        :type env_vars: dict
        :param mount_volumes: The mount volumes stored by mount name (a volume may be None)
        :type mount_volumes: dict
        :param resources: The resources
        :type resources: :class:`node.resources.node_resources.NodeResources`
        :param settings: The setting names and values (a value may be None)
        :type settings: dict
        :param wksp_volumes: The workspace volumes stored by workspace name
        :type wksp_volumes: dict
        :param workspaces: The workspaces stored by name
        :type workspaces: dict
        """

        task_dict = self._get_task_dict(task_type)
        if args:
            ExecutionConfiguration._add_args_to_task(task_dict, args)
        if docker_params:
            ExecutionConfiguration._add_docker_params_to_task(task_dict, docker_params)
        if env_vars:
            ExecutionConfiguration._add_env_vars_to_task(task_dict, env_vars)
        if mount_volumes:
            ExecutionConfiguration._add_mount_volumes_to_task(task_dict, mount_volumes)
        if resources:
            ExecutionConfiguration._add_resources_to_task(task_dict, resources)
        if settings:
            ExecutionConfiguration._add_settings_to_task(task_dict, settings)
        if wksp_volumes:
            ExecutionConfiguration._add_workspace_volumes_to_task(task_dict, wksp_volumes)
        if workspaces:
            ExecutionConfiguration._add_workspaces_to_task(task_dict, workspaces)

    def create_copy(self):
        """Creates and returns a copy of this configuration

        :returns: The copied configuration
        :rtype: :class:`job.configuration.json.execution.exe_config.ExecutionConfiguration`
        """

        return ExecutionConfiguration(deepcopy(self._configuration), do_validate=False)

    def create_tasks(self, task_types):
        """Makes sure that tasks with the given types are created and in the given order. If an already existing task
        type is not included in the given list, it will be removed.

        :param task_types: The list of task types
        :type task_types: list
        """

        tasks_by_type = {}
        for task_dict in self._configuration['tasks']:
            tasks_by_type[task_dict['type']] = task_dict

        tasks = []
        for task_type in task_types:
            if task_type in tasks_by_type:
                tasks.append(tasks_by_type[task_type])
                del tasks_by_type[task_type]
            else:
                tasks.append(ExecutionConfiguration._create_task(task_type))
        self._configuration['tasks'] = tasks

    def get_args(self, task_type):
        """Returns the command arguments for the given task type, None if the task type doesn't exist

        :param task_type: The task type
        :type task_type: string
        :returns: The command arguments, possibly None
        :rtype: string
        """

        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type:
                return task_dict['args']
        return None

    def get_dict(self):
        """Returns the internal dictionary that represents this execution configuration

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration

    def get_docker_params(self, task_type):
        """Returns the Docker parameters for the given task type

        :param task_type: The task type
        :type task_type: string
        :returns: The list of Docker parameters
        :rtype: list
        """

        params = []
        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type:
                if 'docker_params' in task_dict:
                    for param_dict in task_dict['docker_params']:
                        params.append(DockerParameter(param_dict['flag'], param_dict['value']))
        return params

    def get_env_vars(self, task_type):
        """Returns the environment variables for the given task type

        :param task_type: The task type
        :type task_type: string
        :returns: The dict of environment variables
        :rtype: dict
        """

        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type:
                if 'env_vars' in task_dict:
                    return task_dict['env_vars']
        return {}

    def get_input_workspace_names(self):
        """Returns a list of the names of all input workspaces

        :returns: The list of the names of all input workspaces
        :rtype: list
        """

        workspace_names = set()
        if 'input_files' in self._configuration:
            for file_list in self._configuration['input_files'].values():
                for file_dict in file_list:
                    workspace_names.add(file_dict['workspace_name'])
        return list(workspace_names)

    def get_mounts(self, task_type):
        """Returns the mounts for the given task type

        :param task_type: The task type
        :type task_type: string
        :returns: The dict of mount names mapping to volume names
        :rtype: dict
        """

        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type:
                if 'mounts' in task_dict:
                    return task_dict['mounts']
        return {}

    def get_named_docker_volumes(self):
        """Returns the names of all (non-host) Docker volumes

        :returns: The list of all named Docker volumes
        :rtype: list
        """

        volumes = set()
        for task_dict in self._configuration['tasks']:
            if 'volumes' in task_dict:
                for name, vol_dict in task_dict['volumes'].items():
                    if vol_dict['type'] == 'volume':
                        volumes.add(name)
        return list(volumes)

    def get_output_workspace_names(self):
        """Returns a list of the names of all output workspaces

        :returns: The list of the names of all output workspaces
        :rtype: list
        """

        if 'output_workspaces' in self._configuration:
            return list(self._configuration['output_workspaces'].values())
        return []

    def get_resources(self, task_type):
        """Returns the resources for the given task type, None if the task type doesn't exist

        :param task_type: The task type
        :type task_type: string
        :returns: The task resources, possibly None
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type and 'resources' in task_dict:
                resources = []
                for name, value in task_dict['resources'].items():
                    resources.append(ScalarResource(name, value))
                return NodeResources(resources)
        return None

    def get_settings(self, task_type):
        """Returns the settings for the given task type

        :param task_type: The task type
        :type task_type: string
        :returns: The dict of settings
        :rtype: dict
        """

        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type:
                if 'settings' in task_dict:
                    return task_dict['settings']
        return {}

    def get_task_id(self, task_type):
        """Returns the task ID for the given task type, None if the task type doesn't exist

        :param task_type: The task type
        :type task_type: string
        :returns: The task ID, possibly None
        :rtype: string
        """

        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type and 'task_id' in task_dict:
                return task_dict['task_id']
        return None

    def get_task_types(self):
        """Returns all task types in the configuration in order

        :returns: The ordered list of task types
        :rtype: list
        """

        task_types = []
        for task_dict in self._configuration['tasks']:
            task_types.append(task_dict['type'])
        return task_types

    def get_volumes(self, task_type):
        """Returns the Docker volumes for the given task type

        :param task_type: The task type
        :type task_type: string
        :returns: The dict of Docker volumes stored by volume name
        :rtype: dict
        """

        volumes = {}
        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type:
                if 'volumes' in task_dict:
                    for name, vol_dict in task_dict['volumes'].items():
                        if vol_dict['type'] == 'host':
                            vol = Volume(name, vol_dict['container_path'], vol_dict['mode'], is_host=True,
                                         host_path=vol_dict['host_path'])
                        else:
                            driver = None
                            driver_opts = None
                            if 'driver' in vol_dict:
                                driver = vol_dict['driver']
                            if 'driver_opts' in vol_dict:
                                driver_opts = vol_dict['driver_opts']
                            vol = Volume(name, vol_dict['container_path'], vol_dict['mode'], is_host=False,
                                         driver=driver, driver_opts=driver_opts)
                        volumes[name] = vol
        return volumes

    def get_workspaces(self, task_type):
        """Returns the workspaces for the given task type

        :param task_type: The task type
        :type task_type: string
        :returns: The list of workspaces
        :rtype: list
        """

        workspaces = []
        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type:
                if 'workspaces' in task_dict:
                    for name, workspace_dict in task_dict['workspaces'].items():
                        workspaces.append(TaskWorkspace(name, workspace_dict['mode']))
        return workspaces

    def set_input_files(self, input_files):
        """Sets the given input files in the configuration

        :param input_files: A dict where data input name maps to a list of input files
        :type input_files: dict
        """

        files_dict = {}

        for input_name in input_files:
            file_list = []
            for input_file in input_files[input_name]:
                file_dict = {'id': input_file.id, 'type': input_file.file_type,
                             'workspace_name': input_file.workspace_name, 'workspace_path': input_file.workspace_path,
                             'is_deleted': input_file.is_deleted}
                if input_file.local_file_name:
                    file_dict['local_file_name'] = input_file.local_file_name
                file_list.append(file_dict)
            files_dict[input_name] = file_list

        if files_dict:
            self._configuration['input_files'] = files_dict

    def set_output_workspaces(self, output_workspaces):
        """Sets the given output workspaces in the configuration

        :param output_workspaces: A dict where job output parameters map to output workspace name
        :type output_workspaces: dict
        """

        if output_workspaces:
            self._configuration['output_workspaces'] = output_workspaces

    def set_task_ids(self, cluster_id):
        """Sets the IDs for all of the tasks

        :param cluster_id: The cluster ID for the job execution
        :type cluster_id: string
        """

        for task_dict in self._configuration['tasks']:
            task_dict['task_id'] = '%s_%s' % (cluster_id, task_dict['type'])

    @staticmethod
    def _add_args_to_task(task_dict, args):
        """Adds the given command arguments to the given task

        :param task_dict: The task dict
        :type task_dict: dict
        :param args: The command arguments
        :type args: string
        """

        task_dict['args'] = args

    @staticmethod
    def _add_docker_params_to_task(task_dict, docker_params):
        """Adds the given Docker parameters to the given task

        :param task_dict: The task dict
        :type task_dict: dict
        :param docker_params: The Docker parameters
        :type docker_params: list
        """

        if 'docker_params' in task_dict:
            task_docker_params = task_dict['docker_params']
        else:
            task_docker_params = []
            task_dict['docker_params'] = task_docker_params

        for param in docker_params:
            task_docker_params.append({'flag': param.flag, 'value': param.value})

    @staticmethod
    def _add_env_vars_to_task(task_dict, env_vars):
        """Adds the given environment variables to the given task

        :param task_dict: The task dict
        :type task_dict: dict
        :param env_vars: The environment variables
        :type env_vars: dict
        """

        if 'env_vars' in task_dict:
            task_env_vars = task_dict['env_vars']
        else:
            task_env_vars = {}
            task_dict['env_vars'] = task_env_vars

        for name, value in env_vars.items():
            task_env_vars[name] = value

    @staticmethod
    def _add_mount_volumes_to_task(task_dict, mount_volumes):
        """Adds the given mount volumes to the given task. A mount volume of None indicates a required mount that is
        missing.

        :param task_dict: The task dict
        :type task_dict: dict
        :param mount_volumes: The mount volumes stored by mount name (a volume may be None)
        :type mount_volumes: dict
        """

        if 'mounts' in task_dict:
            task_mounts = task_dict['mounts']
        else:
            task_mounts = {}
            task_dict['mounts'] = task_mounts

        volumes = []
        for mount_name, volume in mount_volumes.items():
            if volume:
                task_mounts[mount_name] = volume.name
                volumes.append(volume)
            else:
                task_mounts[mount_name] = None
        ExecutionConfiguration._add_volumes_to_task(task_dict, volumes)

    @staticmethod
    def _add_resources_to_task(task_dict, resources):
        """Adds the given resources to the given task

        :param task_dict: The task dict
        :type task_dict: dict
        :param resources: The resources
        :type resources: :class:`node.resources.node_resources.NodeResources`
        """

        resources_dict = {}
        for resource in resources.resources:
            resources_dict[resource.name] = resource.value  # Assumes scalar resource
        task_dict['resources'] = resources_dict

    @staticmethod
    def _add_settings_to_task(task_dict, settings):
        """Adds the given settings to the given task. A setting value of None indicates a required setting that is
        missing.

        :param task_dict: The task dict
        :type task_dict: dict
        :param settings: The setting names and values (a value may be None)
        :type settings: dict
        """

        if 'settings' in task_dict:
            task_settings = task_dict['settings']
        else:
            task_settings = {}
            task_dict['settings'] = task_settings

        for name, value in settings.items():
            task_settings[name] = value

    @staticmethod
    def _add_volumes_to_task(task_dict, volumes):
        """Adds the given volumes to the given task

        :param task_dict: The task dict
        :type task_dict: dict
        :param volumes: The list of volumes
        :type volumes: list
        """

        if not volumes:
            return

        if 'volumes' in task_dict:
            task_volumes = task_dict['volumes']
        else:
            task_volumes = {}
            task_dict['volumes'] = task_volumes

        for volume in volumes:
            if volume.is_host:
                vol_dict = {'container_path': volume.container_path, 'mode': volume.mode, 'type': 'host',
                            'host_path': volume.host_path}
            else:
                vol_dict = {'container_path': volume.container_path, 'mode': volume.mode, 'type': 'volume'}
                if volume.driver:
                    vol_dict['driver'] = volume.driver
                if volume.driver_opts:
                    vol_dict['driver_opts'] = volume.driver_opts
            task_volumes[volume.name] = vol_dict

    @staticmethod
    def _add_workspace_volumes_to_task(task_dict, wksp_volumes):
        """Adds the given workspace volumes to the given task

        :param task_dict: The task dict
        :type task_dict: dict
        :param wksp_volumes: The workspace volumes stored by workspace name
        :type wksp_volumes: dict
        """

        if 'workspaces' in task_dict:
            task_workspaces = task_dict['workspaces']
        else:
            task_workspaces = {}
            task_dict['workspaces'] = task_workspaces

        for name, volume in wksp_volumes.items():
            wksp_dict = {'mode': volume.mode}
            if volume.name:
                wksp_dict['volume_name'] = volume.name
            task_workspaces[name] = wksp_dict
        ExecutionConfiguration._add_volumes_to_task(task_dict, wksp_volumes.values())

    @staticmethod
    def _add_workspaces_to_task(task_dict, workspaces):
        """Adds the given workspaces to the given task

        :param task_dict: The task dict
        :type task_dict: dict
        :param workspaces: The workspaces stored by name
        :type workspaces: dict
        """

        if 'workspaces' in task_dict:
            task_workspaces = task_dict['workspaces']
        else:
            task_workspaces = {}
            task_dict['workspaces'] = task_workspaces

        for workspace in workspaces.values():
            if workspace.name in task_workspaces:
                # Only replace existing workspace if upgrading mode from RO to RW
                existing_workspace = task_workspaces[workspace.name]
                if existing_workspace['mode'] == MODE_RW or workspace.mode == MODE_RO:
                    continue
            workspace_dict = {'mode': workspace.mode}
            if workspace.volume_name:
                workspace_dict['volume_name'] = workspace.volume_name
            task_workspaces[workspace.name] = workspace_dict

    @staticmethod
    def _convert_configuration(configuration):
        """Converts the given execution configuration to the 2.0 schema

        :param configuration: The previous configuration
        :type configuration: dict
        :return: The converted configuration
        :rtype: dict
        """

        previous = previous_version.ExecutionConfiguration(configuration)

        converted = previous.get_dict()

        converted['version'] = SCHEMA_VERSION

        ExecutionConfiguration._convert_configuration_task(converted, 'pre', 'pre_task')
        ExecutionConfiguration._convert_configuration_task(converted, 'main', 'job_task')
        ExecutionConfiguration._convert_configuration_task(converted, 'post', 'post_task')

        return converted

    @staticmethod
    def _convert_configuration_task(configuration, task_type, old_task_name):
        """Converts the given task in the configuration

        :param configuration: The configuration to convert
        :type configuration: dict
        :param task_type: The type of the task
        :type task_type: string
        :param old_task_name: The old task name
        :type old_task_name: string
        """

        if old_task_name not in configuration:
            return

        old_task_dict = configuration[old_task_name]
        new_task_dict = {"task_id": old_task_name, "type": task_type, "args": ""}

        if 'workspaces' in old_task_dict:
            new_workspace_dict = {}
            new_task_dict['workspaces'] = new_workspace_dict
            for old_workspace in old_task_dict['workspaces']:
                name = old_workspace['name']
                mode = old_workspace['mode']
                new_workspace_dict[name] = {'mode': mode, 'volume_name': 'wksp_%s' % name}

        if 'settings' in old_task_dict:
            new_settings_dict = {}
            new_task_dict['settings'] = new_settings_dict
            for old_setting in old_task_dict['settings']:
                name = old_setting['name']
                value = old_setting['value']
                new_settings_dict[name] = value

        if 'docker_params' in old_task_dict:
            new_params_list = []
            new_task_dict['docker_params'] = new_params_list
            for old_param in old_task_dict['docker_params']:
                new_params_list.append(old_param)

        if 'tasks' not in configuration:
            configuration['tasks'] = []
        configuration['tasks'].append(new_task_dict)
        del configuration[old_task_name]

    @staticmethod
    def _create_task(task_type):
        """Creates a new task with the given type

        :param task_type: The task type
        :type task_type: string
        :return: The task dict
        :rtype: dict
        """

        return {'type': task_type, 'args': ''}

    def _get_task_dict(self, task_type):
        """Returns the dict for the task with the given type, if it exists

        :param task_type: The task type
        :type task_type: string
        :return: The task dict, possibly None
        :rtype: dict
        """

        for task_dict in self._configuration['tasks']:
            if task_dict['type'] == task_type:
                return task_dict
        return None

    def _populate_default_values(self):
        """Populates any missing JSON fields that have default values
        """

        if 'tasks' not in self._configuration:
            self._configuration['tasks'] = []
