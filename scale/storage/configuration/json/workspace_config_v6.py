"""Manages the v6 job configuration schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from storage.configuration.workspace_configuration import WorkspaceConfiguration
from storage.configuration.exceptions import InvalidWorkspaceConfiguration
from storage.configuration.json.workspace_config_1_0 import WorkspaceConfigurationV1


SCHEMA_VERSION = '6'

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

def convert_config_to_v6_json(config):
    """Returns the v6 workspace configuration JSON for the given configuration

    :param config: The workspace configuration
    :type config: :class:`storage.configuration.workspace_configuration.WorkspaceConfiguration`
    :returns: The v6 workspace configuration JSON
    :rtype: :class:`workspace.configuration.json.workspace_config_v6.WorkspaceConfigurationV6`
    """

    return WorkspaceConfigurationV6(config=config.get_dict(), do_validate=False)

class WorkspaceConfigurationV6(object):
    """Represents the schema for a workspace configuration"""

    def __init__(self, config=None, do_validate=False):
        """Creates a v6 workspace configuration JSON object from the given dictionary

        :param config: The workspace configuration JSON dict
        :type config: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`storage.configuration.exceptions.InvalidWorkspaceConfiguration`: If the given configuration is invalid
        """

        if not config:
            config = {}
        self._config = config

        if 'version' not in self._config:
            self._config['version'] = SCHEMA_VERSION

        if self._config['version'] != SCHEMA_VERSION:
            self._convert_from_v1(do_validate)

        self._populate_default_values()
        
        config = self.get_configuration()

        try:
            if do_validate:
                validate(self._config, WORKSPACE_CONFIGURATION_SCHEMA)
                config.validate_broker()
        except ValidationError as ex:
            raise InvalidWorkspaceConfiguration('INVALID_CONFIGURATION', 'Invalid configuration: %s' % unicode(ex))

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

    def _convert_from_v1(self, do_validate):
        """Converts the JSON dict from v1 to the current version

        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`workspace.configuration.workspace_configuration.WorkspaceConfiguration`: If the given configuration is invalid
        """

        v1_json_dict = WorkspaceConfigurationV1(self._config, do_validate=do_validate).get_dict()

        # Only the version needs changed when going from v1 to v6
        v1_json_dict['version'] = SCHEMA_VERSION
        
        self._config = v1_json_dict