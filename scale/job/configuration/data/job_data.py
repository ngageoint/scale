"""Defines the data needed for executing a job"""
from __future__ import unicode_literals

import logging
import os
from numbers import Integral

from job.configuration.data.data_file import DATA_FILE_PARSE_SAVER, DATA_FILE_STORE
from job.configuration.data.exceptions import InvalidData
from job.configuration.results.job_results import JobResults
from job.execution.container import SCALE_JOB_EXE_OUTPUT_PATH

from storage.brokers.broker import FileDownload
from storage.models import ScaleFile


logger = logging.getLogger(__name__)


DEFAULT_VERSION = '1.0'


class ValidationWarning(object):
    """Tracks job data configuration warnings during validation that may not prevent the job from working."""

    def __init__(self, key, details):
        """Constructor sets basic attributes.

        :param key: A unique identifier clients can use to recognize the warning.
        :type key: str
        :param details: A user-friendly description of the problem, including field names and/or associated values.
        :type details: str
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

        self.data_dict = data
        self.param_names = set()
        self.data_inputs_by_name = {}  # str -> dict
        self.data_outputs_by_name = {}  # str -> dict

        if not 'version' in self.data_dict:
            self.data_dict['version'] = DEFAULT_VERSION
        if not self.data_dict['version'] == '1.0':
            raise InvalidData('Invalid job data: %s is an unsupported version number' % self.data_dict['version'])

        if not 'input_data' in self.data_dict:
            self.data_dict['input_data'] = []
        for data_input in self.data_dict['input_data']:
            if not 'name' in data_input:
                raise InvalidData('Invalid job data: Every data input must have a "name" field')
            name = data_input['name']
            if name in self.param_names:
                raise InvalidData('Invalid job data: %s cannot be defined more than once' % name)
            else:
                self.param_names.add(name)
            self.data_inputs_by_name[name] = data_input

        if not 'output_data' in self.data_dict:
            self.data_dict['output_data'] = []
        for data_output in self.data_dict['output_data']:
            if not 'name' in data_output:
                raise InvalidData('Invalid job data: Every data output must have a "name" field')
            name = data_output['name']
            if name in self.param_names:
                raise InvalidData('Invalid job data: %s cannot be defined more than once' % name)
            else:
                self.param_names.add(name)
            self.data_outputs_by_name[name] = data_output

    def add_file_input(self, input_name, file_id):
        """Adds a new file parameter to this job data. This method does not perform validation on the job data.

        :param input_name: The file parameter name
        :type input_name: str
        :param file_id: The ID of the file
        :type file_id: long
        """

        if input_name in self.param_names:
            raise Exception('Data already has a parameter named %s' % input_name)

        self.param_names.add(input_name)
        file_input = {'name': input_name, 'file_id': file_id}
        self.data_dict['input_data'].append(file_input)
        self.data_inputs_by_name[input_name] = file_input

    def add_file_list_input(self, input_name, file_ids):
        """Adds a new files parameter to this job data. This method does not perform validation on the job data.

        :param input_name: The files parameter name
        :type input_name: str
        :param file_ids: The ID of the file
        :type file_ids: list of long
        """

        if input_name in self.param_names:
            raise Exception('Data already has a parameter named %s' % input_name)

        self.param_names.add(input_name)
        files_input = {'name': input_name, 'file_ids': file_ids}
        self.data_dict['input_data'].append(files_input)
        self.data_inputs_by_name[input_name] = files_input

    def add_output(self, output_name, workspace_id):
        """Adds a new output parameter to this job data with a workspace ID. This method does not perform validation on
        the job data.

        :param output_name: The output parameter name
        :type output_name: str
        :param workspace_id: The ID of the workspace
        :type workspace_id: int
        """

        if output_name in self.param_names:
            raise Exception('Data already has a parameter named %s' % output_name)

        self.param_names.add(output_name)
        output = {'name': output_name, 'workspace_id': workspace_id}
        self.data_dict['output_data'].append(output)
        self.data_outputs_by_name[output_name] = output

    def add_property_input(self, input_name, value):
        """Adds a new property parameter to this job data. This method does not perform validation on the job data.

        :param input_name: The property parameter name
        :type input_name: str
        :param value: The value of the property
        :type value: str
        """

        if input_name in self.param_names:
            raise Exception('Data already has a parameter named %s' % input_name)

        self.param_names.add(input_name)
        prop_input = {'name': input_name, 'value': value}
        self.data_dict['input_data'].append(prop_input)
        self.data_inputs_by_name[input_name] = prop_input

    def get_dict(self):
        """Returns the internal dictionary that represents this job data

        :returns: The internal dictionary
        :rtype: dict
        """

        return self.data_dict

    def get_input_file_ids(self):
        """Returns a set of scale file identifiers for each file in the job input data.

        :returns: Set of scale file identifiers
        :rtype: set[int]
        """

        file_ids = set()
        for data_input in self.data_dict['input_data']:
            if 'file_id' in data_input:
                file_ids.add(data_input['file_id'])
            elif 'file_ids' in data_input:
                file_ids.update(data_input['file_ids'])
        return file_ids

    def get_output_workspace_ids(self):
        """Returns a list of the IDs for every workspace used to store the output files for this data

        :returns: List of workspace IDs
        :rtype: list of int
        """

        workspace_ids = set()
        for name in self.data_outputs_by_name:
            file_output = self.data_outputs_by_name[name]
            workspace_id = file_output['workspace_id']
            workspace_ids.add(workspace_id)

        return list(workspace_ids)

    def get_property_values(self, property_names):
        """Retrieves the values contained in this job data for the given property names. If no value is available for a
        property name, it will not be included in the returned dict.

        :param property_names: List of property names
        :type property_names: list of str
        :returns: Dict with each property name mapping to its value
        :rtype: dict of str -> str
        """

        property_values = {}

        for name in property_names:
            if name in self.data_inputs_by_name:
                property_input = self.data_inputs_by_name[name]
                if not 'value' in property_input:
                    raise Exception('Property %s is missing required "value" field' % name)
                property_values[name] = property_input['value']

        return property_values

    def retrieve_input_data_files(self, data_files):
        """Retrieves the given data input files and writes them to the given local directories. Any given file
        parameters that do not appear in the data will not be returned in the results.

        :param data_files: Dict with each file parameter name mapping to a bool indicating if the parameter accepts
            multiple files (True) and an absolute directory path
        :type data_files: dict of str -> tuple(bool, str)
        :returns: Dict with each file parameter name mapping to a list of absolute file paths of the written files
        :rtype: dict of str -> list of str
        """

        # Organize the data files
        param_file_ids = {}  # Parameter name -> list of file IDs
        files_to_retrieve = {}  # File ID -> relative dir path
        for name in data_files:
            multiple = data_files[name][0]
            dir_path = data_files[name][1]
            if name not in self.data_inputs_by_name:
                continue
            file_input = self.data_inputs_by_name[name]
            file_ids = []
            if multiple:
                for file_id in file_input['file_ids']:
                    file_id = long(file_id)
                    file_ids.append(file_id)
                    files_to_retrieve[file_id] = dir_path
            else:
                file_id = long(file_input['file_id'])
                file_ids.append(file_id)
                files_to_retrieve[file_id] = dir_path
            param_file_ids[name] = file_ids

        # Retrieve all files
        retrieved_files = self._retrieve_files(files_to_retrieve)
        for file_id in retrieved_files:
            del files_to_retrieve[file_id]
        if files_to_retrieve:
            msg = 'Failed to retrieve file with ID %i' % files_to_retrieve.keys()[0]
            raise Exception(msg)

        # Organize the results
        retrieved_params = {}  # Parameter name -> list of file paths
        for name in param_file_ids:
            file_path_list = []
            for file_id in param_file_ids[name]:
                file_path_list.append(retrieved_files[file_id])
            retrieved_params[name] = file_path_list

        return retrieved_params

    def save_parse_results(self, parse_results):
        """Saves the given parse results

        :param parse_results: Dict with each input file name mapping to a tuple of GeoJSON containing GIS meta-data
            (optionally None), the start time of the data contained in the file (optionally None), the end time of the
            data contained in the file (optionally None), the list of data types, and the new workspace path (optionally
            None)
        :type parse_results: dict of str -> tuple(str, :class:`datetime.datetime`, :class:`datetime.datetime`, list,
            str, str)
        """

        input_file_ids = []
        for name in self.data_inputs_by_name:
            data_input = self.data_inputs_by_name[name]
            if 'file_ids' in data_input:
                file_ids = data_input['file_ids']
                for file_id in file_ids:
                    input_file_ids.append(file_id)
            elif 'file_id' in data_input:
                file_id = data_input['file_id']
                input_file_ids.append(file_id)

        data_file_parse_saver = DATA_FILE_PARSE_SAVER['DATA_FILE_PARSE_SAVER']
        if not data_file_parse_saver:
            raise Exception('No data file parse saver found')
        data_file_parse_saver.save_parse_results(parse_results, input_file_ids)

    def setup_job_dir(self, data_files):
        """Sets up the directory structure for a job execution and downloads the given files

        :param data_files: Dict with each file parameter name mapping to a bool indicating if the parameter accepts
            multiple files (True) and an absolute directory path
        :type data_files: dict of str -> tuple(bool, str)
        :returns: Dict with each file parameter name mapping to a list of absolute file paths of the written files
        :rtype: dict of str -> list of str
        """

        # Download the job execution input files
        self.retrieve_input_data_files(data_files)

    def store_output_data_files(self, data_files, job_exe):
        """Stores the given data output files

        :param data_files: Dict with each file parameter name mapping to a tuple of absolute local file path and media
            type (media type is optionally None) for a single file parameter and a list of tuples for a multiple file
            parameter
        :type data_files: dict of str -> tuple(str, str) or list of tuple(str, str)
        :param job_exe: The job execution model (with related job and job_type fields) that is storing the output data
            files
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The job results
        :rtype: :class:`job.configuration.results.job_results.JobResults`
        """

        # Organize the data files
        workspace_files = {}  # Workspace ID -> list of (absolute local file path, media type)
        params_by_file_path = {}  # Absolute local file path -> output parameter name
        for name in data_files:
            file_output = self.data_outputs_by_name[name]
            workspace_id = file_output['workspace_id']
            if workspace_id in workspace_files:
                workspace_file_list = workspace_files[workspace_id]
            else:
                workspace_file_list = []
                workspace_files[workspace_id] = workspace_file_list
            data_file_entry = data_files[name]
            if isinstance(data_file_entry, list):
                for file_tuple in data_file_entry:
                    file_path = os.path.normpath(file_tuple[0])
                    if not os.path.isfile(file_path):
                        raise Exception('%s is not a valid file' % file_path)
                    params_by_file_path[file_path] = name
                    # Adjust file path to be relative to upload_dir
                    if len(file_tuple) == 2:
                        new_tuple = (file_path, file_tuple[1])
                    else:
                        new_tuple = (file_path, file_tuple[1], file_tuple[2])
                    workspace_file_list.append(new_tuple)
            else:
                file_path = os.path.normpath(data_file_entry[0])
                if not os.path.isfile(file_path):
                    raise Exception('%s is not a valid file' % file_path)
                params_by_file_path[file_path] = name
                # Adjust file path to be relative to upload_dir
                if len(data_file_entry) == 2:
                    new_tuple = (file_path, data_file_entry[1])
                else:
                    new_tuple = (file_path, data_file_entry[1], data_file_entry[2])
                workspace_file_list.append(new_tuple)

        data_file_store = DATA_FILE_STORE['DATA_FILE_STORE']
        if not data_file_store:
            raise Exception('No data file store found')
        stored_files = data_file_store.store_files(workspace_files, self.get_input_file_ids(), job_exe)

        # Organize results
        param_file_ids = {}  # Output parameter name -> file ID or list of file IDs
        for file_path in stored_files:
            file_id = stored_files[file_path]
            name = params_by_file_path[file_path]
            if isinstance(data_files[name], list):
                if name in param_file_ids:
                    file_id_list = param_file_ids[name]
                else:
                    file_id_list = []
                    param_file_ids[name] = file_id_list
                file_id_list.append(file_id)
            else:
                param_file_ids[name] = file_id

        # Create job results
        results = JobResults()
        for name in param_file_ids:
            param_entry = param_file_ids[name]
            if isinstance(param_entry, list):
                results.add_file_list_parameter(name, param_entry)
            else:
                results.add_file_parameter(name, param_entry)
        return results

    def validate_input_files(self, files):
        """Validates the given file parameters to make sure they are valid with respect to the job interface.

        :param files: Dict of file parameter names mapped to a tuple with three items: whether the parameter is required
            (True), if the parameter is for multiple files (True), and the description of the expected file meta-data
        :type files: dict of str ->
            tuple(bool, bool, :class:`job.configuration.interface.scale_file.ScaleFileDescription`)
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        warnings = []
        for name in files:
            required = files[name][0]
            multiple = files[name][1]
            file_desc = files[name][2]
            if name in self.data_inputs_by_name:
                # Have this input, make sure it is valid
                file_input = self.data_inputs_by_name[name]
                file_ids = []
                if multiple:
                    if not 'file_ids' in file_input:
                        if 'file_id' in file_input:
                            file_input['file_ids'] = [file_input['file_id']]
                        else:
                            msg = 'Invalid job data: Data input %s is a list of files and must have a "file_ids" or ' \
                            '"file_id" field'
                            raise InvalidData(msg % name)
                    if 'file_id' in file_input:
                        del file_input['file_id']
                    value = file_input['file_ids']
                    if not isinstance(value, list):
                        msg = 'Invalid job data: Data input %s must have a list of integers in its "file_ids" field'
                        raise InvalidData(msg % name)
                    for file_id in value:
                        if not isinstance(file_id, Integral):
                            msg = 'Invalid job data: Data input %s must have a list of integers in its "file_ids" ' \
                            'field'
                            raise InvalidData(msg % name)
                        file_ids.append(long(file_id))
                else:
                    if not 'file_id' in file_input:
                        msg = 'Invalid job data: Data input %s is a file and must have a "file_id" field' % name
                        raise InvalidData(msg)
                    if 'file_ids' in file_input:
                        del file_input['file_ids']
                    file_id = file_input['file_id']
                    if not isinstance(file_id, Integral):
                        msg = 'Invalid job data: Data input %s must have an integer in its "file_id" field' % name
                        raise InvalidData(msg)
                    file_ids.append(long(file_id))
                warnings.extend(self._validate_file_ids(file_ids, file_desc))
            else:
                # Don't have this input, check if it is required
                if required:
                    raise InvalidData('Invalid job data: Data input %s is required and was not provided' % name)
        return warnings

    def validate_output_files(self, files):
        """Validates the given file parameters to make sure they are valid with respect to the job interface.

        :param files: List of file parameter names
        :type files: list of str
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        warnings = []
        workspace_ids = set()
        for name in files:
            if not name in self.data_outputs_by_name:
                raise InvalidData('Invalid job data: Data output %s was not provided' % name)
            file_output = self.data_outputs_by_name[name]
            if not 'workspace_id' in file_output:
                raise InvalidData('Invalid job data: Data output %s must have a "workspace_id" field' % name)
            workspace_id = file_output['workspace_id']
            if not isinstance(workspace_id, Integral):
                msg = 'Invalid job data: Data output %s must have an integer in its "workspace_id" field' % name
                raise InvalidData(msg)
            workspace_ids.add(workspace_id)

        data_file_store = DATA_FILE_STORE['DATA_FILE_STORE']
        if not data_file_store:
            raise Exception('No data file store found')
        workspaces = data_file_store.get_workspaces(workspace_ids)

        for workspace_id in workspaces:
            active = workspaces[workspace_id]
            if not active:
                raise InvalidData('Invalid job data: Workspace for ID %i is not active' % workspace_id)
            workspace_ids.remove(workspace_id)

        # Check if there were any workspace IDs that weren't found
        if workspace_ids:
            raise InvalidData('Invalid job data: Workspace for ID(s): %s do not exist' % str(workspace_ids))
        return warnings

    def validate_properties(self, property_names):
        """Validates the given property names to ensure they are all populated correctly and exist if they are required.

        :param property_names: Dict of property names mapped to a bool indicating if they are required
        :type property_names: dict of str -> bool
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        warnings = []
        for name in property_names:
            if name in self.data_inputs_by_name:
                # Have this input, make sure it is a valid property
                property_input = self.data_inputs_by_name[name]
                if not 'value' in property_input:
                    msg = 'Invalid job data: Data input %s is a property and must have a "value" field' % name
                    raise InvalidData(msg)
                value = property_input['value']
                if not isinstance(value, basestring):
                    raise InvalidData('Invalid job data: Data input %s must have a string in its "value" field' % name)
            else:
                # Don't have this input, check if it is required
                if property_names[name]:
                    raise InvalidData('Invalid job data: Data input %s is required and was not provided' % name)
        return warnings

    def _retrieve_files(self, data_files):
        """Retrieves the given data files and writes them to the given local directories. If no file with a given ID
        exists, it will not be retrieved and returned in the results.

        :param data_files: Dict with each file ID mapping to an absolute directory path for downloading
        :type data_files: dict of long -> string
        :returns: Dict with each file ID mapping to its absolute local path
        :rtype: dict of long -> string

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
            local_path = os.path.join(data_files[scale_file.id], scale_file.file_name)
            while local_path in local_paths:
                # Path collision, try a different file name
                counter += 1
                new_file_name = '%i_%s' % (counter, scale_file.file_name)
                local_path = os.path.join(data_files[scale_file.id], new_file_name)
            local_paths.add(local_path)
            file_downloads.append(FileDownload(scale_file, local_path))
            results[scale_file.id] = local_path

        ScaleFile.objects.download_files(file_downloads)

        return results

    def _validate_file_ids(self, file_ids, file_desc):
        """Validates the files with the given IDs against the given file description. If invalid, a
        :class:`job.configuration.data.exceptions.InvalidData` will be thrown.

        :param file_ids: List of file IDs
        :type file_ids: list of long
        :param file_desc: The description of the required file meta-data for validation
        :type file_desc: :class:`job.configuration.interface.scale_file.ScaleFileDescription`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

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
