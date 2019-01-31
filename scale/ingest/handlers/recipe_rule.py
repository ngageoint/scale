"""Defines a file rule for handling files processed by Strike and Scan"""

import re

class RecipeRule(object):
    """This class represents a rule for handling files processed by Strike and Scan
    """

    def __init__(self, input_name, regex, media_types):
        """Constructor

        :param input_name: The recipe input this rule matches
        :type input_name: string
        :param regex: The regex to match the filename on
        :type regex: string
        :param media_types: Media Types to check
        :type media_types: [string]
        """

        self.input_name = input_name
        self.filename_regex = re.compile(regex) if re is not None else None
        self._media_types = set(media_types) if media_types is not None else set()

    def get_media_types(self):
        """Returns the file media type for this ingest trigger condition

        :return: The media type(s)
        :rtype: [string]
        """

        return list(self._media_types)

    def matches_file(self, source_file):
        """Indicates whether the given file name matches this rule

        :param source_file: The source file
        :type source_file: :class:`source.models.SourceFile`
        :returns: True if this file name matches the rule, False otherwise
        :rtype: bool
        """

        if self._media_types and source_file.media_type not in self._media_types:
            return False

        # perform filename regex
        if self.filename_regex:
            return self.filename_regex.match(source_file.file_name)

        # No rules defined, so accept file?
        return True