"""Defines the class for managing a configuration export."""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError


class InvalidConfiguration(Exception):
    """Exception indicating that the provided configuration was invalid."""
    pass


class ValidationWarning(object):
    """Tracks configuration warnings during validation that may not prevent it from working."""

    def __init__(self, key, details):
        """Constructor sets basic attributes.

        :param key: A unique identifier clients can use to recognize the warning.
        :type key: string
        :param details: A user-friendly description of the problem, including field names and/or associated values.
        :type details: string
        """
        self.key = key
        self.details = details


DEFAULT_VERSION = '1.0'

CONFIGURATION_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'version': {
            'type': 'string',
            'pattern': '^.{0,50}$',
        },
        'recipe_types': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/recipe_type_item',
            },
        },
        'job_types': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/job_type_item',
            },
        },
        'errors': {
            'type': 'array',
            'items': {
                '$ref': '#/definitions/error_item',
            },
        }
    },
    'definitions': {
        'recipe_type_item': {
            'type': 'object',
            'additionalProperties': True,
        },
        'job_type_item': {
            'type': 'object',
            'additionalProperties': True,
        },
        'error_item': {
            'type': 'object',
            'additionalProperties': True,
        },
    }
}


class Configuration(object):
    """Represents the recipe, job, and error records in a serialized format that can be imported later.

    :param configuration: The export configuration
    :type configuration: dict

    :raises InvalidDefinition: If the given configuration is invalid
    """
    def __init__(self, configuration):
        self._configuration = configuration

        try:
            validate(configuration, CONFIGURATION_SCHEMA)
        except ValidationError as ex:
            raise InvalidConfiguration('Invalid export configuration: %s' % unicode(ex))

    def get_dict(self):
        """Returns the internal dictionary that represents this export configuration

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration

    def _get_recipe_types(self):
        return self._configuration['recipe_types'] if 'recipe_types' in self._configuration else []
    recipe_types = property(_get_recipe_types)

    def _get_job_types(self):
        return self._configuration['job_types'] if 'job_types' in self._configuration else []
    job_types = property(_get_job_types)

    def _get_errors(self):
        return self._configuration['errors'] if 'errors' in self._configuration else []
    errors = property(_get_errors)
