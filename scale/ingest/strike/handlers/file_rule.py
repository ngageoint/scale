"""Defines a file rule for handling files processed by Strike"""


class FileRule(object):
    """This class represents a rule for handling files processed by Strike
    """

    def __init__(self, filename_regex, data_types, new_workspace, new_workspace_path):
        """Constructor

        :param filename_regex: The regular expression to match against processed file names
        :type filename_regex: :class:`re.RegexObject`
        :param data_types: The list of data tags to apply to files that match this rule
        :type data_types: [string]
        :param new_workspace: The new workspace to move files that match this rule, possibly None
        :type new_workspace: string
        :param new_workspace_path: The new workspace path for files that match this rule, possibly None
        :type new_workspace_path: string
        """

        self.filename_regex = filename_regex
        self.data_types = data_types
        self.new_workspace = new_workspace
        self.new_workspace_path = new_workspace_path

    def matches_file_name(self, file_name):
        """Indicates whether the given file name matches this rule

        :param file_name: The name of the file
        :type file_name: string
        :returns: True if this file name matches the rule, False otherwise
        :rtype: bool
        """

        return self.filename_regex.match(file_name)
