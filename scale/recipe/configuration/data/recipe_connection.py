'''Defines connections that will provide data to execute recipes'''
from __future__ import unicode_literals

from recipe.configuration.data.exceptions import InvalidRecipeConnection
from recipe.configuration.data.recipe_data import ValidationWarning
from storage.media_type import UNKNOWN_MEDIA_TYPE


class RecipeConnection(object):
    '''Represents a connection that will provide data to execute recipes. This class contains the necessary description
    needed to ensure the data provided by the connection will be sufficient to execute the given recipe.
    '''

    def __init__(self):
        '''Constructor
        '''

        self.param_names = set()
        self.properties = []
        self.files = {}  # Param name -> (multiple, media types, optional)
        self.workspace = False

    def add_input_file(self, file_name, multiple, media_types, optional):
        '''Adds a new file parameter to this connection

        :param file_name: The file parameter name
        :type file_name: str
        :param multiple: Whether the file parameter provides multiple files (True)
        :type multiple: bool
        :param media_types: The possible media types of the file parameter (unknown if None or [])
        :type media_types: list of str
        :param optional: Whether the file parameter is optional and may not be provided (True)
        :type optional: bool
        '''

        if file_name in self.param_names:
            raise Exception('Connection already has a parameter named %s' % file_name)

        if not media_types:
            media_types = [UNKNOWN_MEDIA_TYPE]

        self.param_names.add(file_name)
        self.files[file_name] = (multiple, media_types, optional)

    def add_property(self, property_name):
        '''Adds a new property parameter to this connection

        :param property_name: The property parameter name
        :type property_name: str
        '''

        if property_name in self.param_names:
            raise Exception('Connection already has a parameter named %s' % property_name)

        self.param_names.add(property_name)
        self.properties.append(property_name)

    def add_workspace(self):
        '''Indicates that this connection provides a workspace for storing output files
        '''

        self.workspace = True

    def has_workspace(self):
        '''Indicates whether this connection provides a workspace for storing output files

        :returns: True if this connection provides a workspace, False otherwise
        :rtype: bool
        '''

        return self.workspace

    def validate_input_files(self, files):
        '''Validates the given file parameters to make sure they are valid with respect to the recipe definition.

        :param files: Dict of file parameter names mapped to a tuple with three items: whether the parameter is required
            (True), if the parameter is for multiple files (True), and the description of the expected file meta-data
        :type files: dict of str ->
            tuple(bool, bool, :class:`job.configuration.interface.scale_file.ScaleFileDescription`)
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`recipe.configuration.data.recipe_data.ValidationWarning`]

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeConnection`: If there is a configuration
            problem
        '''

        warnings = []
        for name in files:
            required = files[name][0]
            multiple = files[name][1]
            file_desc = files[name][2]
            if name not in self.files:
                if required:
                    raise InvalidRecipeConnection('Data input %s is required and was not provided' % name)
                continue

            conn_file = self.files[name]
            conn_multiple = conn_file[0]
            conn_media_types = conn_file[1]
            conn_optional = conn_file[2]
            if conn_optional and required:
                raise InvalidRecipeConnection('Data input %s is required and data from connection is optional' % name)
            if not multiple and conn_multiple:
                raise InvalidRecipeConnection('Data input %s only accepts a single file' % name)
            for conn_media_type in conn_media_types:
                if not file_desc.is_media_type_allowed(conn_media_type):
                    warn = ValidationWarning('media_type',
                                             'Invalid media type for data input: %s -> %s' % (name, conn_media_type))
                    warnings.append(warn)
        return warnings

    def validate_properties(self, property_names):
        '''Validates the given property names to make sure all properties exist if they are required.

        :param property_names: Dict of property names mapped to a bool indicating if they are required
        :type property_names: dict of str -> bool
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`recipe.configuration.data.recipe_data.ValidationWarning`]

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeConnection`: If there is a configuration
            problem
        '''

        warnings = []
        for name in property_names:
            if name not in self.properties and property_names[name]:
                raise InvalidRecipeConnection('Property %s is required and was not provided' % name)
        return warnings
