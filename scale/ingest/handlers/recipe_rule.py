"""Defines a file rule for handling files processed by Strike and Scan"""


class RecipeRule(object):
    """This class represents a rule for handling files processed by Strike and Scan
    """

    def __init__(self, input_name, media_types, data_types, not_data_types):
        """Constructor

        :param input_name: The recipe input this rule matches
        :type input_name: string
        :param media_types: Media Types to check
        :type media_types: [string]
        :param data_types: The list of data tags to check if files match
        :type data_types: [string]
        :param any_data_types: The list of data tags to check if files match
        :type any_data_types: [string]
        :param not_data_types: The list of data tags to check if files don't match
        :type not_data_types: [string]
        """

        self.input_name = input_name
        self._media_types = media_types if media_types is not None else set()
        self._data_types = data_types if data_types is not None else set()
        # self._any_data_types = any_data_types if any_data_types is not None else set()
        self._not_data_types = not_data_types if not_data_types is not None else set()

    def get_media_types(self):
        """Returns the file media type for this ingest trigger condition

        :return: The media type(s)
        :rtype: [string]
        """

        return self._media_types

    def matches_file(self, source_file):
        """Indicates whether the given file name matches this rule

        :param file_name: The name of the file
        :type file_name: string
        :returns: True if this file name matches the rule, False otherwise
        :rtype: bool
        """

        if self._media_types and source_file.media_type not in self._media_types:
            return False

        data_type_checks = []
        file_data_types = source_file.get_data_type_tags()

        # if self._any_data_types:
        #     data_type_checks.append(True in [tag in file_data_types for tag in self._any_data_types])
        if self._data_types:
            data_type_checks.append(self._data_types <= file_data_types)
        if self._not_data_types:
            data_type_checks.append(True not in [tag in file_data_types for tag in self._not_data_types])

        return False not in data_type_checks if data_type_checks else True
