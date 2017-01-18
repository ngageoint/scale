"""Defines the configuration for running an instance of Scan"""
from __future__ import unicode_literals

import logging
import os
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ingest.scan.configuration.exceptions import InvalidScanConfiguration
from ingest.scan.configuration.scan_configuration_1_0 import ScanConfiguration as ScanConfiguration_1_0
from ingest.scan.handlers.file_handler import FileHandler
from ingest.scan.handlers.file_rule import FileRule
from ingest.scan.monitors import factory
from storage.models import Workspace


logger = logging.getLogger(__name__)


CURRENT_VERSION = '1.0'


STRIKE_CONFIGURATION_SCHEMA = {
    'type': 'object',
    'required': ['workspace', 'scanner', 'files_to_ingest'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the Scan configuration schema',
            'type': 'string'
        },
        'workspace': {
            'type': 'string',
            'minLength': 1
        },
        'scanner': {
            'type': 'object',
            'required': ['type'],
            'additionalProperties': True,
            'properties': {
                'type': {
                    'type': 'string',
                    'minLength': 1
                },
            }
        },
        'files_to_ingest': {
            'type': 'array',
            'minItems': 1,
            'items': {'$ref': '#/definitions/file_item'}
        }
    },
    'definitions': {
        'file_item': {
            'type': 'object',
            'required': ['filename_regex'],
            'additionalProperties': False,
            'properties': {
                'filename_regex': {
                    'type': 'string',
                    'minLength': 1
                },
                'recursive': {
                    'type': 'boolean'
                },
                'data_types': {
                    'type': 'array',
                    'items': {'type': 'string', 'minLength': 1}
                },
                'new_workspace': {
                    'type': 'string',
                    'minLength': 1
                },
                'new_file_path': {
                    'type': 'string',
                    'minLength': 1
                }
            }
        }
    }
}


class ValidationWarning(object):
    """Tracks Scan configuration warnings during validation that may prevent the process from working."""

    def __init__(self, key, details):
        """Constructor sets basic attributes.

        :param key: A unique identifier clients can use to recognize the warning.
        :type key: string
        :param details: A user-friendly description of the problem, including field names and/or associated values.
        :type details: string
        """
        self.key = key
        self.details = details


class ScanConfiguration(object):
    """Represents the configuration for a running Scan instance. The configuration includes details about mounting the
    transfer directory, the suffix for identifying files still being transferred, and regular expressions to
    identify files to ingest and how to store them.
    """

    def __init__(self, configuration):
        """Creates a Scan configuration object from the given dictionary. The general format is checked for
        correctness, but the specified workspace(s) are not checked.

        :param configuration: The Scan configuration
        :type configuration: dict
        :raises InvalidScanConfiguration: If the given configuration is invalid
        """

        self._configuration = configuration

        try:
            validate(configuration, STRIKE_CONFIGURATION_SCHEMA)
        except ValidationError as ex:
            raise InvalidScanConfiguration('Invalid Scan configuration: %s' % unicode(ex))

        self._populate_default_values()
        if self._configuration['version'] != CURRENT_VERSION:
            msg = 'Invalid Scan configuration: %s is an unsupported version number'
            raise InvalidScanConfiguration(msg % self._configuration['version'])

        self._file_handler = FileHandler()
        for file_dict in self._configuration['files_to_ingest']:
            try:
                regex_pattern = re.compile(file_dict['filename_regex'])
            except re.error:
                raise InvalidScanConfiguration('Invalid file name regex: %s' % file_dict['filename_regex'])
            new_workspace = None
            if 'new_workspace' in file_dict:
                new_workspace = file_dict['new_workspace']
            new_file_path = None
            if 'new_file_path' in file_dict:
                if os.path.isabs(file_dict['new_file_path']):
                    msg = 'Invalid Scan configuration: new_file_path may not be an absolute path'
                    raise InvalidScanConfiguration(msg)
                file_dict['new_file_path'] = os.path.normpath(file_dict['new_file_path'])
                new_file_path = file_dict['new_file_path']
            rule = FileRule(regex_pattern, file_dict['data_types'], new_workspace, new_file_path)
            self._file_handler.add_rule(rule)

    def get_dict(self):
        """Returns the internal dictionary that represents this Scan process configuration.

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration

    def get_monitor(self):
        """Returns the configured monitor for this Scan configuration

        :returns: The configured monitor
        :rtype: :class:`ingest.scan.monitors.monitor.Monitor`
        """

        monitor_type = self._configuration['monitor']['type']
        monitor = factory.get_monitor(monitor_type)
        self.load_monitor_configuration(monitor)
        return monitor

    def get_workspace(self):
        """Returns the monitored workspace name for this Scan configuration

        :returns: The monitored workspace name
        :rtype: string
        """

        return self._configuration['workspace']

    def load_monitor_configuration(self, monitor):
        """Loads the configuration into the given monitor

        :param monitor: The configuration as a dictionary
        :type monitor: :class:`ingest.scan.monitors.monitor.Monitor`
        """

        monitor_dict = self._configuration['monitor']
        monitor_type = monitor_dict['type']
        workspace = self._configuration['workspace']

        # Only load configuration if monitor type is unchanged
        if monitor_type == monitor.monitor_type:
            monitor.setup_workspaces(workspace, self._file_handler)
            monitor.load_configuration(monitor_dict)
        else:
            msg = 'Scan monitor type has been changed from %s to %s. Cannot reload configuration.'
            logger.warning(msg, monitor.monitor_type, monitor_type)

    def validate(self):
        """Validates the Scan configuration

        :returns: A list of warnings discovered during validation
        :rtype: list[:class:`ingest.scan.configuration.scan_configuration.ValidationWarning`]

        :raises :class:`ingest.scan.configuration.exceptions.InvalidScanConfiguration`: If the configuration is
            invalid.
        """

        warnings = []

        monitor_type = self._configuration['monitor']['type']
        if monitor_type not in factory.get_monitor_types():
            raise InvalidScanConfiguration('\'%s\' is an invalid monitor type' % monitor_type)

        monitored_workspace_name = self._configuration['workspace']
        workspace_names = {monitored_workspace_name}
        for rule in self._file_handler.rules:
            if rule.new_workspace:
                workspace_names.add(rule.new_workspace)

        for workspace in Workspace.objects.filter(name__in=workspace_names):
            if workspace.name == monitored_workspace_name:
                broker_type = workspace.get_broker().broker_type
                monitor = factory.get_monitor(monitor_type)
                if broker_type not in monitor.supported_broker_types:
                    msg = 'Monitor type %s does not support broker type %s'
                    raise InvalidScanConfiguration(msg % (monitor_type, broker_type))
            if not workspace.is_active:
                raise InvalidScanConfiguration('Workspace is not active: %s' % workspace.name)
            workspace_names.remove(workspace.name)

        if workspace_names:
            raise InvalidScanConfiguration('Unknown workspace name: %s' % workspace_names.pop())

        return warnings

    def _convert_schema(self, configuration):
        """Upgrade schema from a previous version

        :param configuration: The Scan configuration
        :type configuration: dict
        :returns: The converted configuration
        :rtype: dict
        """

        raise NotImplementedError

    def _populate_default_values(self):
        """Goes through the configuration and populates any missing values with defaults."""

        if 'version' not in self._configuration:
            self._configuration['version'] = CURRENT_VERSION

        for file_dict in self._configuration['files_to_ingest']:
            if 'recursive' not in file_dict:
                file_dict['recursive'] = True

            if 'data_types' not in file_dict:
                file_dict['data_types'] = []
