"""Defines exceptions that can occur when interacting with a job interface"""
from __future__ import unicode_literals

from error.exceptions import ScaleError


class InvalidInterfaceDefinition(Exception):
    """Exception indicating that the provided definition of a job interface was invalid
    """
    pass


class InvalidEnvironment(Exception):
    """Exception indicating that the provided definition of a job interface was invalid
    """
    pass


class MissingSetting(ScaleError):
    """Error class indicating that a required setting value is missing
    """

    def __init__(self, setting):
        """Constructor

        :param setting: The name of the missing setting
        :type setting: string
        """

        super(MissingSetting, self).__init__(6, 'missing-setting')
        self.setting = setting

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return 'Required setting %s was not provided' % self.setting
