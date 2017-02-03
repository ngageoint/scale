"""Defines exceptions that can occur when interacting with a job results"""
from __future__ import unicode_literals

from error.exceptions import ScaleError


class InvalidResultsManifest(ScaleError):
    """Error class indicating that a result manifest is invalid
    """

    def __init__(self, msg):
        """Constructor

        :param msg: An error message to log
        :type msg: string
        """

        super(InvalidResultsManifest, self).__init__(5, 'invalid-results-manifest')
        self.msg = msg

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return self.msg


class MissingRequiredOutput(ScaleError):
    """Error class indicating that a required output was not produced
    """

    def __init__(self, output):
        """Constructor

        :param output: The name of missing output
        :type output: string
        """

        super(MissingRequiredOutput, self).__init__(7, 'missing-required-output')
        self.output = output

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return '%s is a required output, but the algorithm did not provide it' % self.output
