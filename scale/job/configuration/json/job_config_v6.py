"""Manages the v6 job configuration schema"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.configuration import DEFAULT_PRIORITY, JobConfiguration
from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.json.job_config_2_0 import JobConfigurationV2
from job.configuration.mount import HostMountConfig, VolumeMountConfig
from job.execution.configuration.volume import HOST_TYPE, VOLUME_TYPE


SCHEMA_VERSION = '6'


JOB_CONFIG_SCHEMA = {
    'type': 'object',
    'required': ['mounts', 'output_workspaces', 'priority', 'settings'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the job configuration schema',
            'type': 'string',
        },
        'mounts': {
            'description': 'Defines volumes to use for the job\'s mounts',
            'type': 'object',
            'additionalProperties': {
                '$ref': '#/definitions/mount'
            },
        },
        'output_workspaces': {
            'description': 'Defines workspaces to use for the job\'s output files',
            'type': 'object',
            'required': ['default', 'outputs'],
            'additionalProperties': False,
            'properties': {
                'default': {
                    'description': 'Defines the job\'s default output workspace',
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
            'description': 'Defines the job\'s priority',
            'type': 'integer',
            'minimum': 1,
        },
        'settings': {
            'description': 'Defines values to use for the job\'s settings',
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
    """Returns the v6 job configuration JSON for the given configuration

    :param config: The job configuration
    :type config: :class:`job.configuration.configuration.JobConfiguration`
    :returns: The v6 job configuration JSON
    :rtype: :class:`job.configuration.json.job_config_v6.JobConfigurationV6`
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

    return JobConfigurationV6(config=config_dict, do_validate=False)


class JobConfigurationV6(object):
    """Represents a v6 job configuration JSON"""

    def __init__(self, config=None, do_validate=False):
        """Creates a v6 job configuration JSON object from the given dictionary

        :param config: The job configuration JSON dict
        :type config: dict
        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the given configuration is invalid
        """

        if not config:
            config = {}
        self._config = config

        if 'version' not in self._config:
            self._config['version'] = SCHEMA_VERSION

        if self._config['version'] != SCHEMA_VERSION:
            self._convert_from_v2(do_validate)

        self._populate_default_values()

        try:
            if do_validate:
                validate(self._config, JOB_CONFIG_SCHEMA)
        except ValidationError as ex:
            raise InvalidJobConfiguration('INVALID_CONFIGURATION', 'Invalid configuration: %s' % unicode(ex))

    def get_configuration(self):
        """Returns the job configuration represented by this JSON

        :returns: The job configuration
        :rtype: :class:`job.configuration.configuration.JobConfiguration`:
        """

        config = JobConfiguration()

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

    def _convert_from_v2(self, do_validate):
        """Converts the JSON dict from v2 to the current version

        :param do_validate: Whether to perform validation on the JSON schema
        :type do_validate: bool

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the given configuration is invalid
        """

        v2_json_dict = JobConfigurationV2(self._config, do_validate=do_validate).get_dict()

        # Only the version needs changed when going from v2 to v6
        if 'version' in v2_json_dict:
            del v2_json_dict['version']
        v2_json_dict['version'] = SCHEMA_VERSION

        self._data = v2_json_dict

    def _populate_default_values(self):
        """Populates any missing required values with defaults
        """

        if 'mounts' not in self._config:
            self._config['mounts'] = {}
        for mount_dict in self._config['mounts'].values():
            if mount_dict['type'] == 'volume':
                if 'driver' not in mount_dict:
                    mount_dict['driver'] = ''
                if 'driver_opts' not in mount_dict:
                    mount_dict['driver_opts'] = {}

        if 'output_workspaces' not in self._config:
            self._config['output_workspaces'] = {}
        if 'default' not in self._config['output_workspaces']:
            self._config['output_workspaces']['default'] = ''
        if 'outputs' not in self._config['output_workspaces']:
            self._config['output_workspaces']['outputs'] = {}

        if 'priority' not in self._config:
            self._config['priority'] = DEFAULT_PRIORITY

        if 'settings' not in self._config:
            self._config['settings'] = {}
