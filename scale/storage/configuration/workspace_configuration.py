"""Defines the configuration for a storage Workspace"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

import storage.brokers.factory as broker_factory
from storage.configuration.exceptions import InvalidWorkspaceConfiguration

DEFAULT_VERSION = '1.0'

WORKSPACE_CONFIGURATION_SCHEMA = {
    'type': 'object',
    'required': ['broker'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the Workspace configuration schema',
            'type': 'string',
            'pattern': '^.{0,50}$',
        },
        'broker': {
            'type': 'object',
            'required': ['type'],
            'additionalProperties': False,
            'properties': {
                'type': {
                    'type': 'string',
                    'enum': ['host'],
                },
            }
        }
    }
}


class WorkspaceConfiguration(object):
    """Represents the configuration for a storage Workspace.
    The configuration includes details about the storage broker system required to read, write, move, or delete files
    within the workspace.
    """

    def __init__(self, configuration):
        """Creates a Workspace configuration object from the given dictionary.
        The general format is checked for correctness, but the specified broker is not checked.

        :param configuration: The Workspace configuration
        :type configuration: dict
        :raises InvalidWorkspaceConfiguration: If the given configuration is invalid
        """

        self._configuration = configuration

        # Valid the overall JSON schema
        try:
            validate(configuration, WORKSPACE_CONFIGURATION_SCHEMA)
        except ValidationError as ex:
            raise InvalidWorkspaceConfiguration('Invalid Workspace configuration: %s' % unicode(ex))

        # Validate the broker-specific attributes
        broker = broker_factory.get_broker(self._configuration['broker']['type'])
        broker.validate_configuration(self._configuration['broker'])

        self._populate_default_values()
        if not self._configuration['version'] == '1.0':
            msg = 'Invalid Workspace configuration: %s is an unsupported version number'
            raise InvalidWorkspaceConfiguration(msg % self._configuration['version'])

    def _populate_default_values(self):
        """Goes through the configuration and populates any missing values with defaults."""

        if 'version' not in self._configuration:
            self._configuration['version'] = DEFAULT_VERSION
