'''Defines the data needed for executing a recipe'''
from numbers import Integral

from job.configuration.data.data_file import DATA_FILE_STORE
from recipe.configuration.data.exceptions import InvalidData
from storage.models import ScaleFile


DEFAULT_VERSION = u'1.0'


class ValidationWarning(object):
    '''Tracks recipe data configuration warnings during validation that may not prevent the recipe from working.'''

    def __init__(self, key, details):
        '''Constructor sets basic attributes.

        :param key: A unique identifier clients can use to recognize the warning.
        :type key: str
        :param details: A user-friendly description of the problem, including field names and/or associated values.
        :type details: str
        '''
        self.key = key
        self.details = details


class RecipeData(object):
    '''Represents the data needed for executing a recipe. Data includes details about the data inputs, links needed to
    connect shared resources to resource instances in Scale, and details needed to store all resulting output.
    '''

    def __init__(self, data):
        '''Creates a recipe data object from the given dictionary. The general format is checked for correctness, but
        the actual input and output details are not checked for correctness against the recipe definition.

        :param data: The recipe data
        :type data: dict

        :raises InvalidData: If the recipe data is invalid
        '''

        self.data_dict = data
        self.param_names = set()
        self.data_inputs_by_name = {}  # str -> dict

        if not u'version' in self.data_dict:
            self.data_dict[u'version'] = DEFAULT_VERSION
        if not self.data_dict[u'version'] == u'1.0':
            raise InvalidData(u'Invalid recipe data: %s is an unsupported version number' % self.data_dict[u'version'])

        if not u'input_data' in self.data_dict:
            self.data_dict[u'input_data'] = []
        for data_input in self.data_dict[u'input_data']:
            if not u'name' in data_input:
                raise InvalidData(u'Invalid recipe data: Every data input must have a "name" field')
            name = data_input[u'name']
            if name in self.param_names:
                raise InvalidData(u'Invalid recipe data: %s cannot be defined more than once' % name)
            else:
                self.param_names.add(name)
            self.data_inputs_by_name[name] = data_input

        if u'workspace_id' in self.data_dict:
            workspace_id = self.data_dict[u'workspace_id']
            if not isinstance(workspace_id, Integral):
                raise InvalidData(u'Invalid recipe data: Workspace ID must be an integer')

    def add_file_input(self, input_name, file_id):
        '''Adds a new file parameter to this recipe data.
        This method does not perform validation on the recipe data.

        :param input_name: The file parameter name
        :type input_name: str
        :param file_id: The ID of the file
        :type file_id: long
        '''

        if input_name in self.param_names:
            raise Exception(u'Data already has a parameter named %s' % input_name)

        self.param_names.add(input_name)
        file_input = {u'name': input_name, u'file_id': file_id}
        self.data_dict[u'input_data'].append(file_input)
        self.data_inputs_by_name[input_name] = file_input

    def add_input_to_data(self, recipe_input_name, job_data, job_input_name):
        '''Adds the given input from the recipe data as a new input to the given job data

        :param recipe_input_name: The name of the recipe data input to add to the job data
        :type recipe_input_name: str
        :param job_data: The job data
        :type job_data: :class:`job.configuration.data.job_data.JobData`
        :param job_input_name: The name of the job data input to add
        :type job_input_name: str
        '''

        if recipe_input_name in self.data_inputs_by_name:
            recipe_input = self.data_inputs_by_name[recipe_input_name]
            if u'value' in recipe_input:
                value = recipe_input[u'value']
                job_data.add_property_input(job_input_name, value)
            elif u'file_id' in recipe_input:
                file_id = recipe_input[u'file_id']
                job_data.add_file_input(job_input_name, file_id)
            elif u'file_ids' in recipe_input:
                file_ids = recipe_input[u'file_ids']
                job_data.add_file_list_input(job_input_name, file_ids)

    def get_input_file_ids(self):
        '''Returns a set of scale file identifiers for each file in the recipe input data.

        :returns: Set of scale file identifiers
        :rtype: set[int]
        '''

        file_ids = set()
        for data_input in self.data_dict[u'input_data']:
            if u'file_id' in data_input:
                file_ids.add(data_input[u'file_id'])
            elif u'file_ids' in data_input:
                file_ids.update(data_input[u'file_ids'])
        return file_ids

    def get_workspace_id(self):
        '''Returns the workspace ID in the recipe data

        :returns: The workspace ID
        :rtype: int
        '''

        return self.data_dict[u'workspace_id']

    def set_workspace_id(self, workspace_id):
        '''Set the workspace ID in the recipe data.

        :param workspace_id: The new workspace ID
        :type workspace_id: int

        :raises InvalidData: If the workspace id is an invalid type
        '''
        if not isinstance(workspace_id, Integral):
            raise InvalidData(u'Workspace ID must be an integer')
        self.data_dict[u'workspace_id'] = workspace_id

    def get_dict(self):
        '''Returns the internal dictionary that represents this recipe data

        :returns: The internal dictionary
        :rtype: dict
        '''

        return self.data_dict

    def validate_input_files(self, files):
        '''Validates the given file parameters to make sure they are valid with respect to the job interface

        :param files: Dict of file parameter names mapped to a tuple with three items: whether the parameter is required
            (True), if the parameter is for multiple files (True), and the description of the expected file meta-data
        :type files: dict of str ->
            tuple(bool, bool, :class:`job.configuration.interface.scale_file.ScaleFileDescription`)
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`recipe.configuration.data.recipe_data.ValidationWarning`]

        :raises :class:`recipe.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        '''

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
                    if not u'file_ids' in file_input:
                        if u'file_id' in file_input:
                            file_input[u'file_ids'] = [file_input[u'file_id']]
                        else:
                            msg = u'Invalid recipe data: Data input %s is a list of files and must have a "file_ids" ' \
                            'or "file_id" field'
                            raise InvalidData(msg % name)
                    if u'file_id' in file_input:
                        del file_input[u'file_id']
                    value = file_input[u'file_ids']
                    if not isinstance(value, list):
                        msg = u'Invalid recipe data: Data input %s must have a list of integers in its "file_ids" field'
                        raise InvalidData(msg % name)
                    for file_id in value:
                        if not isinstance(file_id, Integral):
                            msg = u'Invalid recipe data: Data input %s must have a list of integers in its "file_ids"' \
                            'field'
                            raise InvalidData(msg % name)
                        file_ids.append(long(file_id))
                else:
                    if not u'file_id' in file_input:
                        msg = u'Invalid recipe data: Data input %s is a file and must have a "file_id" field' % name
                        raise InvalidData(msg)
                    if u'file_ids' in file_input:
                        del file_input[u'file_ids']
                    file_id = file_input[u'file_id']
                    if not isinstance(file_id, Integral):
                        msg = u'Invalid recipe data: Data input %s must have an integer in its "file_id" field' % name
                        raise InvalidData(msg)
                    file_ids.append(long(file_id))
                warnings.extend(self._validate_file_ids(file_ids, file_desc))
            else:
                # Don't have this input, check if it is required
                if required:
                    raise InvalidData(u'Invalid recipe data: Data input %s is required and was not provided' % name)
        return warnings

    def validate_properties(self, property_names):
        '''Validates the given property names to make sure all properties are populated correctly and exist if they are
        required

        :param property_names: Dict of property names mapped to a bool indicating if they are required
        :type property_names: dict of str -> bool
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`recipe.configuration.data.recipe_data.ValidationWarning`]

        :raises :class:`recipe.configuration.data.exceptions.InvalidData`: If there is a configuration problem.
        '''

        warnings = []
        for name in property_names:
            if name in self.data_inputs_by_name:
                # Have this input, make sure it is a valid property
                property_input = self.data_inputs_by_name[name]
                if not u'value' in property_input:
                    msg = u'Invalid recipe data: Data input %s is a property and must have a "value" field' % name
                    raise InvalidData(msg)
                value = property_input[u'value']
                if not isinstance(value, basestring):
                    msg = u'Invalid recipe data: Data input %s must have a string in its "value" field' % name
                    raise InvalidData(msg)
            else:
                # Don't have this input, check if it is required
                if property_names[name]:
                    raise InvalidData(u'Invalid recipe data: Data input %s is required and was not provided' % name)
        return warnings

    def validate_workspace(self):
        '''Validates the given file parameters to make sure they are valid with respect to the job interface

        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`recipe.configuration.data.recipe_data.ValidationWarning`]

        :raises :class:`recipe.configuration.data.exceptions.InvalidData`: If the workspace is missing or invalid.
        '''

        warnings = []
        if not u'workspace_id' in self.data_dict:
            raise InvalidData(u'Invalid recipe data: Workspace ID is needed and was not provided')
        workspace_id = self.data_dict[u'workspace_id']

        data_file_store = DATA_FILE_STORE[u'DATA_FILE_STORE']
        if not data_file_store:
            raise Exception(u'No data file store found')
        workspaces = data_file_store.get_workspaces([workspace_id])

        if not workspaces:
            raise InvalidData(u'Invalid recipe data: Workspace for ID %i does not exist' % workspace_id)
        active = workspaces[workspace_id]
        if not active:
            raise InvalidData(u'Invalid recipe data: Workspace for ID %i is not active' % workspace_id)
        return warnings

    def _validate_file_ids(self, file_ids, file_desc):
        '''Validates the files with the given IDs against the given file description

        :param file_ids: List of file IDs
        :type file_ids: list of long
        :param file_desc: The description of the required file meta-data for validation
        :type file_desc: :class:`job.configuration.interface.scale_file.ScaleFileDescription`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`recipe.configuration.data.recipe_data.ValidationWarning`]

        :raises :class:`recipe.configuration.data.exceptions.InvalidData`: If any of the files are missing.
        '''

        warnings = []
        found_ids = set()
        for scale_file in ScaleFile.objects.filter(id__in=file_ids):
            found_ids.add(scale_file.id)
            media_type = scale_file.media_type
            if not file_desc.is_media_type_allowed(media_type):
                warn = ValidationWarning(u'media_type',
                                         u'Invalid media type for file: %i -> %s' % (scale_file.id, media_type))
                warnings.append(warn)

        # Check if there were any file IDs that weren't found in the query
        for file_id in file_ids:
            if file_id not in found_ids:
                raise InvalidData(u'Invalid recipe data: Data file for ID %i does not exist' % file_ids[0])
        return warnings
