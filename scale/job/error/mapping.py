"""Defines the class for handling the error mapping for a job type"""
from __future__ import absolute_import
from __future__ import unicode_literals

import logging

from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.error.error import JobError
from error.models import Error, get_builtin_error, get_job_error


logger = logging.getLogger(__name__)


# TODO: remove when legacy job types go away
def create_legacy_error_mapping(error_dict):
    """Returns the error mapping for the given legacy error dict

    :param error_dict: The legacy error dict
    :type error_dict: dict
    :returns: The error mapping
    :rtype: :class:`job.error.mapping.JobErrorMapping`
    """

    if error_dict is None:
        error_dict = {}

    mapping = JobErrorMapping(None)
    mapping.error_dict = error_dict

    if 'version' not in error_dict:
        error_dict['version'] = '1.0'
    if error_dict['version'] != '1.0':
        raise InvalidInterfaceDefinition('Invalid error interface version: %s' % error_dict['version'])
    if 'exit_codes' not in error_dict:
        error_dict['exit_codes'] = {}
    if not isinstance(error_dict['exit_codes'], dict):
        raise InvalidInterfaceDefinition('Invalid error interface')
    for exit_code, error_name in error_dict['exit_codes'].items():
        exit_code = int(exit_code)
        error = JobError(None, error_name)
        mapping.add_mapping(exit_code, error)

    return mapping


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

        # TODO: remove when support for legacy job types is removed
        self.error_dict = {}

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
                try:
                    error = get_job_error(self.job_type_name, error_name)
                except Error.DoesNotExist:
                    # TODO: remove exception handling when legacy style job types are removed
                    logger.exception('Unable to find error mapping: %s', error_name)
                    return None

            if not error:
                # No exit code match, so return the given default error
                error = get_builtin_error(default_error_name)

        return error

    # TODO: remove this when legacy style job types are removed
    def get_error_names_legacy(self):
        """Returns a set of all error names for this interface

        :returns: Set of error names
        :rtype: {string}
        """

        return {error.name for error in self._mapping.values()}

    def save_models(self):
        """Saves this mapping as error models in the database
        """

        error_models = [error.create_model() for error in self._mapping.values()]
        Error.objects.save_job_error_models(self.job_type_name, error_models)

    # TODO: remove this when legacy style job types are removed
    def validate_legacy(self):
        """Validates the error mappings to ensure that all referenced errors actually exist.

        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition`: If there is a missing error.
        """

        error_names = self.get_error_names_legacy()
        error_map = {error.name: error for error in Error.objects.filter(name__in=error_names)}

        for error_name in error_names:
            if error_name not in error_map:
                raise InvalidInterfaceDefinition('Missing error model reference: %s' % error_name)
        return []
