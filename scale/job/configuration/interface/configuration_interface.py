"""Defines the interface for defining a default job configuration"""
from __future__ import unicode_literals

import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.interface.exceptions import InvalidInterfaceDefinition

from error.models import Error

logger = logging.getLogger(__name__)

CONFIGURATION_INTERFACE_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'version of the configuration_interface schema',
            'type': 'string',
            'pattern': '^.{0,50}$',
        },
        'default_settings': {
            'type': 'object',
            'item': {
                'type': 'string',
            },
        },
    },
}


class ConfigurationInterface(object):
    """Represents the interface for defining a default job configuration"""

    def __init__(self, definition):
        """Creates a configuration interface from the given definition.

        If the definition is invalid, a :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition`
        exception will be thrown.

        :param definition: The interface definition
        :type definition: dict
        """
        if definition is None:
            definition = {}

        self.definition = definition

        try:
            validate(definition, CONFIGURATION_INTERFACE_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidInterfaceDefinition(validation_error)

        self._populate_default_values()

        if self.definition['version'] != '1.0':
            raise InvalidInterfaceDefinition('%s is an unsupported version number' % self.definition['version'])

    def get_dict(self):
        """Returns the internal dictionary that represents this error mapping

        :returns: The internal dictionary
        :rtype: dict
        """

        return self.definition

    # def get_default_setting_names(self):
    #     """Returns a set of all default setting names for this interface
    #
    #     :returns: Set of default setting names
    #     :rtype: {string}
    #     """
    #     if 'default_settings' not in self.definition:
    #         return set()
    #
    #     settings = self.definition.get('default_settings')
    #     return {setting_name for setting_name in settings.iterkeys()}
    #
    # def validate(self):
    #     """Validates the setting definitions to ensure that all referenced errors actually exist.
    #
    #     :returns: A list of warnings discovered during validation.
    #     :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]
    #
    #     :raises :class:`job.configuration.interface.exceptions.InvalidInterfaceDefinition`: If there is a missing error.
    #     """
    #     setting_names = self.get_error_names()
    #     error_map = {error.name: error for error in Error.objects.filter(name__in=error_names)}
    #
    #     for error_name in error_names:
    #         if error_name not in error_map:
    #             raise InvalidInterfaceDefinition('Missing error model reference: %s' % error_name)
    #     return []

    def _populate_default_values(self):
        """Goes through the definition and fills in any missing default values"""
        if 'version' not in self.definition:
            self.definition['version'] = '1.0'
        if 'default_settings' not in self.definition:
            self.definition['default_settings'] = {}
