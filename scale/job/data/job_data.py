"""Defines the data needed for executing a job"""
from __future__ import unicode_literals

import logging
from copy import deepcopy

import os
from numbers import Integral

from data.data.value import FileValue, JsonValue
from data.data.json.data_v6 import convert_data_to_v6_json, DataV6
from job.configuration.data.exceptions import InvalidData
from job.configuration.interface.scale_file import ScaleFileDescription
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH
from job.seed.types import SeedInputFiles
from storage.brokers.broker import FileDownload
from storage.models import ScaleFile
from util.environment import normalize_env_var_name

logger = logging.getLogger(__name__)


class ValidationWarning(object):
    """Tracks job data configuration warnings during validation that may not prevent the job from working."""

    def __init__(self, key, details):
        """Constructor sets basic attributes.

        :param key: A unique identifier clients can use to recognize the warning.
        :type key: string
        :param details: A user-friendly description of the problem, including field names and/or associated values.
        :type details: string
        """
        self.key = key
        self.details = details


class JobData(object):
    """Represents the data needed for executing a job. Data includes details about the data inputs, links needed to
    connect shared resources to resource instances in Scale, and details needed to store all resulting output.
    """

    def __init__(self, data=None):
        """Creates a job data object from the given dictionary. The general format is checked for correctness, but the
        actual input and output details are not checked for correctness against the job interface. If the data is
        invalid, a :class:`job.configuration.data.exceptions.InvalidData` will be thrown.

        :param data: The job data
        :type data: dict
        """

        if not data:
            data = {}

        self._new_data = DataV6(data, do_validate=True).get_data()

    def add_file_input(self, name, file_id):
        """Adds a new file parameter to this job data.

        :param data: The files parameter dict
        :type data: dict
        """

        self._new_data.add_value(FileValue(name, [file_id]))

    def add_file_list_input(self, name, file_ids):
        """Adds a new files parameter to this job data.

        :param name: The files parameter name
        :type name: string
        :param file_ids: The ID of the file
        :type file_ids: [long]
        """

        self._new_data.add_value(FileValue(name, file_ids))

    def add_json_input(self, data, add_to_internal=True):
        """Adds a new json parameter to this job data.

        :param data: The json parameter dict
        :type data: dict
        :param add_to_internal: Whether we should add to private data dict. Unneeded when used from __init__
        :type add_to_internal: bool
        """

        self._new_data.add_value(JsonValue(data['name'], data['value']))

    def add_file_output(self, data, add_to_internal=True):
        """Adds a new output files to this job data with a workspace ID.

        :param data: The output parameter dict
        :type data: dict
        :param add_to_internal: Whether we should add to private data dict. Unneeded when used from __init__
        :type add_to_internal: bool
        """

        # No longer holding output workspaces in data
        pass

    def get_all_properties(self):
        """Retrieves all properties from this job data and returns them in ascending order of their names

        :returns: List of strings containing name=value
        :rtype: [string]
        """

        properties = []

        names = []
        for input_value in self._new_data.values.values():
            if isinstance(input_value, JsonValue):
                names.append(input_value.name)
        names = sorted(names)
        for name in names:
            properties.append(name + '=' + self._new_data.values[name].value)

        return properties

    def get_dict(self):
        """Returns the internal dictionary that represents this job data

        :returns: The internal dictionary
        :rtype: dict
        """

        return convert_data_to_v6_json(self._new_data).get_dict()

    def get_input_file_ids(self):
        """Returns a set of scale file identifiers for each file in the job input data.

        :returns: Set of scale file identifiers
        :rtype: {int}
        """

        file_ids = set()
        for input_value in self._new_data.values.values():
            if isinstance(input_value, FileValue):
                for file_id in input_value.file_ids:
                    file_ids.add(file_id)
        return file_ids

    def get_input_file_ids_by_input(self):
        """Returns the list of file IDs for each input that holds files

        :returns: Dict where each file input name maps to its list of file IDs
        :rtype: dict
        """

        file_ids = {}
        for input_value in self._new_data.values.values():
            if isinstance(input_value, FileValue):
                file_ids[input_value.name] = input_value.file_ids
        return file_ids

    def get_input_file_info(self):
        """Returns a set of scale file identifiers and input names for each file in the job input data.

        :returns: Set of scale file identifiers and names
        :rtype: set[tuple]
        """

        file_info = set()

        for input_value in self._new_data.values.values():
            if isinstance(input_value, FileValue):
                for file_id in input_value.file_ids:
                    file_info.add((file_id, input_value.name))

        return file_info

    def get_output_workspace_ids(self):
        """Returns a list of the IDs for every workspace used to store the output files for this data

        :returns: List of workspace IDs
        :rtype: [int]
        """

        return []

    def get_output_workspaces(self):
        """Returns a dict of the output parameter names mapped to their output workspace ID

        :returns: A dict mapping output parameters to workspace IDs
        :rtype: dict
        """

        return {}

    def get_property_values(self, property_names):
        """Retrieves the values contained in this job data for the given property names. If no value is available for a
        property name, it will not be included in the returned dict.

        :param property_names: List of property names
        :type property_names: [string]
        :returns: Dict with each property name mapping to its value
        :rtype: {string: string}
        """

        property_values = {}

        for name in property_names:
            if name in self._new_data.values:
                property_values[name] = self._new_data.values[name].value

        return property_values

    def retrieve_input_data_files(self, data_files):
        """Retrieves the given data input files and writes them to the given local directories. Any given file
        parameters that do not appear in the data will not be returned in the results.

        :param data_files: Object containing manifest details on input files.
        :type data_files: [`job.seed.types.SeedInputFiles`]
        :returns: Dict with each file parameter name mapping to a list of absolute file paths of the written files
        :rtype: {string: [string]}
        """

        # Organize the data files
        param_file_ids = {}  # Parameter name -> [file IDs]
        # File ID -> tuple(string, bool) for relative dir path and if partially accessed
        files_to_retrieve = {}
        for data_file in data_files:
            input_name = data_file.name
            multiple = data_file.multiple
            dir_path = os.path.join(SCALE_JOB_EXE_INPUT_PATH, input_name)
            partial = data_file.partial
            if data_file.name not in self._new_data.values:
                continue
            file_input = self._new_data.values[data_file.name]
            file_ids = []
            if not multiple and len(file_input.file_ids) > 1:
                raise Exception(
                    'Multiple inputs detected for input %s that does not support.' % (data_file.name,))
            for file_id in file_input.file_ids:
                file_id = long(file_id)
                file_ids.append(file_id)
                files_to_retrieve[file_id] = (dir_path, partial)
            param_file_ids[data_file.name] = file_ids

        # Retrieve all files
        retrieved_files = self._retrieve_files(files_to_retrieve)
        for file_id in retrieved_files:
            del files_to_retrieve[file_id]
        if files_to_retrieve:
            msg = 'Failed to retrieve file with ID %i' % files_to_retrieve.keys()[0]
            raise Exception(msg)

        # Organize the results
        retrieved_params = {}  # Parameter name -> [file paths]
        for name in param_file_ids:
            file_path_list = []
            for file_id in param_file_ids[name]:
                file_path_list.append(retrieved_files[file_id])
            retrieved_params[name] = file_path_list

        return retrieved_params

    def get_injected_input_values(self, input_files):
        """Apply all execution time values to job data

        TODO: Remove with v6 when old style Job Types are removed

        :param input_files: Mapping of input names to InputFiles
        :type input_files: {str, :class:`job.execution.configuration.input_file.InputFile`}
        :return: Mapping of all input keys to their true file / property values
        :rtype: {str, str}
        """
        input_values = {}

        # No data is created here, as this is only used for parameter injection into command args.
        # Environment variables injection is done under get_injected_env_vars

        return input_values

    def has_workspaces(self):
        """Whether this job data contains output wrkspaces

        :returns: Whether this job data contains output wrkspaces
        :rtype: bool
        """

        return False

    # TODO: Remove with v5 API
    def extend_interface_with_inputs_v5(self, interface, job_files):
        """Create an input_data like object for legacy v5 API

        :param interface: Seed manifest which should have concrete inputs injected
        :type interface: :class:`job.seed.manifest.SeedManifest`
        :param job_files: A list of files that are referenced by the job data.
        :type job_files: [:class:`storage.models.ScaleFile`]
        :return: A dictionary of Seed Manifest inputs key mapped to the corresponding data value.
        :rtype: dict
        """

        inputs = []
        input_files = deepcopy(interface.get_input_files())
        input_json = deepcopy(interface.get_input_json())

        file_map = {job_file.id: job_file for job_file in job_files}
        for in_file in input_files:
            # Use internal JobInputFiles data structure to get Scale File IDs
            # Follow that up with a list comprehension over potentially multiple IDs to get
            # final list of ScaleFile objects
            in_file['value'] = [file_map[x] for x in self._new_data.values[in_file['name']].file_ids]

            if len(in_file['value']) >= 2:
                in_file['type'] = 'files'
            else:
                in_file['value'] = in_file['value'][0]
                in_file['type'] = 'file'
            inputs.append(in_file)
        for x in input_json:
            x['value'] = self._new_data.values[x['name']].value
            x['type'] = 'property'
            inputs.append(x)
        return inputs

    def extend_interface_with_inputs(self, interface, job_files):
        """Add a value property to both files and json objects within Seed Manifest

        :param interface: Seed manifest which should have concrete inputs injected
        :type interface: :class:`job.seed.manifest.SeedManifest`
        :param job_files: A list of files that are referenced by the job data.
        :type job_files: [:class:`storage.models.ScaleFile`]
        :return: A dictionary of Seed Manifest inputs key mapped to the corresponding data value.
        :rtype: dict
        """

        inputs = deepcopy(interface.get_inputs())
        input_files = deepcopy(interface.get_input_files())
        input_json = deepcopy(interface.get_input_json())

        files = []
        json = []
        file_map = {job_file.id: job_file for job_file in job_files}
        for in_file in input_files:
            # Use internal JobInputFiles data structure to get Scale File IDs
            # Follow that up with a list comprehension over potentially multiple IDs to get 
            # final list of ScaleFile objects

            in_file['value'] = [file_map[x] for x in self._new_data.values[in_file['name']].file_ids]
            files.append(in_file)
        for x in input_json:
            x['value'] = self._new_data.values[x['name']].value
            json.append(x)
        inputs['files'] = files
        inputs['json'] = json
        return inputs

    def get_injected_env_vars(self, input_files):
        """Inject all execution time values to job data mappings

        :param input_files: Mapping of input names to InputFiles
        :type input_files: {str, :class:`job.execution.configuration.input_file.InputFile`}
        :return: Mapping of all input keys to their true file / property values
        :rtype: {str, str}
        """
        env_vars = {}
        for file_input in self._new_data.values.values():
            if isinstance(file_input, FileValue):
                env_var_name = normalize_env_var_name(file_input.name)
                if len(file_input.file_ids) > 1:
                    # When we have input for multiple files, map in the entire directory
                    env_vars[env_var_name] = os.path.join(SCALE_JOB_EXE_INPUT_PATH, file_input.name)
                else:
                    input_file = input_files[file_input.name][0]
                    file_name = os.path.basename(input_file.workspace_path)
                    if input_file.local_file_name:
                        file_name = input_file.local_file_name
                    env_vars[env_var_name] = os.path.join(SCALE_JOB_EXE_INPUT_PATH, file_input.name, file_name)
        for json_input in self._new_data.values.values():
            if isinstance(file_input, JsonValue):
                env_vars[normalize_env_var_name(json_input.name)] = json_input.value

        return env_vars

    def setup_job_dir(self, data_files):
        """Sets up the directory structure for a job execution and downloads the given files

        :param data_files: Dict with each file parameter name mapping to a bool indicating if the parameter accepts
            multiple files (True) and an absolute directory path
        :type data_files: {string: tuple(bool, string)}
        :returns: Dict with each file parameter name mapping to a list of absolute file paths of the written files
        :rtype: {string: [string]}
        """

        data_files = [SeedInputFiles(x) for x in data_files]
        # Download the job execution input files
        self.retrieve_input_data_files(data_files)


    def validate_input_files(self, files):
        """Validates the given file parameters to make sure they are valid with respect to the job interface.

        :param files: List of Seed Input Files
        :type files: [:class:`job.seed.types.SeedInputFiles`]
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        warnings = []
        for input_file in files:
            name = input_file.name
            required = input_file.required
            file_desc = ScaleFileDescription()

            if name in self._new_data.values:
                if isinstance(self._new_data.values[name], FileValue):
                    # Have this input, make sure it is valid
                    file_input = self._new_data.values[name]
                    file_ids = []

                    for media_type in input_file.media_types:
                        file_desc.add_allowed_media_type(media_type)

                    for file_id in file_input.file_ids:
                        if not isinstance(file_id, Integral):
                            msg = ('Invalid job data: Data input %s must have a list of integers in its "file_ids" '
                                   'field')
                            raise InvalidData(msg % name)
                        file_ids.append(long(file_id))

                    warnings.extend(self._validate_file_ids(file_ids, file_desc))
            else:
                # Don't have this input, check if it is required
                if required:
                    raise InvalidData('Invalid job data: Data input %s is required and was not provided' % name)

        return []

    def validate_input_json(self, input_json):
        """Validates the given property names to ensure they are all populated correctly and exist if they are required.

        :param input_json: List of Seed input json fields
        :type input_json: [:class:`job.seed.types.SeedInputJson`]
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        warnings = []
        for in_js in input_json:
            name = in_js.name
            if name in self._new_data.values:
                if isinstance(self._new_data.values[name], JsonValue):
                    # Have this input, make sure it is a valid property
                    property_input = self._new_data.values[name]
                    value = property_input.value
                    if not isinstance(value, in_js.python_type):
                        msg = 'Invalid job data: Data input %s must have a json type %s in its "value" field'
                        raise InvalidData(msg % (name, in_js.type))
            else:
                # Don't have this input, check if it is required
                if in_js.required:
                    raise InvalidData('Invalid job data: Data input %s is required and was not provided' % name)

        return warnings

    def validate_output_files(self, files):
        """Validates the given file parameters to make sure they are valid with respect to the job interface.

        :param files: List of file parameter names
        :type files: [string]
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        return []

    def _retrieve_files(self, data_files):
        """Retrieves the given data files and writes them to the given local directories. If no file with a given ID
        exists, it will not be retrieved and returned in the results.

        :param data_files: Dict with each file ID mapping to an absolute directory path for downloading and
            bool indicating if job supports partial file download (True).
        :type data_files: {long: type(string, bool)}
        :returns: Dict with each file ID mapping to its absolute local path
        :rtype: {long: string}

        :raises ArchivedWorkspace: If any of the files has an archived workspace (no longer active)
        :raises DeletedFile: If any of the files has been deleted
        """

        file_ids = data_files.keys()
        files = ScaleFile.objects.filter(id__in=file_ids)

        file_downloads = []
        results = {}
        local_paths = set()  # Pay attention to file name collisions and update file name if needed
        counter = 0
        for scale_file in files:
            partial = data_files[scale_file.id][1]
            local_path = os.path.join(data_files[scale_file.id][0], scale_file.file_name)
            while local_path in local_paths:
                # Path collision, try a different file name
                counter += 1
                new_file_name = '%i_%s' % (counter, scale_file.file_name)
                local_path = os.path.join(data_files[scale_file.id][0], new_file_name)
            local_paths.add(local_path)

            file_downloads.append(FileDownload(scale_file, local_path, partial))
            results[scale_file.id] = local_path

        ScaleFile.objects.download_files(file_downloads)

        return results

    def _validate_file_ids(self, file_ids, file_desc):
        """Validates the files with the given IDs against the given file description. If invalid, a
        :class:`job.configuration.data.exceptions.InvalidData` will be thrown.

        :param file_ids: List of file IDs
        :type file_ids: [long]
        :param file_desc: The description of the required file meta-data for validation
        :type file_desc: :class:`job.configuration.interface.scale_file.ScaleFileDescription`
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If any of the files are missing.
        """

        warnings = []
        found_ids = set()
        for scale_file in ScaleFile.objects.filter(id__in=file_ids):
            found_ids.add(scale_file.id)
            media_type = scale_file.media_type
            if not file_desc.is_media_type_allowed(media_type):
                warn = ValidationWarning('media_type',
                                         'Invalid media type for file: %i -> %s' % (scale_file.id, media_type))
                warnings.append(warn)

        # Check if there were any file IDs that weren't found in the query
        for file_id in file_ids:
            if file_id not in found_ids:
                raise InvalidData('Invalid job data: Data file for ID %i does not exist' % file_id)
        return warnings
