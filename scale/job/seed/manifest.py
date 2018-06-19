"""Defines the interface for executing a job"""
from __future__ import unicode_literals

import json
import logging
import os

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.data.exceptions import InvalidData, InvalidConnection
from job.execution.configuration.exceptions import MissingMount, MissingSetting
from job.seed.exceptions import InvalidSeedManifestDefinition
from job.seed.types import SeedInputFiles, SeedInputJson, SeedOutputJson, SeedOutputFiles
from scheduler.vault.manager import secrets_mgr
from storage.media_type import UNKNOWN_MEDIA_TYPE
from util.environment import normalize_env_var_name

logger = logging.getLogger(__name__)

MODE_RO = 'ro'
MODE_RW = 'rw'

SCHEMA_FILENAME = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schema/seed.manifest.schema.json')
with open(SCHEMA_FILENAME) as schema_file:
    SEED_MANIFEST_SCHEMA = json.load(schema_file)


class SeedManifest(object):
    """Represents the interface defined by an algorithm developer to a Seed job"""

    def __init__(self, definition, do_validate=True):
        """Creates a seed interface from the given definition. If the definition is invalid, a
        :class:`job.seed.exceptions.InvalidInterfaceDefinition` exception will be thrown.

        :param definition: The interface definition
        :type definition: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool
        """

        self.definition = definition

        try:
            if do_validate:
                validate(definition, SEED_MANIFEST_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidSeedManifestDefinition(validation_error)

        self._populate_default_values()

        self._check_for_name_collisions()
        self._check_mount_name_uniqueness()

        self._validate_mount_paths()
        # self._create_validation_dicts()

    def add_output_to_connection(self, output_name, job_conn, input_name):
        """Adds the given output from the interface as a new input to the given job connection

        :param output_name: The name of the output to add to the connection
        :type output_name: str
        :param job_conn: The job connection
        :type job_conn: :class:`job.data.job_connection.JobConnection`
        :param input_name: The name of the connection input
        :type input_name: str
        """

        output = self._get_output_data_item_by_name(output_name)
        # TODO: We are only getting files, but in the future we need to branch for file/json

        if isinstance(output, SeedOutputFiles):
            # TODO: How do we want to handle down-stream partial handling? Setting to False presently
            job_conn.add_input_file(input_name, output.multiple, [output.media_type], not output.required, False)

        if isinstance(output, SeedOutputJson):
            job_conn.add_property(input_name)

    def add_workspace_to_data(self, job_data, workspace_id):
        """Adds the given workspace ID to the given job data for every output in this job interface

        :param job_data: The job data
        :type job_data: :class:`job.data.job_data.JobData`
        :param workspace_id: The workspace ID
        :type workspace_id: int
        """

        for file_output_name in self.get_file_output_names():
            job_data.add_file_output({'name':file_output_name, 'workspace_id': workspace_id})

    def get_name(self):
        """Gets the Job name
        :return: the name
        :rtype: str
        """

        return self.get_job()['name']

    def get_title(self):
        """Gets the Job title
        :return: the title
        :rtype: str
        """

        return self.get_job()['title']

    def get_description(self):
        """Gets the Job description
        :return: the description
        :rtype: str
        """

        return self.get_job()['description']

    def get_tags(self):
        """Gets the Job tags
        :return: the tags
        :rtype: [str]
        """

        return self.get_job()['tags']

    def get_job(self):
        """Gets the Job object within the Seed manifest

        :return: the Job object
        """

        return self.definition['job']

    def get_job_version(self):
        """Gets the Job version
        :return: the version
        :rtype: str
        """

        return self.get_job()['jobVersion']

    def get_timeout(self):
        """Gets the Job timeout

        :return: the version
        :rtype: integer
        """

        return self.get_job()['timeout']

    def get_command(self):
        """Gets the command
        :return: the command
        :rtype: str
        """

        return self.get_interface().get('command', None)

    def get_injected_command_args(self, values, env_vars):
        """Gets the command, injecting env_vars and input variables

        :param values: Input values to replace named placeholders in command value
        :type values: {str, str}
        :param env_vars: Incoming environment variables
        :type env_vars: dict
        :return: the command
        :rtype: str
        """

        from util.command import environment_expansion

        return environment_expansion(env_vars, self.get_command())

    def get_interface(self):
        """Gets the interface for the Seed job

        :return: the interface object
        :rtype: dict
        """

        return self.get_job().get('interface', {})

    def get_settings(self):
        """Gets the settings for the Seed job

        :return: the settings object
        :rtype: dict
        """

        return self.get_interface().get('settings', [])

    def get_inputs(self):
        """Gets the inputs defined in the interface

        :return: the inputs defined for the job
        :rtype: dict
        """

        return self.get_interface().get('inputs', {'files': [], 'json': []})

    def get_outputs(self):
        """Gets the outputs defined in the interface

        :return: the outputs defined for the job
        :rtype: dict
        """

        return self.get_interface().get('outputs', {'files': [], 'json': []})

    def get_input_files(self):
        """Gets the list of input files defined in the interface

        :return: the input file definitions for job
        :rtype: list
        """

        return self.get_inputs().get('files', [])

    def get_input_json(self):
        """Gets the list of json defined in the interface

        :return: the input json definitions for job
        :rtype: list
        """

        return self.get_inputs().get('json', [])

    def get_seed_output_files(self):
        """Get the list of SeedOutputFiles typed results

        :return: list of output files elements
        :rtype: [`job.seed.types.SeedOutputFiles`]
        """

        return [SeedOutputFiles(x) for x in self.get_output_files()]

    def get_output_files(self):
        """Gets the list of output files defined in the interface

        Commonly used when matching globs to capture output files

        :return: the output file definitions for job
        :rtype: list
        """

        return self.get_outputs().get('files', [])

    def get_seed_output_json(self):
        """Get the list of SeedOutputJson typed results

        :return: list of output json elements
        :rtype: [`job.seed.types.SeedOutputJson`]
        """

        return [SeedOutputJson(x) for x in self.get_output_json()]

    def get_output_json(self):
        """Gets the list of output json defined in the interface

        Commonly used when matching globs to capture output files

        :return: the output file definitions for job
        :rtype: list
        """

        return self.get_outputs().get('json', [])

    def get_scalar_resources(self):
        """Gets the scalar resources defined the Seed job

        :return: the scalar resources required by job
        :rtype: list
        """

        return self.get_job().get('resources', {'scalar': []})['scalar']

    def get_mounts(self):
        """Gets the mounts defined the Seed job

        :return: the mounts for a job
        :rtype: list
        """

        return self.get_interface().get('mounts', [])

    def get_maintainer(self):
        """Gets the maintainer details for the Seed job

        :return: the maintainer details of job
        :rtype: dict
        """

        return self.get_job()['maintainer']

    def get_errors(self):
        """Get the error mapping defined for the Seed job

        :return: the error codes mapped for job
        :rtype: list
        """

        return self.get_job().get('errors', [])

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
        for output_file in self.get_output_files():
            names.append(output_file['name'])
        return names

    def perform_pre_steps(self, job_data):
        """Performs steps prep work before a job can actually be run.  This includes downloading input files.
        This returns the command that should be executed for these parameters.
        :param job_data: The job data
        :type job_data: :class:`job.data.job_data.JobData`
        """
        job_data.setup_job_dir(self.get_input_files())

    def validate_connection(self, job_conn):
        """Validates the given job connection to ensure that the connection will provide sufficient data to run a job
        with this interface

        :param job_conn: The job data
        :type job_conn: :class:`job.seed.data.job_connection.JobConnection`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.data.job_data.ValidationWarning`]

        :raises :class:`job.data.exceptions.InvalidConnection`: If there is a configuration problem.
        """

        warnings = []
        warnings.extend(job_conn.validate_input_files([SeedInputFiles(x) for x in self.get_input_files()]))
        warnings.extend(job_conn.validate_properties([SeedInputJson(x) for x in self.get_input_json()]))
        # Make sure connection has a workspace if the interface has any output files
        if len(self.get_output_files()) and not job_conn.has_workspace():
            raise InvalidConnection('No workspace provided for output files')
        return warnings

    def validate_data(self, job_data):
        """Ensures that the job_data matches the job_interface description

        :param job_data: The job data
        :type job_data: :class:`job.data.job_data.JobData`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.data.job_data.ValidationWarning`]

        :raises :class:`job.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        warnings = []
        warnings.extend(job_data.validate_input_files([SeedInputFiles(x) for x in self.get_input_files()]))
        warnings.extend(job_data.validate_input_json([SeedInputJson(x) for x in self.get_input_json()]))
        warnings.extend(job_data.validate_output_files([x['name'] for x in self.get_output_files()]))
        return warnings

    def validate_populated_mounts(self, exe_configuration):
        """Ensures that all required mounts are defined in the execution configuration

        :param exe_configuration: The execution configuration
        :type exe_configuration: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        """

        for name, mount_volume in exe_configuration.get_mounts('main').items():
            if mount_volume is None:
                raise MissingMount(name)

    def validate_populated_settings(self, exe_configuration):
        """Ensures that all required settings are defined in the execution configuration

        :param exe_configuration: The execution configuration
        :type exe_configuration: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        """

        for name, value in exe_configuration.get_settings('main').items():
            if value is None:
                raise MissingSetting(name)

    def _check_for_name_collisions(self):
        """Ensures all names that map to environment variables are unique, and throws a
        :class:`job.seed.exceptions.InvalidInterfaceDefinition` if they are not unique.

        Per Seed specification for implementors we must validate that all reserved keywords, settings
        and inputs are unique as they are ultimately injected as environment variables.
        """

        # Include reserved keywords
        env_vars = ["OUTPUT_DIR"]

        env_vars += [normalize_env_var_name(setting['name']) for setting in self.get_settings()]
        env_vars += [normalize_env_var_name(input_file['name']) for input_file in self.get_input_files()]
        env_vars += [normalize_env_var_name(json['name']) for json in self.get_input_json()]
        env_vars += [normalize_env_var_name('ALLOCATED_' + resource['name']) for resource in
                     self.get_scalar_resources()]

        if len(env_vars) != len(set(env_vars)):
            raise InvalidSeedManifestDefinition('Collisions are not allowed between reserved keywords, resources, settings'
                                                'and input names.')

    def _check_mount_name_uniqueness(self):
        """Ensures all the mount names are unique, and throws a
        :class:`job.seed.exceptions.InvalidInterfaceDefinition` if they are not unique
        """

        mounts = []
        for mount in self.get_mounts():
            mounts.append(mount['name'])

        if len(mounts) != len(set(mounts)):
            raise InvalidSeedManifestDefinition('Mount names must be unique.')

    @staticmethod
    def _get_one_file_from_directory(dir_path):
        """Checks a directory for one and only one file.  If there is not one file, raise a
        :exception:`job.data.exceptions.InvalidData`.  If there is one file, this method
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

        for output_json in self.get_seed_output_json():
            if data_item_name == output_json.name:
                return output_json

        for output_file in self.get_seed_output_files():
            if data_item_name == output_file.name:
                return output_file

    def _get_settings_values(self, settings, exe_configuration, job_type, censor):
        """
        :param settings: The settings
        :type settings: dict
        :param exe_configuration: The execution configuration
        :type exe_configuration: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        :param job_type: The job type definition
        :type job_type: :class:`job.models.JobType`
        :param censor: Whether to censor secrets
        :type censor: bool
        :return: settings name and the value to replace it with
        :rtype: dict
        """

        config_settings = exe_configuration.get_dict()
        param_replacements = {}
        secret_settings = {}

        # Isolate the job_type settings and convert to list
        for task_dict in config_settings['tasks']:
            if task_dict['type'] == 'main':
                config_settings_dict = task_dict['settings']

        for setting in settings:
            setting_name = setting['name']
            setting_is_secret = setting['secret']

            if setting_is_secret:
                job_index = job_type.get_secrets_key()

                if not secret_settings:
                    secret_settings = secrets_mgr.retrieve_job_type_secrets(job_index)

                if setting_name in secret_settings.keys():
                    if censor:
                        settings_value = '*****'
                    else:
                        settings_value = secret_settings[setting_name]
                    param_replacements[setting_name] = settings_value
                else:
                    param_replacements[setting_name] = ''
            else:
                if setting_name in config_settings_dict:
                    param_replacements[setting_name] = config_settings_dict[setting_name]
                else:
                    param_replacements[setting_name] = ''

        return param_replacements

    def _populate_default_values(self):
        """Goes through the definition and fills in any missing default values"""
        self._populate_resource_defaults()
        self._populate_inputs_defaults()
        self._populate_outputs_defaults()
        self._populate_mounts_defaults()
        self._populate_settings_defaults()

    def _populate_mounts_defaults(self):
        """Populates the default values for any missing mounts values"""

        for mount in self.get_mounts():
            if 'mode' not in mount:
                mount['mode'] = MODE_RO

    def _populate_settings_defaults(self):
        """populates the default values for any missing settings values"""

        for setting in self.get_settings():
            if 'secret' not in setting:
                setting['secret'] = False

    def _populate_inputs_defaults(self):
        """populates the default values for any missing inputs values"""

        for input_file in self.get_input_files():
            if 'required' not in input_file:
                input_file['required'] = True
            if 'mediaType' not in input_file:
                input_file['mediaTypes'] = []
            if 'multiple' not in input_file:
                input_file['multiple'] = False
            if 'partial' not in input_file:
                input_file['partial'] = False

        for input_json in self.get_input_json():
            if 'required' not in input_json:
                input_json['required'] = True

    def _populate_outputs_defaults(self):
        """populates the default values for any missing outputs values"""
        for output_file in self.get_output_files():
            if 'mediaType' not in output_file:
                output_file['mediaType'] = UNKNOWN_MEDIA_TYPE
            if 'count' not in output_file:
                output_file['multiple'] = False
            if 'required' not in output_file:
                output_file['required'] = True

        for output_json in self.get_output_json():
            if 'required' not in output_json:
                output_json['required'] = True

    def _populate_resource_defaults(self):
        """populates the default values for any missing shared_resource values"""

        pass

    def _populate_errors_defaults(self):
        """populates the default values for any missing errors values"""

        for error in self.get_errors():
            if 'category' not in error:
                error['category'] = 'job'
            if 'description' not in error:
                error['description'] = error['title']

    def _validate_mount_paths(self):
        """Ensures that all mount paths are valid

        :raises :class:`job.seed.exceptions.InvalidSeedManifestDefinition`: If a mount path is invalid
        """

        for mount in self.get_mounts():
            name = mount['name']
            path = mount['path']
            if not os.path.isabs(path):
                raise InvalidSeedManifestDefinition('%s mount must have an absolute path' % name)
