"""Defines the data needed for executing a job"""
from __future__ import unicode_literals

import json
import logging
import os
from abc import ABCMeta
from numbers import Integral

from job.configuration.data.data_file import DATA_FILE_STORE
from job.configuration.data.exceptions import InvalidData
from job.configuration.interface.scale_file import ScaleFileDescription
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH
from job.seed.metadata import SeedMetadata, METADATA_SUFFIX
from job.seed.results.job_results import JobResults
from job.seed.results.outputs_json import SeedOutputsJson, SEED_OUPUTS_JSON_FILENAME
from job.seed.types import SeedInputFiles, SeedOutputFiles
from product.models import ProductFileMetadata
from storage.brokers.broker import FileDownload
from storage.models import ScaleFile

logger = logging.getLogger(__name__)

DEFAULT_VERSION = '2.0'


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


class JobDataFields(object):
    __metaclass__ = ABCMeta

    def __init__(self, data):
        self.dict = data

    def __repr__(self):
        return self.dict

    @property
    def name(self):
        return self.dict['name']


class JobDataInputFiles(JobDataFields):
    @property
    def file_ids(self):
        return self.dict['file_ids']


class JobDataInputJson(JobDataFields):
    @property
    def value(self):
        return self.dict['value']


class JobDataOutputFiles(JobDataFields):
    @property
    def workspace_id(self):
        return self.dict['workspace_id']


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

        self._data = data
        self._data_names = {}  # str -> `JobDataFields`
        self._output_files = {}  # str -> `JobDataOutputFiles`
        self._input_json = {}  # str -> `JobDataInputJson`
        self._input_files = {}  # str -> `JobDataInputFiles`

        if 'version' not in self._data:
            self._data['version'] = DEFAULT_VERSION
        if not self._data['version'] == '2.0':
            raise InvalidData('Invalid job data: %s is an unsupported version number' % self._data['version'])

        # Add structure placeholders
        if 'input_data' not in self._data:
            self._data['input_data'] = {}
        if 'files' not in self._data['input_data']:
            self._data['input_data']['files'] = []
        if 'json' not in self._data['input_data']:
            self._data['input_data']['json'] = []
        if 'output_data' not in self._data:
            self._data['output_data'] = {}
        if 'files' not in self._data['output_data']:
            self._data['output_data']['files'] = []

        for data_input in self._data['input_data']['files']:
            self.add_file_input(data_input, False)
        for data_input in self._data['input_data']['json']:
            self.add_json_input(data_input, False)
        for data_output in self._data['output_data']['files']:
            self.add_file_output(data_output, False)

    def add_file_input(self, data, add_to_internal=True):
        """Adds a new file parameter to this job data.

        :param data: The files parameter dict
        :type data: dict
        :param add_to_internal: Whether we should add to private data dict. Unneeded when used from __init__
        :type add_to_internal: bool
        """

        self._validate_job_data_field(data, 'file_ids')
        input = JobDataInputFiles(data)
        if add_to_internal:
            self._data['input_data']['files'].append(data)
        self._data_names[input.name] = input
        self._input_files[input.name] = input

    def add_json_input(self, data, add_to_internal=True):
        """Adds a new json parameter to this job data.

        :param data: The json parameter dict
        :type data: dict
        :param add_to_internal: Whether we should add to private data dict. Unneeded when used from __init__
        :type add_to_internal: bool
        """

        self._validate_job_data_field(data, 'value')
        input = JobDataInputJson(data)
        if add_to_internal:
            self._data['input_data']['json'].append(data)
        self._data_names[input.name] = input
        self._input_json[input.name] = input

    def add_file_output(self, data, add_to_internal=True):
        """Adds a new output files to this job data with a workspace ID.

        :param data: The output parameter dict
        :type data: dict
        :param add_to_internal: Whether we should add to private data dict. Unneeded when used from __init__
        :type add_to_internal: bool
        """

        self._validate_job_data_field(data, 'workspace_id')
        output = JobDataOutputFiles(data)
        if add_to_internal:
            self._data['output_data']['files'].append(data)
        self._data_names[output.name] = output
        self._output_files[output.name] = output

    def capture_output_files(self, output_files):
        """Evaluate files patterns and capture any available side-car metadata associated with matched files

        :param output_files: interface definition of Seed output files that should be captured
        :type output_files: list
        :return: collection of files name keys mapped to a ProductFileMetadata list. { name : [`ProductFileMetadata`]
        :rtype: dict
        """

        seed_output_files = [SeedOutputFiles(x) for x in output_files]

        # Dict of detected files and associated metadata
        captured_files = {}

        # Iterate over each files object
        for output_file in seed_output_files:
            # For files obj that are detected, handle results (may be multiple)
            product_files = []
            for matched_file in output_file.get_files():

                product_file_meta = ProductFileMetadata(output_file.name, matched_file, output_file.media_type)

                # check to see if there is side-car metadata files
                metadata_file = os.path.join(matched_file, METADATA_SUFFIX)

                # If metadata is found, attempt to grab any Scale relevant data and place in ProductFileMetadata tuple
                if os.path.isfile(metadata_file):
                    with open(metadata_file) as metadata_file_handle:
                        metadata = SeedMetadata(json.load(metadata_file_handle))

                        # Create a GeoJSON object, as the present Seed Metadata schema only uses the Geometry fragment
                        # TODO: Update if Seed schema updates.  Ref: https://github.com/ngageoint/seed/issues/95
                        product_file_meta.geojson = \
                            {
                                'type': 'Feature',
                                'geometry': metadata.get_geometry()
                            }

                        timestamp = metadata.get_time()

                        # Seed Metadata Schema defines start / end as required
                        # so we do not need to check here.
                        if timestamp:
                            product_file_meta.data_start = timestamp['start']
                            product_file_meta.data_end = timestamp['end']

                product_files.append(product_file_meta)

            captured_files[output_file.name] = product_files

        return captured_files

    def get_all_properties(self):
        """Retrieves all properties from this job data and returns them in ascending order of their names

        :returns: List of strings containing name=value
        :rtype: [string]
        """

        properties = []

        names = sorted(self._input_json.keys())
        for name in names:
            properties.append(name + '=' + self._input_json[name].value)

        return properties

    def get_dict(self):
        """Returns the internal dictionary that represents this job data

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._data

    def get_input_file_ids(self):
        """Returns a set of scale file identifiers for each file in the job input data.

        :returns: Set of scale file identifiers
        :rtype: {int}
        """

        file_ids = set()
        for data_input in self._data['input_data']['files']:
            if 'file_ids' in data_input:
                file_ids.add(data_input.file_ids)
        return file_ids

    def get_input_file_ids_by_input(self):
        """Returns the list of file IDs for each input that holds files

        :returns: Dict where each file input name maps to its list of file IDs
        :rtype: dict
        """

        file_ids = {}
        for data_input in self._data['input_data']['files']:
            if data_input.file_ids:
                file_ids[data_input.name] = data_input.file_ids
                file_ids[data_input['name']] = [data_input['file_id']]
        return file_ids

    def get_input_file_info(self):
        """Returns a set of scale file identifiers and input names for each file in the job input data.

        :returns: Set of scale file identifiers and names
        :rtype: set[tuple]
        """

        file_info = set()

        for data_input in self._data['input_data']['files']:
            if data_input.file_ids:
                for file_id in data_input.file_ids:
                    file_info.add((file_id, data_input.name))

        return file_info

    def get_output_workspace_ids(self):
        """Returns a list of the IDs for every workspace used to store the output files for this data

        :returns: List of workspace IDs
        :rtype: [int]
        """

        workspace_ids = set()
        for output in self._output_files.itervalues():
            workspace_ids.add(output.workspace_id)

        return list(workspace_ids)

    def get_output_workspaces(self):
        """Returns a dict of the output parameter names mapped to their output workspace ID

        :returns: A dict mapping output parameters to workspace IDs
        :rtype: dict
        """

        workspaces = {}
        for output in self._output_files.itervalues():
            workspaces[output.name] = output.workspace_id

        return workspaces

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
            if name in self._input_json:
                property_values[name] = self._input_json[name].value

        return property_values

    def retrieve_input_data_files(self, data_files):
        """Retrieves the given data input files and writes them to the given local directories. Any given file
        parameters that do not appear in the data will not be returned in the results.

        :param data_files: Dict with each file parameter name mapping to a bool indicating if the parameter accepts
            multiple files (True), an absolute directory path and bool indicating if job supports partial file
            download (True).
        :type data_files: {string: tuple(bool, string, bool)}
        :returns: Dict with each file parameter name mapping to a list of absolute file paths of the written files
        :rtype: {string: [string]}
        """

        # Organize the data files
        param_file_ids = {}  # Parameter name -> [file IDs]
        files_to_retrieve = {}  # File ID -> tuple(string, bool) for relative dir path and if partially accessed
        for data_file in data_files:
            input_name = data_file.name
            multiple = data_file.multiple
            dir_path = os.path.join(SCALE_JOB_EXE_INPUT_PATH, self._input_files[input_name])
            partial = data_file.partial
            if data_file.name not in self._data_names:
                continue
            file_input = self._data_names[data_file.name]
            file_ids = []
            if not multiple and len(file_input) > 1:
                raise Exception('Multiple inputs detected for input %s that does not support.' % (data_file.name,))
            for file_id in file_input:
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


    def capture_output_json(self, output_json_interface):
        """

        :param output_json_interface:
        :return:
        """
        # Identify any outputs from seed.outputs.json
        schema = SeedOutputsJson.construct_schema(output_json_interface)
        outputs = SeedOutputsJson.read_outputs(schema)
        seed_outputs_json = outputs.get_values()

        json_results = {}
        for key, value in seed_outputs_json.iteritems():

            if key in [x.json_key for x in output_json_interface]:
                json_results[key] = value
            else:
                logger.warning("Skipping capture of key '%s' in %s not found in interface." %
                               (key, SEED_OUPUTS_JSON_FILENAME))

        return json_results

    def store_output_data_files(self, data_files, outputs_json_interface, job_exe):
        """Stores the given output data

        :param data_files: Dict with each file parameter name mapping to a ProductFileMetadata class
        :type data_files: {string: ProductFileMetadata)
        :param outputs_json_interface: List of output json interface objects
        :type outputs_json_interface: [:class:`job.seed.types.SeedOutputJson`]
        :param job_exe: The job execution model (with related job and job_type fields) that is storing the output data
            files
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The job results
        :rtype: :class:`job.configuration.results.job_results.JobResults`
        """

        # Organize the data files
        workspace_files = {}  # Workspace ID -> [`ProductFileMetadata`]
        params_by_file_path = {}  # Absolute local file path -> output parameter name
        for name in data_files:
            file_output = self._output_files[name]
            workspace_id = file_output.workspace_id
            if workspace_id in workspace_files:
                workspace_file_list = workspace_files[workspace_id]
            else:
                workspace_file_list = []
                workspace_files[workspace_id] = workspace_file_list
            data_file_entry = data_files[name]
            for entry in data_file_entry:
                file_path = os.path.normpath(entry.local_path)
                if not os.path.isfile(file_path):
                    raise Exception('%s is not a valid file' % file_path)
                params_by_file_path[file_path] = name
                workspace_file_list.append(entry)

        data_file_store = DATA_FILE_STORE['DATA_FILE_STORE']
        if not data_file_store:
            raise Exception('No data file store found')
        stored_files = data_file_store.store_files(workspace_files, self.get_input_file_ids(), job_exe)

        # Organize results
        param_file_ids = {}  # Output parameter name -> file ID or [file IDs]
        for file_path in stored_files:
            file_id = stored_files[file_path]
            name = params_by_file_path[file_path]
            if name in param_file_ids:
                file_id_list = param_file_ids[name]
            else:
                file_id_list = []
                param_file_ids[name] = file_id_list
            file_id_list.append(file_id)

        # Create job results
        results = JobResults()
        for name in param_file_ids:
            param_entry = param_file_ids[name]
            results.add_file_list_parameter(name, param_entry)

        # Identify any outputs from seed.outputs.json
        try:
            schema = SeedOutputsJson.construct_schema(outputs_json_interface)
            outputs = SeedOutputsJson.read_outputs(schema)
            seed_outputs_json = outputs.get_values()

            for key in seed_outputs_json:
                results.add_output_json(key, seed_outputs_json[key])
        except IOError:
            logger.exception('No seed.outputs.json file found to process.')

        return results

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

            if name in self._input_files:
                # Have this input, make sure it is valid
                file_input = self._input_files[name]
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

        # Handle extra inputs in the data that are not defined in the interface
        for name in self._input_files:
            if name not in [x.name for x in files]:
                warn = ValidationWarning('unknown_input', 'Unknown input %s will be ignored' % name)
                warnings.append(warn)
                self._delete_input(name)

        return warnings

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
            if name in self._input_json:
                # Have this input, make sure it is a valid property
                property_input = self._input_json[name]
                value = property_input.value
                if not isinstance(value, in_js.python_type):
                    raise InvalidData('Invalid job data: Data input %s must have a json type %s in its "value" field' %
                                      (name, in_js.type))
            else:
                # Don't have this input, check if it is required
                if in_js.required:
                    raise InvalidData('Invalid job data: Data input %s is required and was not provided' % name)

        # Handle extra inputs in the data that are not defined in the interface
        for name in list(self._input_json.keys()):
            if name not in [x.name for x in input_json]:
                warn = ValidationWarning('unknown_input', 'Unknown input %s will be ignored' % name)
                warnings.append(warn)
                self._delete_input(name)

        return warnings

    def validate_output_files(self, files):
        """Validates the given file parameters to make sure they are valid with respect to the job interface.

        :param files: List of file parameter names
        :type files: [string]
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        """

        warnings = []
        workspace_ids = set()
        output_files = self._data['output_data']['files']
        outputs_by_name = {k.name: output_files[k] for k in output_files}  # Output Name -> `JobDataOutputFiles`
        for name in files:
            if name not in outputs_by_name:
                raise InvalidData('Invalid job data: Data output %s was not provided' % name)
            file_output = outputs_by_name[name]
            if 'workspace_id' not in file_output:
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

    def _delete_input(self, name):
        """Deletes the input with the given name

        :param name: The name of the input to delete
        :type name: string
        """

        if name in self._input_files:
            self._data['input_data']['files'] = self._delete_by_name(self._data['input_data']['files'], name)
            del self._input_files[name]
            del self._data_names[name]
        elif name in self._input_json:
            self._data['input_data']['json'] = self._delete_by_name(self._data['input_data']['json'], name)
            del self._input_json[name]
            del self._data_names[name]

    def _delete_by_name(self, collection, name):
        """Traverse a list of dicts and return list that omits the dict with a 'name' value match

        :param collection: Original list to removal dict from
        :type collection: [dict]
        :param name: Value for name key that should be omitted
        :type name: str
        :return: List without dict matching on 'name' key value
        :rtype: [dict]
        """
        return [d for d in collection if d.get('name') != name]

    def _get_name_mapped_dict(self, collection, type):
        """Get a dictionary from a given collection

        :param collection:
        :param type:
        :return:
        """

        return {k: collection[k] for k in collection if isinstance(collection[k], type)}

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

    def _validate_job_data_field(self, data, field_name):
        """Validate a JobData input or output field for required fields

        :param data: Input or output data field
        :type data: dict
        :param field_name: Name of field that describes additional input / output metadata
        :type field_name: basestring
        :return:
        """
        if 'name' not in data:
            raise InvalidData('Every JobData input / output must have a "name" field.')
        name = data['name']
        if name in self._data_names:
            raise InvalidData('%s cannot be defined more than once.' % name)

        if field_name not in data:
            raise InvalidData('Expected field %s was missing.' % field_name)
