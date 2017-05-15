"""Defines exceptions that can occur when interacting with jobs and job types"""
from __future__ import unicode_literals

import logging
from abc import ABCMeta, abstractmethod

from django.db.utils import DatabaseError, OperationalError

from error.models import Error


logger = logging.getLogger(__name__)


# Scale job errors registered by their exit codes
REGISTERED_ERRORS = {}  # {Exit code: ScaleError}
REGISTERED_WRAPPED_EX = {}  # {Wrapped exception class name: ScaleError}


def get_error_by_exit_code(exit_code):
    """Returns the name of the error that corresponds to the given exit code, possibly None

    :param exit_code: The exit code
    :type exit_code: int
    :returns: The error model, possibly None
    :rtype: :class:`error.models.Error`
    """

    logger.info('Registered exit codes are: %s', ', '.join(REGISTERED_ERRORS.keys()))
    if exit_code not in REGISTERED_ERRORS:
        return None
    return Error.objects.get_builtin_error(REGISTERED_ERRORS[exit_code].error_name)


def get_error_by_exception(wrapped_ex):
    """Returns the ScaleError that corresponds to the given wrapped exception class name, possibly None

    :param wrapped_ex: The name of the wrapped exception class
    :type wrapped_ex: string
    :returns: The error, possibly None
    :rtype: :class:`error.exceptions.ScaleError`
    """

    if wrapped_ex not in REGISTERED_WRAPPED_EX:
        return None
    return REGISTERED_WRAPPED_EX[wrapped_ex]


def register_error(error):
    """Registers the given ScaleError

    :param error: The ScaleError
    :type error: :class:`error.exceptions.ScaleError`
    """

    if error.exit_code in REGISTERED_ERRORS:
        raise Exception('Tried to register error with duplicate exit code: %d', error.exit_code)
    REGISTERED_ERRORS[error.exit_code] = error
    if error.wrapped_ex:
        if error.wrapped_ex in REGISTERED_WRAPPED_EX:
            raise Exception('Tried to register error with duplicate wrapped exception: %s', error.wrapped_ex)
        REGISTERED_WRAPPED_EX[error.wrapped_ex] = error


class ScaleError(Exception):
    """Abstract base class for exceptions that represent Scale errors. The exceptions contain exit code and error
    information.
    """

    __metaclass__ = ABCMeta

    def __init__(self, exit_code, error_name, log_stacktrace=False, wrapped_ex=None):
        """Constructor

        :param exit_code: The exit code for communicating the error back to the scheduler
        :type exit_code: int
        :param error_name: The name of the Scale error to attach to the failed job
        :type error_name: string
        :param log_stacktrace: Whether to log the exception's stacktrace
        :type log_stacktrace: bool
        :param wrapped_ex: The name of the wrapped exception class
        :type wrapped_ex: string
        """

        self.exit_code = exit_code
        self.error_name = error_name
        self.log_stacktrace = log_stacktrace
        self.wrapped_ex = wrapped_ex

    @abstractmethod
    def get_log_message(self):
        """The log message to print out when the error occurs. This should be overridden by derived classes to provide
        detailed log messaging.

        :returns: The log message
        :rtype: string
        """

        raise NotImplementedError()

    def log(self):
        """Logs the error message
        """

        if self.log_stacktrace:
            logger.exception(self.get_log_message())
        else:
            logger.error(self.get_log_message())


class ScaleDatabaseError(ScaleError):
    """Error class that wraps the Django DatabaseError
    """

    def __init__(self):
        """Constructor
        """

        super(ScaleDatabaseError, self).__init__(2, 'database', True, DatabaseError.__name__)

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return 'An error occurred with the Scale database'


class ScaleIOError(ScaleError):
    """Error class that wraps the Python IOError
    """

    def __init__(self):
        """Constructor
        """

        super(ScaleIOError, self).__init__(4, 'filesystem-io', True, IOError.__name__)

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return 'An I/O operation failed'


class ScaleOperationalError(ScaleError):
    """Error class that wraps the Django OperationalError
    """

    def __init__(self):
        """Constructor
        """

        super(ScaleOperationalError, self).__init__(3, 'database-operation', True, OperationalError.__name__)

    def get_log_message(self):
        """See :meth:`error.exceptions.ScaleError.get_log_message`
        """

        return 'A Scale database operation failed'
