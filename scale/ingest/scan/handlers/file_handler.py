"""Defines the handler for files processed by Strike and Scan"""


class FileHandler(object):
    """This class handles the rules for files processed by Strike and Scan
    """

    def __init__(self):
        """Constructor
        """

        self.rules = []

    def add_rule(self, rule):
        """Adds the given rule to the handler

        :param rule: The name of the file
        :type rule: :class:`ingest.handlers.file_rule.FileRule`
        """

        self.rules.append(rule)

    def match_file_name(self, file_name):
        """Checks the given file name and returns the first rule that matches it, returning None if no match is made

        :param file_name: The name of the file
        :type file_name: string
        :returns: The matched rule, possibly None
        :rtype: :class:`ingest.handlers.file_rule.FileRule`
        """

        for rule in self.rules:
            if rule.matches_file_name(file_name):
                return rule
        return None
