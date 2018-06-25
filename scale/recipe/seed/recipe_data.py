"""Defines the data needed for executing a recipe"""
from __future__ import unicode_literals

import logging

from numbers import Integral

from data.data.value import FileValue, JsonValue
from data.data.json.data_v6 import convert_data_to_v6_json, DataV6
from recipe.configuration.data.exceptions import InvalidRecipeData

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

        self._new_data = DataV6(data, do_validate=True).get_data()
        self._workspace_id = None

    def add_file_input(self, name, file_id):
        """Adds a new file parameter to this job data.

        :param data: The files parameter dict
        :type data: dict
        :param add_to_internal: Whether we should add to private data dict. Unneeded when used from __init__
        :type add_to_internal: bool
        """

        self._new_data.add_value(FileValue(name, [file_id]))

    def add_input_to_data(self, recipe_input_name, job_data, job_input_name):
        """Adds the given input from the recipe data as a new input to the given job data

        :param recipe_input_name: The name of the recipe data input to add to the job data
        :type recipe_input_name: str
        :param job_data: The job data
        :type job_data: :class:`job.data.job_data.JobData`
        :param job_input_name: The name of the job data input to add
        :type job_input_name: str
        """

        if recipe_input_name in self._new_data.values:
            data_value = self._new_data.values[recipe_input_name]
            if isinstance(data_value, FileValue):
                job_data.add_file_list_input(job_input_name, data_value.file_ids)
            if isinstance(data_value, JsonValue):
                job_data.add_json_input({'name':job_input_name, 'value': data_value.value})

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

    def get_workspace_id(self):
        """Returns the workspace ID in the recipe data

        :returns: The workspace ID
        :rtype: int
        """

        return self._workspace_id

    def set_workspace_id(self, workspace_id):
        """Set the workspace ID in the recipe data.

        :param workspace_id: The new workspace ID
        :type workspace_id: int

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the workspace ID is an invalid type
        """
        if not isinstance(workspace_id, Integral):
            raise InvalidRecipeData('Workspace ID must be an integer')
        self._workspace_id = workspace_id

    def validate_input_files(self, files):
        """Validates the given file parameters to make sure they are valid with respect to the job interface.

        :param files: Dict of file parameter names mapped to a tuple with three items: whether the parameter is required
            (True), if the parameter is for multiple files (True), and the description of the expected file meta-data
        :type files: dict of str ->
            tuple(bool, bool, :class:`job.configuration.interface.scale_file.ScaleFileDescription`)
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidRecipeData`: If there is a configuration problem.
        """

        return []

    def validate_input_json(self, input_json):
        """Validates the given property names to ensure they are all populated correctly and exist if they are required.

        :param input_json: List of Seed input json fields
        :type input_json: [:class:`job.seed.types.SeedInputJson`]
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.data.exceptions.InvalidRecipeData`: If there is a configuration problem.
        """

        return []

    def validate_workspace(self):
        """Validates the given file parameters to make sure they are valid with respect to the job interface

        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`recipe.configuration.data.recipe_data.ValidationWarning`]

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the workspace is missing or invalid
        """

        if not self._workspace_id:
            raise InvalidRecipeData('Invalid recipe data: Workspace ID is needed and was not provided')
        return []
