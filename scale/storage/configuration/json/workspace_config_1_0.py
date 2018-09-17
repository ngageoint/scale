"""Defines the JSON schema for a job configuration"""
from __future__ import unicode_literals

import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from storage.configuration.workspace_configuration import WorkspaceConfiguration
from storage.configuration.exceptions import InvalidWorkspaceConfiguration

logger = logging.getLogger(__name__)

SCHEMA_VERSION = '1.0'

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
            'additionalProperties': True,
            'properties': {
                'type': {
                    'type': 'string',
                    'enum': ['host', 'nfs', 's3'],
                },
            },
        },
    },
}


class WorkspaceConfigurationV1(object):
    """Represents the schema for a workspace configuration"""

    def __init__(self, configuration=None, do_validate=False):
        """Creates a configuration interface from the given configuration json dict.

        If the definition is invalid, a :class:`storage.configuration.exceptions.InvalidWorkspaceConfiguration`
        exception will be thrown.

        :param configuration: The configuration json
        :type configuration: dict
        """
        if configuration is None:
            configuration = {}

        self._config = configuration
        config = self.get_configuration()

        try:
            if do_validate:
                validate(configuration, WORKSPACE_CONFIGURATION_SCHEMA)
                config.validate_broker()
        except ValidationError as validation_error:
            raise InvalidWorkspaceConfiguration('INVALID_CONFIGURATION', validation_error)

        self._populate_default_values()

        if self._config['version'] != SCHEMA_VERSION:
            msg = '%s is an unsupported version number'
            raise InvalidWorkspaceConfiguration('INVALID_VERSION', msg % self._config['version'])

    def get_configuration(self):
        """Returns the workspace configuration represented by this JSON

        :returns: The workspace configuration
        :rtype: :class:`workspace.configuration.workspace_configuration.WorkspaceConfiguration`:
        """

        config = WorkspaceConfiguration()
        config.configuration = self._config
        
        return config
        
    def get_dict(self):
        """Returns the internal dictionary that represents this workspace configuration

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._config

    def _populate_default_values(self):
        """Goes through the configuration and populates any missing values with defaults."""

        if 'version' not in self._config:
            self._config['version'] = SCHEMA_VERSION
