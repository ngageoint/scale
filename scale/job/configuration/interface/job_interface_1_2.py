"""Defines the interface for executing a job"""
from __future__ import unicode_literals

import logging
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.interface import job_interface_1_1 as previous_interface
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.configuration.exceptions import MissingSetting


logger = logging.getLogger(__name__)

SCHEMA_VERSION = '1.2'

JOB_INTERFACE_SCHEMA = {
    'type': 'object',
    'required': ['command', 'command_arguments'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'version of the job_interface schema',
            "default": SCHEMA_VERSION,
            "type": "string"
        },
        'command': {
            'description': 'The command that will be called.  Uses variable replacement',
            'type': 'string',
        },
        'command_arguments': {
            'description': 'The arguments that are passed to the command',
            'type': 'string',
        },
        'env_vars': {
            'description': 'Environment variables that will be made available at runtime',
            'type': 'array',
            'items': {
                '$ref': '#/definitions/env_var',
            },
        },
        'settings': {
            'description': 'Job settings that will be in command call',
            'type': 'array',
            'items': {
                '$ref': '#/definitions/setting',
            },
        },
        'input_data': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/input_data_item',
            },
        },
        'output_data': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/output_data_item',
            },
        },
        'shared_resources': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/shared_resource',
            },
        },
    },
    'definitions': {
        'env_var': {
            'type': 'object',
            'required': ['name', 'value'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                },
                'value': {
                    'type': 'string',
                },
            },
        },
        'setting': {
            'type': 'object',
            'required': ['name'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                },
                'required': {
                    'type': 'boolean',
                },
            },
        },
        'input_data_item': {
            'type': 'object',
            'required': ['name', 'type'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z0-9\\-_ ]{1,255}$',
                },
                'type': {
                    'type': 'string',
                    'enum': ['file', 'files', 'property'],
                },
                'required': {
                    'type': 'boolean',
                },
                'partial': {
                    'description': 'file/files type only flag indicating input may be mounted vs downloaded',
                    'type': 'boolean'
                },
                'media_types': {
                    'type': 'array',
                },
            },
        },
        'output_data_item': {
            'type': 'object',
            'required': ['name', 'type'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                    'pattern': '^[a-zA-Z0-9\\-_ ]{1,255}$',
                },
                'type': {
                    'type': 'string',
                    'enum': ['file', 'files'],
                },
                'required': {
                    'type': 'boolean',
                },
                'media_type': {
                    'type': 'string',
                },
            },
        },
        'shared_resource': {
            'type': 'object',
            'required': ['name', 'type'],
            'additionalProperties': False,
            'properties': {
                'name': {
                    'type': 'string',
                },
                'type': {
                    'type': 'string',
                },
                'required': {
                    'type': 'boolean',
                },
            },
        },
    },
}


