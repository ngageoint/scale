"""Defines the interface for executing a job"""
from __future__ import unicode_literals

import json
import logging
import os
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.data.exceptions import InvalidData, InvalidConnection
from job.configuration.interface import job_interface_1_2 as previous_interface
from job.configuration.interface.exceptions import InvalidInterfaceDefinition, InvalidSetting
from job.configuration.interface.scale_file import ScaleFileDescription
from job.configuration.results.exceptions import InvalidResultsManifest
from job.configuration.results.results_manifest.results_manifest import ResultsManifest
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH



logger = logging.getLogger(__name__)

SCHEMA_VERSION = '1.3'

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
                'secret': {
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


class JobInterface(object):
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

        self._check_env_var_uniqueness()
        self._check_param_name_uniqueness()
        self._check_setting_name_uniqueness()

        self._validate_command_arguments()
        self._create_validation_dicts()

    def add_output_to_connection(self, output_name, job_conn, input_name):
        """Adds the given output from the interface as a new input to the given job connection

        :param output_name: The name of the output to add to the connection
        :type output_name: str
        :param job_conn: The job connection
        :type job_conn: :class:`job.configuration.data.job_connection.JobConnection`
        :param input_name: The name of the connection input
        :type input_name: str
        """

        output_data = self._get_output_data_item_by_name(output_name)
        if output_data:
            output_type = output_data['type']
            if output_type in ['file', 'files']:
                multiple = (output_type == 'files')
                optional = not output_data['required']
                media_types = []
                if 'media_type' in output_data and output_data['media_type']:
                    media_types.append(output_data['media_type'])
                # TODO: How do we want to handle down-stream partial handling? Setting to False presently
                job_conn.add_input_file(input_name, multiple, media_types, optional, False)

    def add_workspace_to_data(self, job_data, workspace_id):
        """Adds the given workspace ID to the given job data for every output in this job interface

        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param workspace_id: The workspace ID
        :type workspace_id: int
        """

        for file_output_name in self.get_file_output_names():
            job_data.add_output(file_output_name, workspace_id)

    @staticmethod
    def convert_interface(interface):
        """Convert a previous Job interface schema to the 1.3 schema

        :param interface: The previous interface
        :type interface: dict
        :return: converted interface
        :rtype: dict
        """
        previous = previous_interface.JobInterface(interface)

        converted = previous.get_dict()

        converted['version'] = SCHEMA_VERSION

        for setting in converted['settings']:
            if 'secret' not in setting:
                setting['secret'] = False

        return converted

    def fully_populate_command_argument(self, job_data, job_environment, job_exe_id):
        """Return a fully populated command arguments string. If pre-steps are necessary
        (see are_pre_steps_needed), they should be run before this.  populated with information
        from the job_data, job_environment, job_input_dir, and job_output_dir.This gets the properties and
        input_files from the job_data, the shared_resources from the job_environment, and ${input}
        ${output_dir} from the work_dir.
        Throws a :class:`job.configuration.interface.exceptions.InvalidEnvironment` if the necessary
        pre-steps have not been performed

        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param job_environment: The job environment
        :type job_environment: :class:`job.configuration.environment.job_environment.JobEnvironment`
        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        """
        # TODO: don't ignore job_envirnoment
        command_arguments = self.populate_command_argument_properties(job_data)
        param_replacements = {}

        for input_data in self.definition['input_data']:
            input_name = input_data['name']
            input_type = input_data['type']
            input_required = input_data['required']
            if input_type == 'file':
                param_dir = os.path.join(SCALE_JOB_EXE_INPUT_PATH, input_name)
                if os.path.isdir(param_dir):
                    file_path = self._get_one_file_from_directory(param_dir)
                    param_replacements[input_name] = file_path
                elif input_required:
                    raise InvalidData('Unable to create run command. Expected required file in %s' % param_dir)
                else:
                    param_replacements[input_name] = ''

            elif input_type == 'files':
                param_dir = os.path.join(SCALE_JOB_EXE_INPUT_PATH, input_name)
                if os.path.isdir(param_dir):
                    param_replacements[input_name] = param_dir
                elif input_required:
                    raise InvalidData('Unable to create run command. Expected required files in %s' % param_dir)
                else:
                    param_replacements[input_name] = ''

        param_replacements['job_output_dir'] = SCALE_JOB_EXE_OUTPUT_PATH

        command_arguments = self._replace_command_parameters(command_arguments, param_replacements)

        # Remove extra whitespace
        command_arguments = ' '.join(command_arguments.split())

        return command_arguments

    def get_command(self):
        """Gets the command
        :return: the command
        :rtype: str
        """

        return self.definition['command']

    def get_dict(self):
        """Returns the internal dictionary that represents this job interface

        :returns: The internal dictionary
        :rtype: dict
        """

        return self.definition

    def get_file_output_names(self):
        """Returns the output parameter names for all file outputs

        :return: The file output parameter names
        :rtype: list of str
        """

        names = []
        for output_data in self.definition['output_data']:
            if output_data['type'] in ['file', 'files']:
                names.append(output_data['name'])
        return names

    def perform_post_steps(self, job_exe, job_data, stdoutAndStderr):
        """Stores the files and deletes any working directories

        :param job_exe: The job execution model with related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param stdoutAndStderr: the standard out from the job execution
        :type stdoutAndStderr: str
        :return: A tuple of the job results and the results manifest generated by the job execution
        :rtype: (:class:`job.configuration.results.job_results.JobResults`,
            :class:`job.configuration.results.results_manifest.results_manifest.ResultsManifest`)
        """

        manifest_data = {}
        path_to_manifest_file = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, 'results_manifest.json')
        if os.path.exists(path_to_manifest_file):
            logger.info('Opening results manifest...')
            with open(path_to_manifest_file, 'r') as manifest_file:
                manifest_data = json.loads(manifest_file.read())
                logger.info('Results manifest:')
                logger.info(manifest_data)
        else:
            logger.info('No results manifest found')

        results_manifest = ResultsManifest(manifest_data)
        stdout_files = self._get_artifacts_from_stdout(stdoutAndStderr)
        results_manifest.add_files(stdout_files)

        results_manifest.validate(self._output_file_manifest_dict)

        files_to_store = {}
        for manifest_file_entry in results_manifest.get_files():
            param_name = manifest_file_entry['name']

            media_type = None
            output_data_item = self._get_output_data_item_by_name(param_name)
            if output_data_item:
                media_type = output_data_item.get('media_type')

            msg = 'Output %s has invalid/missing file path "%s"'
            if 'file' in manifest_file_entry:
                file_entry = manifest_file_entry['file']
                if not os.path.isfile(file_entry['path']):
                    raise InvalidResultsManifest(msg % (param_name, file_entry['path']))
                if 'geo_metadata' in file_entry:
                    files_to_store[param_name] = (file_entry['path'], media_type, file_entry['geo_metadata'])
                else:
                    files_to_store[param_name] = (file_entry['path'], media_type)
            elif 'files' in manifest_file_entry:
                file_tuples = []
                for file_entry in manifest_file_entry['files']:
                    if not os.path.isfile(file_entry['path']):
                        raise InvalidResultsManifest(msg % (param_name, file_entry['path']))
                    if 'geo_metadata' in file_entry:
                        file_tuples.append((file_entry['path'], media_type, file_entry['geo_metadata']))
                    else:
                        file_tuples.append((file_entry['path'], media_type))
                files_to_store[param_name] = file_tuples

        job_data_parse_results = {}  # parse results formatted for job_data
        for parse_result in results_manifest.get_parse_results():
            filename = parse_result['filename']
            assert filename not in job_data_parse_results
            geo_metadata = parse_result.get('geo_metadata', {})
            geo_json = geo_metadata.get('geo_json', None)
            data_started = geo_metadata.get('data_started', None)
            data_ended = geo_metadata.get('data_ended', None)
            data_types = parse_result.get('data_types', [])
            new_workspace_path = parse_result.get('new_workspace_path', None)
            if new_workspace_path:
                new_workspace_path = os.path.join(new_workspace_path, filename)
            job_data_parse_results[filename] = (geo_json, data_started, data_ended, data_types, new_workspace_path)

        job_data.save_parse_results(job_data_parse_results)
        return (job_data.store_output_data_files(files_to_store, job_exe), results_manifest)

    def perform_pre_steps(self, job_data, job_environment):
        """Performs steps prep work before a job can actually be run.  This includes downloading input files.
        This returns the command that should be executed for these parameters.
        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param job_environment: The job environment
        :type job_environment: :class:`job.configuration.environment.job_environment.JobEnvironment`
        """
        retrieve_files_dict = self._create_retrieve_files_dict()
        job_data.setup_job_dir(retrieve_files_dict)

    def populate_command_argument_properties(self, job_data):
        """Return the command arguments string,
        populated with the properties from the job_data.

        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :return: command arguments for the given properties
        :rtype: str
        """
        command_arguments = self.definition['command_arguments']
        param_replacements = {}

        for input_data in self.definition['input_data']:
            input_name = input_data['name']
            input_type = input_data['type']
            if input_type == 'property':
                property_val = job_data.data_inputs_by_name[input_name]['value']
                param_replacements[input_name] = property_val

        command_arguments = self._replace_command_parameters(command_arguments, param_replacements)

        return command_arguments

    def populate_command_argument_settings(self, command_arguments, job_configuration):
        """Return the command arguments string,
        populated with the settings from the job_configuration.

        :param command_arguments: The command_arguments that you want to perform the replacement on
        :type command_arguments: string
        :param job_configuration: The job configuration
        :type job_configuration: :class:`job.configuration.configuration.job_configuration.JobConfiguration`
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
        :type job_configuration: :class:`job.configuration.configuration.job_configuration.JobConfiguration`

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

    def validate_connection(self, job_conn):
        """Validates the given job connection to ensure that the connection will provide sufficient data to run a job
        with this interface

        :param job_conn: The job data
        :type job_conn: :class:`job.configuration.data.job_connection.JobConnection`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidConnection`: If there is a configuration problem.
        """

        warnings = []
        warnings.extend(job_conn.validate_input_files(self._input_file_validation_dict))
        warnings.extend(job_conn.validate_properties(self._property_validation_dict))
        # Make sure connection has a workspace if the interface has any output files
        if self._output_file_validation_list and not job_conn.has_workspace():
            raise InvalidConnection('No workspace provided for output files')
        return warnings

    def validate_data(self, job_data):
        """Ensures that the job_data matches the job_interface description

        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        warnings = []
        warnings.extend(job_data.validate_input_files(self._input_file_validation_dict))
        warnings.extend(job_data.validate_properties(self._property_validation_dict))
        warnings.extend(job_data.validate_output_files(self._output_file_validation_list))
        return warnings

    def validate_populated_settings(self, job_configuration):
        """Ensures that all required settings are defined in the job_configuration

        :param job_configuration: The job configuration
        :type job_configuration: :class:`job.configuration.configuration.job_configuration.JobConfiguration`
        """

        interface_settings = self.definition['settings']
        config_setting_names = [setting.name for setting in job_configuration.get_job_task_settings()]

        for setting in interface_settings:
            setting_name = setting['name']
            setting_required = setting['required']

            if setting_required:
                if setting_name not in config_setting_names:
                    raise InvalidSetting('Required setting %s was not provided' % setting_name)

    def _check_env_var_uniqueness(self):
        """Ensures all the enviornmental variable names are unique, and throws a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` if they are not unique
        """

        env_vars = [env_var['name'] for env_var in self.definition['env_vars']]

        if len(env_vars) != len(set(env_vars)):
            raise InvalidInterfaceDefinition('Environment variable names must be unique')

    def _check_param_name_uniqueness(self):
        """Ensures all the parameter names are unique, and throws a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` if they are not unique
        """

        for input_data in self.definition['input_data']:
            if input_data['name'] in self._param_names:
                raise InvalidInterfaceDefinition('shared resource & input_data names must be unique')
            self._param_names.add(input_data['name'])

        for shared_resource in self.definition['shared_resources']:
            if shared_resource['name'] in self._param_names:
                raise InvalidInterfaceDefinition('shared resource & input_data names must be unique')
            self._param_names.add(shared_resource['name'])

    def _create_retrieve_files_dict(self):
        """creates parameter folders and returns the dict needed to call
        :classmethod:`job.configuration.data.job_data.JobData.retrieve_files_dict`

        :return: a dictionary representing the files to retrieve
        :rtype:  dist of str->tuple with input_name->(is_multiple, input_path)
        """

        retrieve_files_dict = {}
        for input_data in self.definition['input_data']:
            input_name = input_data['name']
            input_type = input_data['type']
            if input_type in ['file', 'files']:
                is_multiple = input_type == 'files'
                partial = input_data['partial']
                input_path = os.path.join(SCALE_JOB_EXE_INPUT_PATH, input_name)
                retrieve_files_dict[input_name] = (is_multiple, input_path, partial)
        return retrieve_files_dict

    def _check_setting_name_uniqueness(self):
        """Ensures all the settings names are unique, and throws a
        :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition` if they are not unique
        """

        for setting in self.definition['settings']:
            if setting['name'] in self._param_names:
                raise InvalidInterfaceDefinition('Setting names must be unique')
            self._param_names.add(setting['name'])

    def _create_validation_dicts(self):
        """Creates the validation dicts required by job_data to perform its validation"""
        for input_data in self.definition['input_data']:
            name = input_data['name']
            required = input_data['required']
            if input_data['type'] == 'property':
                self._property_validation_dict[name] = required
            elif input_data['type'] == 'file':
                file_desc = ScaleFileDescription()
                for media_type in input_data['media_types']:
                    file_desc.add_allowed_media_type(media_type)
                self._input_file_validation_dict[name] = (required, False, file_desc)
            elif input_data['type'] == 'files':
                file_desc = ScaleFileDescription()
                for media_type in input_data['media_types']:
                    file_desc.add_allowed_media_type(media_type)
                self._input_file_validation_dict[name] = (required, True, file_desc)

        for ouput_data in self.definition['output_data']:
            output_type = ouput_data['type']
            if output_type in ['file', 'files']:
                name = ouput_data['name']
                required = ouput_data['required']
                self._output_file_validation_list.append(name)
                self._output_file_manifest_dict[name] = (output_type == 'files', required)

    @staticmethod
    def _get_artifacts_from_stdout(stdout):
        """Parses stdout looking for artifacts of the form ARTIFACT:<ouput_name>:<output_path>
        :param stdout: the standard out from the job execution
        :type stdout: str

        :return: a list of artifacts that were found by parsing stdout
        :rtype: a list of artifact dicts.  each artifact dict has a "name" and either a "path" or "paths
        see job.configuration.results.manifest.RESULTS_MANIFEST_SCHEMA
        """
        artifacts_found = {}
        artifacts_pattern = '^ARTIFACT:([^:]*):(.*)'
        for artifact_match in re.findall(artifacts_pattern, stdout, re.MULTILINE):
            artifact_name = artifact_match[0]
            artifact_path = artifact_match[1]
            if artifact_name in artifacts_found:
                paths = []
                if 'paths' in artifacts_found[artifact_name]:
                    paths = artifacts_found[artifact_name]['paths']
                else:
                    paths = [artifacts_found[artifact_name]['path']]
                    artifacts_found[artifact_name].pop('path')
                paths.append(artifact_path)
                artifacts_found[artifact_name]['paths'] = paths
            else:
                artifacts_found[artifact_name] = {'name': artifact_name, 'path': artifact_path}
        return artifacts_found.values()

    @staticmethod
    def _get_one_file_from_directory(dir_path):
        """Checks a directory for one and only one file.  If there is not one file, raise a
        :exception:`job.configuration.data.exceptions.InvalidData`.  If there is one file, this method
        returns the full path of that file.

        :param dir_path: The directories path
        :type dir_path: string
        :return: The path to the one file in a given directory
        :rtype: str
        """
        entries_in_dir = os.listdir(dir_path)
        if len(entries_in_dir) != 1:
            raise InvalidData('Unable to create run command.  Expected one file in %s', dir_path)
        return os.path.join(dir_path, entries_in_dir[0])

    def _get_output_data_item_by_name(self, data_item_name):
        """gets an output data item with the given name
        :param data_item_name: The name of the data_item_name
        :type data_item_name: str
        """

        for output_data in self.definition['output_data']:
            if data_item_name == output_data['name']:
                return output_data

    @staticmethod
    def _get_settings_values(settings, config_settings):
        """
        :param settings: The job configuration
        :type settings: JSON
        :param config_settings: The job configuration
        :type config_settings: :class:`job.configuration.configuration.job_configuration.JobConfiguration`
        :return: settings name and the value to replace it with
        :rtype: dict
        """

        param_replacements = {}

        # Isolate the job_type settings and convert to list
        config_settings = config_settings['job_task']['settings']
        config_settings_dict = {setting['name']: setting['value'] for setting in config_settings}

        for setting in settings:
            setting_name = setting['name']

            if setting_name in config_settings_dict:
                param_replacements[setting_name] = config_settings_dict[setting_name]
            else:
                param_replacements[setting_name] = ''

        return param_replacements

    def _populate_default_values(self):
        """Goes through the definition and fills in any missing default values"""
        if 'version' not in self.definition:
            self.definition['version'] = SCHEMA_VERSION
        if 'input_data' not in self.definition:
            self.definition['input_data'] = []
        if 'shared_resources' not in self.definition:
            self.definition['shared_resources'] = []
        if 'output_data' not in self.definition:
            self.definition['output_data'] = []

        self._populate_input_data_defaults()
        self._populate_resource_defaults()
        self._populate_output_data_defaults()

    def _populate_settings_defaults(self):
        """populates the default values for any missing settings values"""

        if 'settings' not in self.definition:
            self.definition['settings'] = []

        for setting in self.definition['settings']:
            if 'required' not in setting:
                setting['required'] = True

            if 'secret' not in setting:
                setting['secret'] = False

    def _populate_env_vars_defaults(self):
        """populates the default values for any missing environment variable values"""

        if 'env_vars' not in self.definition:
            self.definition['env_vars'] = []

        for env_var in self.definition['env_vars']:
            if 'value' not in env_var:
                env_var['value'] = ""

    def _populate_input_data_defaults(self):
        """populates the default values for any missing input_data values"""
        for input_data in self.definition['input_data']:
            if 'required' not in input_data:
                input_data['required'] = True
            if input_data['type'] in ['file', 'files'] and 'media_types' not in input_data:
                input_data['media_types'] = []
            if input_data['type'] in ['file', 'files'] and 'partial' not in input_data:
                input_data['partial'] = False

    def _populate_output_data_defaults(self):
        """populates the default values for any missing output_data values"""
        for output_data in self.definition['output_data']:
            if 'required' not in output_data:
                output_data['required'] = True

    def _populate_resource_defaults(self):
        """populates the default values for any missing shared_resource values"""
        for shared_resource in self.definition['shared_resources']:
            if 'required' not in shared_resource:
                shared_resource['required'] = True

    def _populate_default_values(self):
        """Goes through the definition and fills in any missing default values"""
        if 'version' not in self.definition:
            self.definition['version'] = SCHEMA_VERSION
        if 'input_data' not in self.definition:
            self.definition['input_data'] = []
        if 'shared_resources' not in self.definition:
            self.definition['shared_resources'] = []
        if 'output_data' not in self.definition:
            self.definition['output_data'] = []

        self._populate_input_data_defaults()
        self._populate_resource_defaults()
        self._populate_output_data_defaults()

    def _populate_input_data_defaults(self):
        """populates the default values for any missing input_data values"""
        for input_data in self.definition['input_data']:
            if 'required' not in input_data:
                input_data['required'] = True
            if input_data['type'] in ['file', 'files'] and 'media_types' not in input_data:
                input_data['media_types'] = []

    def _populate_output_data_defaults(self):
        """populates the default values for any missing output_data values"""
        for output_data in self.definition['output_data']:
            if 'required' not in output_data:
                output_data['required'] = True

    def _populate_resource_defaults(self):
        """populates the default values for any missing shared_resource values"""
        for shared_resource in self.definition['shared_resources']:
            if 'required' not in shared_resource:
                shared_resource['required'] = True

    @staticmethod
    def _replace_command_parameters(command_arguments, param_replacements):
        """find all occurrences of a parameter with a given name in the command_arguments string and
        replace it with the param value. If the parameter replacement string in the command uses a
        custom output ( ${-f :foo}).
        The parameter will be replaced with the string preceding the colon and the given param value
        will be appended.

        :param command_arguments: The command_arguments that you want to perform the replacement on
        :type command_arguments: string
        :param param_replacements: The parameters you are searching for
        :type param_replacements: dict
        :return: The string with all replacements made
        :rtype: str
        """
        ret_str = command_arguments

        for param_name, param_value in param_replacements.iteritems():
            param_pattern = '\$\{([^\}]*\:)?' + re.escape(param_name) + '\}'
            pattern_prog = re.compile(param_pattern)

            keep_replacing = True
            while keep_replacing:
                match_obj = re.search(pattern_prog, ret_str)
                if match_obj:
                    replacement_str = param_value
                    if match_obj.group(1):
                        replacement_str = match_obj.group(1)[:-1] + param_value
                    ret_str = ret_str[0:match_obj.start()] + replacement_str + ret_str[match_obj.end():]
                else:
                    keep_replacing = False

        return ret_str

    @staticmethod
    def _replace_env_var_parameters(env_vars, param_replacements):
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

    def _validate_command_arguments(self):
        """Ensure the command string is valid, and any parameters used
        are actually in the input_data or shared_resources.
        Will raise a :exception:`job.configuration.data.exceptions.InvalidInterfaceDefinition`
        if the arguments are not valid
        """
        command_arguments = self.definition['command_arguments']

        param_pattern = '\$\{(?:[^\}]*:)?([^\}]*)\}'

        for param in re.findall(param_pattern, command_arguments):
            found_match = False
            for input_data in self.definition['input_data']:
                if input_data['name'] == param:
                    found_match = True
                    break
            if not found_match:
                for shared_resource in self.definition['shared_resources']:
                    if shared_resource['name'] == param:
                        found_match = True
                        break

            if not found_match:
                if self.definition['version'] >= '1.2':
                    for setting in self.definition['settings']:
                        if setting['name'] == param:
                            found_match = True
                            break

            # Look for system properties
            if param == 'job_output_dir':
                found_match = True

            if not found_match:
                msg = 'The %s parameter was not found in any inputs, shared_resources, or system variables' % param
                raise InvalidInterfaceDefinition(msg)
