"""Defines the data needed for executing a recipe"""
from __future__ import unicode_literals

import logging
from copy import deepcopy

from numbers import Integral

from job.configuration.data.data_file import DATA_FILE_STORE
from job.configuration.interface.scale_file import ScaleFileDescription
from job.data.types import JobDataInputFiles, JobDataInputJson
from recipe.configuration.data.exceptions import InvalidRecipeData
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


class RecipeData(object):
    """Represents the data needed for executing a recipe. Data includes details about the data inputs, links needed to
    connect shared resources to resource instances in Scale, and details needed to store all resulting output.
    """

    def __init__(self, data=None):
        """Creates a job data object from the given dictionary. The general format is checked for correctness, but the
        actual input and output details are not checked for correctness against the job interface. If the data is
        invalid, a :class:`job.configuration.data.exceptions.InvalidRecipeData` will be thrown.

        :param data: The job data
        :type data: dict
        """

        if not data:
            data = {}

        self._data = data
        self._data_names = {}  # str -> `JobDataFields`
        self._input_json = {}  # str -> `JobDataInputJson`
        self._input_files = {}  # str -> `JobDataInputFiles`

        if 'version' not in self._data:
            self._data['version'] = DEFAULT_VERSION
        if not self._data['version'] == '2.0':
            raise InvalidRecipeData('%s is an unsupported version number' % self._data['version'])

        if 'workspace_id' in self._data:
            workspace_id = self._data['workspace_id']
            if not isinstance(workspace_id, Integral):
                raise InvalidRecipeData('Workspace ID must be an integer')

        # Add structure placeholders
        if 'input_data' not in self._data:
            self._data['input_data'] = {}
        if 'files' not in self._data['input_data']:
            self._data['input_data']['files'] = []
        if 'json' not in self._data['input_data']:
            self._data['input_data']['json'] = []

        for data_input in self._data['input_data']['files']:
            self._add_file_input(data_input, False)
        for data_input in self._data['input_data']['json']:
            self.add_json_input(data_input, False)

    def add_file_input(self, name, file_id):
        """Adds a new file parameter to this job data.

        :param data: The files parameter dict
        :type data: dict
        :param add_to_internal: Whether we should add to private data dict. Unneeded when used from __init__
        :type add_to_internal: bool
        """

        self._add_file_input({'name':name, 'file_ids': [file_id]})

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

    def _add_file_input(self, data, add_to_internal=True):
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
        for data_input in self._input_files.itervalues():
            for id in data_input.file_ids:
                file_ids.add(id)
        return file_ids

    def get_input_file_ids_by_input(self):
        """Returns the list of file IDs for each input that holds files

        :returns: Dict where each file input name maps to its list of file IDs
        :rtype: dict
        """

        file_ids = {}
        for data_input in self._input_files.itervalues():
            if data_input.file_ids:
                file_ids[data_input.name] = data_input.file_ids
        return file_ids

    def get_input_file_info(self):
        """Returns a set of scale file identifiers and input names for each file in the job input data.

        :returns: Set of scale file identifiers and names
        :rtype: set[tuple]
        """

        file_info = set()

        for data_input in self._input_files.itervalues():
            if data_input.file_ids:
                for file_id in data_input.file_ids:
                    file_info.add((file_id, data_input.name))

        return file_info

    def get_workspace_id(self):
        """Returns the workspace ID in the recipe data

        :returns: The workspace ID
        :rtype: int
        """

        return self._data['workspace_id']

    def set_workspace_id(self, workspace_id):
        """Set the workspace ID in the recipe data.

        :param workspace_id: The new workspace ID
        :type workspace_id: int

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the workspace ID is an invalid type
        """
        if not isinstance(workspace_id, Integral):
            raise InvalidRecipeData('Workspace ID must be an integer')
        self._data['workspace_id'] = workspace_id

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

    def get_injected_input_values(self, input_files):
        """Apply all execution time values to job data

        TODO: Remove with v6 when old style Job Types are removed

        :param input_files: Mapping of input names to InputFiles
        :type input_files: {str, :class:`job.configuration.input_file.InputFile`}
        :return: Mapping of all input keys to their true file / property values
        :rtype: {str, str}
        """
        input_values = {}

        # No data is created here, as this is only used for parameter injection into command args.
        # Environment variables injection is done under get_injected_env_vars

        return input_values

    def validate_input_files(self, files):
        """Validates the given file parameters to make sure they are valid with respect to the job interface.

        :param files: List of Seed Input Files
        :type files: [:class:`job.seed.types.SeedInputFiles`]
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidRecipeData`: If there is a configuration problem.
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
                        msg = ('Invalid recipe data: Data input %s must have a list of integers in its "file_ids" '
                               'field')
                        raise InvalidRecipeData(msg % name)
                    file_ids.append(long(file_id))

                warnings.extend(self._validate_file_ids(file_ids, file_desc))
            else:
                # Don't have this input, check if it is required
                if required:
                    raise InvalidRecipeData('Invalid recipe data: Data input %s is required and was not provided' % name)

        # Handle extra inputs in the data that are not defined in the interface
        for name in deepcopy(self._input_files):
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

        :raises :class:`job.configuration.data.exceptions.InvalidRecipeData`: If there is a configuration problem.
        """

        warnings = []
        for in_js in input_json:
            name = in_js.name
            if name in self._input_json:
                # Have this input, make sure it is a valid property
                property_input = self._input_json[name]
                value = property_input.value
                if not isinstance(value, in_js.python_type):
                    raise InvalidRecipeData('Invalid recipe data: Data input %s must have a json type %s in its "value" field' %
                                      (name, in_js.type))
            else:
                # Don't have this input, check if it is required
                if in_js.required:
                    raise InvalidRecipeData('Invalid recipe data: Data input %s is required and was not provided' % name)

        # Handle extra inputs in the data that are not defined in the interface
        for name in list(self._input_json.keys()):
            if name not in [x.name for x in input_json]:
                warn = ValidationWarning('unknown_input', 'Unknown input %s will be ignored' % name)
                warnings.append(warn)
                self._delete_input(name)

        return warnings

    def validate_workspace(self):
        """Validates the given file parameters to make sure they are valid with respect to the job interface

        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`recipe.configuration.data.recipe_data.ValidationWarning`]

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the workspace is missing or invalid
        """

        warnings = []
        if not 'workspace_id' in self._data:
            raise InvalidRecipeData('Invalid recipe data: Workspace ID is needed and was not provided')
        workspace_id = self._data['workspace_id']

        data_file_store = DATA_FILE_STORE['DATA_FILE_STORE']
        if not data_file_store:
            raise Exception('No data file store found')
        workspaces = data_file_store.get_workspaces([workspace_id])

        if not workspaces:
            raise InvalidRecipeData('Invalid recipe data: Workspace for ID %i does not exist' % workspace_id)
        active = workspaces[workspace_id]
        if not active:
            raise InvalidRecipeData('Invalid recipe data: Workspace for ID %i is not active' % workspace_id)
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

    def _validate_file_ids(self, file_ids, file_desc):
        """Validates the files with the given IDs against the given file description. If invalid, a
        :class:`job.configuration.data.exceptions.InvalidRecipeData` will be thrown.

        :param file_ids: List of file IDs
        :type file_ids: [long]
        :param file_desc: The description of the required file meta-data for validation
        :type file_desc: :class:`job.configuration.interface.scale_file.ScaleFileDescription`
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidRecipeData`: If any of the files are missing.
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
                raise InvalidRecipeData('Invalid recipe data: Data file for ID %i does not exist' % file_id)
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
            raise InvalidRecipeData('Every RecipeData input must have a "name" field.')
        name = data['name']
        if name in self._data_names:
            raise InvalidRecipeData('%s cannot be defined more than once.' % name)

        if field_name not in data:
            raise InvalidRecipeData('Expected field %s was missing.' % field_name)

