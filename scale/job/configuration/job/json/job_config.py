"""Defines the JSON schema for a job configuration"""
from __future__ import unicode_literals

import logging

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.job.exceptions import InvalidJobConfiguration
from job.configuration.job.json import job_config_1_0 as previous_interface

logger = logging.getLogger(__name__)

SCHEMA_VERSION = '2.0'

JOB_CONFIG_SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the job configuration schema',
            'type': 'string',
            'default': SCHEMA_VERSION,
            'pattern': '^.{0,50}$',
        },
        'mounts': {
            'description': 'Defines volumes to use for the job\'s mounts',
            'type': 'object',
            'additionalProperties': {
                '$ref': '#/definitions/mount'
            },
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
            'type': 'object',
            'required': ['type'],
            'additionalProperties': False,
            'properties': {
                'type': {
                    'enum': ['host', 'volume'],
                },
                'host_path': {
                    'type': 'string',
                },
                'driver': {
                    'type': 'string',
                },
                'driver_opts': {
                    'type': 'object',
                    'item': {
                        'type': 'string',
                    },
                },
            },
        },
    },
}


class JobConfiguration(object):
    """Represents the schema for a job configuration"""

    def __init__(self, configuration=None):
        """Creates a job configuration from the given dict

        :param configuration: The configuration dict
        :type configuration: dict

        :raises :class:`job.configuration.job.exceptions.InvalidJobConfiguration`: If the given configuration is invalid
        """

        if configuration is None:
            configuration = {}

        self._configuration = configuration

        if 'version' not in self._configuration:
            self._configuration['version'] = SCHEMA_VERSION
        if self._configuration['version'] != SCHEMA_VERSION:
            self._convert_configuration()

        try:
            validate(configuration, JOB_CONFIG_SCHEMA)
        except ValidationError as validation_error:
            raise InvalidJobConfiguration(validation_error)

        self._populate_default_values()
        self._validate_mounts()
        self._validate_settings()

    def get_dict(self):
        """Returns the internal dictionary representing this configuration

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration

    def get_setting_value(self, name):
        """Returns the value of the given setting if defined in this configuration, otherwise returns None

        :param name: The name of the setting
        :type name: string
        :returns: The value of the setting, possibly None
        :rtype: string
        """

        if name in self._configuration['settings']:
            return self._configuration['settings'][name]

        return None

    def get_settings(self):
        """Returns the dict of all settings defined in this configuration

        :returns: The dict of all settings defined in this configuration
        :rtype: dict
        """

        return self._configuration['settings']

    def _convert_configuration(self):
        """Converts the configuration from a previous schema version

        :raises :class:`job.configuration.job.exceptions.InvalidJobConfiguration`: If the given configuration is invalid
        """

        # Validate/process the dict according to the previous version
        self._configuration = previous_interface.JobConfiguration(self._configuration).get_dict()

        self._configuration['version'] = SCHEMA_VERSION
        self._configuration['settings'] = self._configuration['default_settings']
        del self._configuration['default_settings']

    def _populate_default_values(self):
        """Populates any missing default values"""

        if 'mounts' not in self._configuration:
            self._configuration['mounts'] = {}
        if 'settings' not in self._configuration:
            self._configuration['settings'] = {}

    def _validate_mounts(self):
        """Ensures that the mounts are valid

        :raises :class:`job.configuration.job.exceptions.InvalidJobConfiguration`: If the mounts are invalid
        """

        for name, mount in self._configuration['mounts'].iteritems():
            if mount['type'] == 'host':
                if 'host_path' not in mount:
                    raise InvalidJobConfiguration('Host mount %s requires host_path' % name)
                if 'driver' in mount:
                    raise InvalidJobConfiguration('Host mount %s does not support driver' % name)
                if 'driver_opts' in mount:
                    raise InvalidJobConfiguration('Host mount %s does not support driver_opts' % name)
            elif mount['type'] == 'volume':
                if 'driver' not in mount:
                    raise InvalidJobConfiguration('Volume mount %s requires driver' % name)
                if 'host_path' in mount:
                    raise InvalidJobConfiguration('Volume mount %s does not support host_path' % name)

    def _validate_settings(self):
        """Ensures that the settings are valid

        :raises :class:`job.configuration.job.exceptions.InvalidJobConfiguration`: If the settings are invalid
        """

        for setting_name, setting_value in self._configuration['settings'].iteritems():
            if not setting_value:
                raise InvalidJobConfiguration('Setting %s has blank value' % setting_name)