class JobInterface(previous_interface.JobInterface):
    """Represents the interface for executing a job"""

    def __init__(self, definition):
        """Creates a job interface from the given definition. If the definition is invalid, a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` exception will be thrown.

        :param definition: The interface definition
        :type definition: dict
        """
        self.definition = definition
        self._param_names = set()

        # Tuples used for validation with other classes
        self._property_validation_dict = {}  # str->bool
        self._input_file_validation_dict = {}  # str->tuple
        self._output_file_validation_list = []

        self._output_file_manifest_dict = {}  # str->bool

        if 'version' not in self.definition:
            self.definition['version'] = SCHEMA_VERSION

        if self.definition['version'] != SCHEMA_VERSION:
            self.convert_interface(definition)

        try:
            validate(definition, JOB_INTERFACE_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidInterfaceDefinition(validation_error)

        self._populate_default_values()
        self._populate_settings_defaults()
        self._populate_env_vars_defaults()

        self._check_param_name_uniqueness()
        self._check_setting_name_uniqueness()
        self._check_env_var_uniqueness()
        self._validate_command_arguments()
        self._create_validation_dicts()

    @staticmethod
    def convert_interface(interface):
        """Convert the previous Job interface schema to the 1.2 schema

        :param interface: The previous interface
        :type interface: dict
        :return: converted interface
        :rtype: dict
        """
        previous = previous_interface.JobInterface(interface)

        converted = previous.get_dict()

        converted['version'] = SCHEMA_VERSION

        if 'env_vars' not in converted:
            converted['env_vars'] = []

        if 'settings' not in converted:
            converted['settings'] = []

        return converted

    def _populate_settings_defaults(self):
        """populates the default values for any missing settings values"""

        if 'settings' not in self.definition:
            self.definition['settings'] = []

        for setting in self.definition['settings']:
            if 'required' not in setting:
                setting['required'] = True

    def _populate_env_vars_defaults(self):
        """populates the default values for any missing environment variable values"""

        if 'env_vars' not in self.definition:
            self.definition['env_vars'] = []

        for env_var in self.definition['env_vars']:
            if 'value' not in env_var:
                env_var['value'] = ""

    def populate_command_argument_settings(self, command_arguments, job_configuration):
        """Return the command arguments string,
        populated with the settings from the job_configuration.

        :param command_arguments: The command_arguments that you want to perform the replacement on
        :type command_arguments: string
        :param job_configuration: The job configuration
        :type job_configuration: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        :return: command arguments with the settings populated
        :rtype: str
        """

        config_settings = job_configuration.get_dict()
        interface_settings = self.definition['settings']

        param_replacements = self._get_settings_values(interface_settings,
                                                       config_settings)

        command_arguments = self._replace_command_parameters(command_arguments, param_replacements)

        return command_arguments

    def populate_env_vars_arguments(self, job_configuration):
        """Populates the environment variables with the requested values.

        :param job_configuration: The job configuration
        :type job_configuration: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`

        :return: env_vars populated with values
        :rtype: dict
        """

        env_vars = self.definition['env_vars']
        config_settings = job_configuration.get_dict()
        interface_settings = self.definition['settings']

        param_replacements = self._get_settings_values(interface_settings,
                                                       config_settings)
        env_vars = self._replace_env_var_parameters(env_vars, param_replacements)

        return env_vars

    def _get_settings_values(self, settings, config_settings):
        """
        :param settings: The job configuration
        :type settings: JSON
        :param config_settings: The job configuration
        :type config_settings: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        :return: settings name and the value to replace it with
        :rtype: dict
        """

        param_replacements = {}

        # Isolate the job_type settings and convert to list
        config_settings = config_settings['job_task']['settings']
        config_settings_dict = {setting['name']: setting['value'] for setting in config_settings}

        for setting in settings:
            setting_name = setting['name']
            setting_required = setting['required']

            if setting_name in config_settings_dict:
                param_replacements[setting_name] = config_settings_dict[setting_name]
            else:
                param_replacements[setting_name] = ''

        return param_replacements

    def _replace_env_var_parameters(self, env_vars, param_replacements):
        """find all occurrences of a parameter with a given name in the environment
        variable strings and replace them with the param values. If the parameter
        replacement string in the variable uses a custom output ( ${-f :foo}).
        The parameter will be replaced with the string preceding the colon and the
        given param value will be appended.

        :param env_vars: The environment variables that you want to perform replacement on
        :type env_vars: list
        :param param_replacements: The parameter you are searching for
        :type param_replacements: dict
        :return: The string with all replacements made
        :rtype: str
        """

        for env_var in env_vars:
            ret_str = env_var['value']
            for param_name, param_value in param_replacements.iteritems():
                param_pattern = '\$\{([^\}]*\:)?' + re.escape(param_name) + '\}'
                pattern_prog = re.compile(param_pattern)

                match_obj = pattern_prog.search(ret_str)
                if match_obj:
                    ret_str = param_value
                    break

            if ret_str == env_var['value']:
                env_var['value'] = ''
            else:
                env_var['value'] = ret_str

        return env_vars

    def _check_setting_name_uniqueness(self):
        """Ensures all the settings names are unique, and throws a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` if they are not unique
        """

        for setting in self.definition['settings']:
            if setting['name'] in self._param_names:
                raise InvalidInterfaceDefinition('Setting names must be unique')
            self._param_names.add(setting['name'])

    def _check_env_var_uniqueness(self):
        """Ensures all the enviornmental variable names are unique, and throws a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` if they are not unique
        """

        env_vars = [env_var['name'] for env_var in self.definition['env_vars']]

        if len(env_vars) != len(set(env_vars)):
            raise InvalidInterfaceDefinition('Environment variable names must be unique')

    def validate_populated_settings(self, job_exe, job_configuration):
        """Ensures that all required settings are defined in the job_configuration

        :param job_exe: The job execution model with related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        :param job_configuration: The job configuration
        :type job_configuration: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        """

        interface_settings = self.definition['settings']
        config_setting_names = [setting.name for setting in job_configuration.get_job_task_settings()]

        for setting in interface_settings:
            setting_name = setting['name']
            setting_required = setting['required']

            if setting_required:
                if setting_name not in config_setting_names:
                    raise MissingSetting('Required setting %s was not provided' % setting_name)
