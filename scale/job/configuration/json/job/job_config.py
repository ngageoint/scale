"""Defines the JSON schema for a job configuration"""
from __future__ import unicode_literals

import logging
import os

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.json.job import job_config_1_0 as previous_interface
from job.configuration.volume import Volume

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
                    'additionalProperties': {
                        'type': 'string',
                    },
                },
            },
        },
    },
}


class ValidationWarning(object):
    """Tracks job configuration warnings during validation that may not prevent the job from working."""

    def __init__(self, key, details):
        """Constructor sets basic attributes.

        :param key: A unique identifier clients can use to recognize the warning.
        :type key: string
        :param details: A user-friendly description of the problem, including field names and/or associated values.
        :type details: string
        """
        self.key = key
        self.details = details


class JobConfiguration(object):
    """Represents the schema for a job configuration"""

    def __init__(self, configuration=None):
        """Creates a job configuration from the given dict

        :param configuration: The configuration dict
        :type configuration: dict

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the given configuration is invalid
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

    def get_mount_volume(self, mount_name, volume_name, container_path, mode):
        """Returns the volume that has been configured for the given mount name. If the given mount is not defined in
        this configuration, None is returned.

        :param mount_name: The name of the mount defined in the job type
        :type mount_name: string
        :param volume_name: The name of the volume
        :type volume_name: string
        :param container_path: The path within the container onto which the volume will be mounted
        :type container_path: string
        :param mode: Either 'ro' for read-only or 'rw' for read-write
        :type mode: string
        :returns: The volume that should be mounted into the job container, possibly None
        :rtype: :class:`job.configuration.volume.Volume`
        """

        if mount_name not in self._configuration['mounts']:
            return None

        volume = None
        mount_config = self._configuration['mounts'][mount_name]
        mount_type = mount_config['type']
        if mount_type == 'host':
            host_path = mount_config['host_path']
            volume = Volume(container_path, mode, is_host=True, host_path=host_path)
        elif mount_type == 'volume':
            driver = mount_config['driver']
            driver_opts = mount_config['driver_opts']
            volume = Volume(container_path, mode, is_host=False, name=volume_name, driver=driver,
                            driver_opts=driver_opts)

        return volume

    def get_secret_settings(self, interface):
        """Returns a dict of configuration settings that are secret based off the job interface
        setting designations.

        :param interface: The interface dict for the job type
        :type interface: dict
        :returns: name:value pairs of secret settings, possibly None
        :rtype: dict
        """

        secrets = {}

        if 'settings' in self._configuration and 'settings' in interface:
            interface_settings = interface['settings']
            secret_settings = [setting['name'] for setting in interface_settings if setting['secret']]

            for setting_name in secret_settings:
                if setting_name in self._configuration['settings']:
                    secrets[setting_name] = self._configuration['settings'][setting_name]

        return secrets

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

    def validate(self, interface):
        """Validates the configuration against the interface to find setting and mount usages

        :param interface: The interface dict for the job type
        :type interface: dict
        :returns: A list of warnings discovered during validation.
        :rtype: [:class:`job.configuration.data.job_data.ValidationWarning`]
        """

        warnings = []

        settings_to_delete = []
        if 'settings' in self._configuration and 'settings' in interface and \
           self._configuration['settings'] is not None and interface['settings'] is not None:
            interface_settings = interface['settings']

            # Remove settings not used in the interface
            interface_setting_names = [setting['name'] for setting in interface_settings]
            for setting_name in self._configuration['settings']:
                if setting_name not in interface_setting_names:
                    warning_str = 'Setting %s will be ignored due to no matching interface designation.' % setting_name
                    settings_to_delete.append({'name': setting_name, 'warning': warning_str})

             # Detect any secrets and remove them as settings in configuration
            interface_secret_names = [setting['name'] for setting in interface_settings if setting['secret']]
            for setting_name in interface_secret_names:
                if setting_name in self._configuration['settings']:
                    if setting_name not in settings_to_delete:
                        settings_to_delete.append({'name': setting_name, 'warning': None})

        elif 'settings' in self._configuration and self._configuration['settings'] is not None:
            # Remove all settings
            for setting_name in self._configuration['settings']:
                warning_str = 'Setting %s will be ignored due to no matching interface designation.' % setting_name
                settings_to_delete.append({'name': setting_name, 'warning': warning_str})

        for setting in settings_to_delete:
            del self._configuration['settings'][setting['name']]
            if setting['warning']:
                warnings.append(ValidationWarning('settings', setting['warning']))

        mounts_to_delete = []
        if 'mounts' in interface and 'mounts' in self._configuration and \
           self._configuration['mounts'] is not None and interface['mounts'] is not None:
            interface_mounts = interface['mounts']

            # Remove mounts not used in the interface
            interface_mount_names = [mount['name'] for mount in interface_mounts]
            for mount_name, _mount_value in self._configuration['mounts'].items():
                if mount_name not in interface_mount_names:
                    warning_str = 'Mount %s will be ignored due to no matching interface designation.' % mount_name
                    mounts_to_delete.append({'name': mount_name, 'warning': warning_str})

        elif 'mounts' in self._configuration and self._configuration['mounts'] is not None:
            # Remove all mounts
            for mount_name, _mount_value in self._configuration['mounts'].items():
                warning_str = 'Mount %s will be ignored due to no matching interface designation.' % mount_name
                mounts_to_delete.append({'name': mount_name, 'warning': warning_str})

        for mount in mounts_to_delete:
            del self._configuration['mounts'][mount['name']]
            warnings.append(ValidationWarning('mounts', mount['warning']))

        return warnings

    def _convert_configuration(self):
        """Converts the configuration from a previous schema version

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the given configuration is invalid
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
        for mount in self._configuration['mounts'].values():
            if type == 'volume':
                if 'driver_opts' not in mount:
                    mount['driver_opts'] = {}
        if 'settings' not in self._configuration:
            self._configuration['settings'] = {}

    def _validate_mounts(self):
        """Ensures that the mounts are valid

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the mounts are invalid
        """

        for name, mount in self._configuration['mounts'].iteritems():
            if mount['type'] == 'host':
                if 'host_path' not in mount:
                    raise InvalidJobConfiguration('Host mount %s requires host_path' % name)
                if not os.path.isabs(mount['host_path']):
                    raise InvalidJobConfiguration('Host mount %s must use an absolute host_path' % name)
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

        :raises :class:`job.configuration.exceptions.InvalidJobConfiguration`: If the settings are invalid
        """

        for setting_name, setting_value in self._configuration['settings'].iteritems():
            if not setting_value:
                raise InvalidJobConfiguration('Setting %s has blank value' % setting_name)
