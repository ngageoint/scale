"""Manages the v6 recipe configuration schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.mount import HostMountConfig, VolumeMountConfig
from job.execution.configuration.volume import HOST_TYPE, VOLUME_TYPE
from recipe.configuration.configuration import DEFAULT_PRIORITY, RecipeConfiguration
from recipe.configuration.exceptions import InvalidRecipeConfiguration

SCHEMA_VERSION = '7'
SCHEMA_VERSIONS = ['6', '7']

RECIPE_CONFIG_SCHEMA = {
    'type': 'object',
    'required': ['output_workspaces'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the recipe configuration schema',
            'type': 'string',
        },
        'mounts': {
            'description': 'Defines volumes to use for the jobs\' mounts',
            'type': 'object',
            'additionalProperties': {
                '$ref': '#/definitions/mount'
            },
        },
        'output_workspaces': {
            'description': 'Defines workspaces to use for the jobs\' output files',
            'type': 'object',
            'required': ['default', 'outputs'],
            'additionalProperties': False,
            'properties': {
                'default': {
                    'description': 'Defines the jobs\' default output workspace',
                    'type': 'string',
                },
                'outputs': {
                    'description': 'Defines a workspace for each given output name',
                    'type': 'object',
                    'additionalProperties': {
                        'type': 'string',
                    },
                },
            },
        },
        'priority': {
            'description': 'Defines the jobs\' priority',
            'type': 'integer',
            'minimum': 1,
        },
        'settings': {
            'description': 'Defines values to use for the jobs\' settings',
            'type': 'object',
            'additionalProperties': {
                'type': 'string',
            },
        },
    },
    'definitions': {
        'mount': {
            'oneOf': [{
                'type': 'object',
                'description': 'A configuration for a host mount',
                'required': ['type', 'host_path'],
                'additionalProperties': False,
                'properties': {
                    'type': {
                        'enum': ['host'],
                    },
                    'host_path': {
                        'type': 'string',
                    },
                },
            }, {
                'type': 'object',
                'description': 'A configuration for a volume mount',
                'required': ['type', 'driver', 'driver_opts'],
                'additionalProperties': False,
                'properties': {
                    'type': {
                        'enum': ['volume'],
                    },
                    'driver': {
                        'type': 'string',
                    },
                    'driver_opts': {
                        'type': 'object',
                        'additionalProperties': {
                            'type': 'string',
                        },
                    },
                },
            }],
        },
    },
}


def convert_config_to_v6_json(config):
    """Returns the v6 recipe configuration JSON for the given configuration

    :param config: The recipe configuration
    :type config: :class:`recipe.configuration.configuration.RecipeConfiguration`
    :returns: The v6 recipe configuration JSON
    :rtype: :class:`recipe.configuration.json.recipe_config_v6.RecipeConfigurationV6`
    """

    mounts_dict = {}
    for mount_config in config.mounts.values():
        if mount_config.mount_type == HOST_TYPE:
            mounts_dict[mount_config.name] = {'type': 'host', 'host_path': mount_config.host_path}
        elif mount_config.mount_type == VOLUME_TYPE:
            vol_dict = {'type': 'volume', 'driver_opts': mount_config.driver_opts}
            if mount_config.driver:
                vol_dict['driver'] = mount_config.driver
            mounts_dict[mount_config.name] = vol_dict

    workspace_dict = {'outputs': config.output_workspaces}
    if config.default_output_workspace:
        workspace_dict['default'] = config.default_output_workspace

    config_dict = {'version': SCHEMA_VERSION, 'mounts': mounts_dict, 'output_workspaces': workspace_dict,
                   'priority': config.priority, 'settings': config.settings}

    return RecipeConfigurationV6(config=config_dict, do_validate=False)


class RecipeConfigurationV6(object):
    """Represents a v6 recipe configuration JSON"""

    def __init__(self, config=None, existing=None, do_validate=False):
        """Creates a v6 job configuration JSON object from the given dictionary

        :param config: The recipe configuration JSON dict
        :type config: dict
        :param existing: Existing RecipeConfiguration to use for default values for unspecified fields
        :type existing: RecipeConfigurationV6
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`recipe.configuration.exceptions.InvalidRecipeConfiguration`: If the given configuration is invalid
        """

        if not config:
            config = {}
        self._config = config
        self._existing_config = None
        if existing:
            self._existing_config = existing._config

        if 'version' not in self._config:
            self._config['version'] = SCHEMA_VERSION

        if self._config['version'] not in SCHEMA_VERSIONS:
            msg = '%s is an unsupported version number'
            raise InvalidRecipeConfiguration('INVALID_VERSION', msg % self._config['version'])

        self._populate_default_values()

        try:
            if do_validate:
                validate(self._config, RECIPE_CONFIG_SCHEMA)
        except ValidationError as ex:
            raise InvalidRecipeConfiguration('INVALID_CONFIGURATION', 'Invalid configuration: %s' % unicode(ex))

    def get_configuration(self):
        """Returns the recipe configuration represented by this JSON

        :returns: The recipe configuration
        :rtype: :class:`recipe.configuration.configuration.RecipeConfiguration`:
        """

        config = RecipeConfiguration()

        for name, mount_dict in self._config['mounts'].items():
            if mount_dict['type'] == 'host':
                config.add_mount(HostMountConfig(name, mount_dict['host_path']))
            elif mount_dict['type'] == 'volume':
                config.add_mount(VolumeMountConfig(name, mount_dict['driver'], mount_dict['driver_opts']))

        default_workspace = self._config['output_workspaces']['default']
        if default_workspace:
            config.default_output_workspace = default_workspace
        for output, workspace in self._config['output_workspaces']['outputs'].items():
            config.add_output_workspace(output, workspace)

        config.priority = self._config['priority']

        for name, value in self._config['settings'].items():
            config.add_setting(name, value)

        return config

    def get_dict(self):
        """Returns the internal dictionary

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._config

    def _populate_default_values(self):
        """Populates any missing required values with defaults
        """

        if 'mounts' not in self._config:
            self._config['mounts'] = self._existing_config['mounts'] if self._existing_config else {}

        for mount_dict in self._config['mounts'].values():
            if mount_dict['type'] == 'volume':
                if 'driver' not in mount_dict:
                    mount_dict['driver'] = ''
                if 'driver_opts' not in mount_dict:
                    mount_dict['driver_opts'] = {}

        if 'output_workspaces' not in self._config:
            self._config['output_workspaces'] = self._existing_config['output_workspaces'] if self._existing_config else {}
        if 'default' not in self._config['output_workspaces']:
            self._config['output_workspaces']['default'] = ''
        if 'outputs' not in self._config['output_workspaces']:
            self._config['output_workspaces']['outputs'] = {}

        if 'priority' not in self._config:
            self._config['priority'] = self._existing_config['priority'] if self._existing_config else DEFAULT_PRIORITY

        if 'settings' not in self._config:
            self._config['settings'] = self._existing_config['settings'] if self._existing_config else {}
