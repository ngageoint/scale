"""Defines the exceptions related to diagnostics"""
from __future__ import unicode_literals

from error.exceptions import ScaleError


class TestException(ScaleError):
    """Error class indicating that a test error occurred
    """

    def __init__(self):
        """Constructor
        """

        super(TestException, self).__init__(11, 'test')

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return ''
