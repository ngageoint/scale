"""Defines the class for handling the error mapping for a job type"""
from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.error.error import JobError
from error.models import Error, get_builtin_error, get_job_error


logger = logging.getLogger(__name__)


class JobErrorMapping(object):
    """Handles the error mapping for a job type"""

    def __init__(self, job_type_name):
        """Creates an error mapping for a job type with the given name

        :param job_type_name: The job type name
        :type job_type_name: string
        """

        # TODO: a job type name of None indicates that this is a legacy job type - remove associated legacy logic when
        # legacy job types are removed
        self.job_type_name = job_type_name
        self._mapping = {}  # {Exit code: Error}

    def add_mapping(self, exit_code, error):
        """Adds a mapping from the given exit code to the given error

        :param exit_code: The exit code
        :type exit_code: int
        :param error: The error
        :type error: :class:`job.error.error.JobError`
        """

        self._mapping[exit_code] = error

    def get_error(self, exit_code=None, default_error_name='algorithm-unknown'):
        """Retrieves the error model that maps to the given exit code. If the exit code is zero (success), None is
        returned. For a failure exit code with no mapping, the given default error is returned.

        :param exit_code: The exit code from a task
        :type exit_code: int
        :param default_error_name: The name of the builtin error to use if no mapping exists for the exit code
        :type default_error_name: string
        :returns: The error model mapped to the given exit code, possibly None
        :rtype: :class:`error.models.Error`
        """

        error = None
        if exit_code is not None:
            # If the exit code is zero, None should be returned
            if exit_code == 0:
                return None

            if exit_code in self._mapping:
                error_name = self._mapping[exit_code].name
                error = get_job_error(self.job_type_name, error_name)

            if not error:
                # No exit code match, so return the given default error
                error = get_builtin_error(default_error_name)

        return error


    def save_models(self):
        """Saves this mapping as error models in the database
        """

        error_models = [error.create_model() for error in self._mapping.values()]
        Error.objects.save_job_error_models(self.job_type_name, error_models)
