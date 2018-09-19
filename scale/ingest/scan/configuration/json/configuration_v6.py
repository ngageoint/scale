"""Manages the v6 batch configuration schema"""
from __future__ import unicode_literals

import logging
import os
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ingest.handlers.file_handler import FileHandler
from ingest.handlers.file_rule import FileRule
from ingest.scan.configuration.scan_configuration import ScanConfiguration
from ingest.scan.configuration.exceptions import InvalidScanConfiguration
from ingest.scan.scanners import factory
from storage.models import Workspace

logger = logging.getLogger(__name__)

SCHEMA_VERSION = '6'

SCAN_CONFIGURATION_SCHEMA = {
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
        },
        'recursive': {
            'type': 'boolean'
        },
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

def convert_config_to_v6_json(config):
    """Returns the v6 scan configuration JSON for the given configuration

    :param config: The scan configuration
    :type config: :class:`ingest.scan.configuration.scan_configuration.ScanConfiguration`
    :returns: The v6 scan configuration JSON
    :rtype: :class:`ingest.scan.configuration.json.configuration_v6.ScanConfigurationV6`
    """

    config_dict = config.config_dict
    config_dict['version'] = SCHEMA_VERSION

    return ScanConfigurationV6(configuration=config_dict, do_validate=False)


class ScanConfigurationV6(object):
    """Represents the configuration for a running Scan instance. The configuration includes details about mounting the
    transfer directory, the suffix for identifying files still being transferred, and regular expressions to
    identify files to ingest and how to store them.
    """

    def __init__(self, configuration, do_validate=False):
        """Creates a Scan configuration object from the given dictionary. The general format is checked for
        correctness, but the specified workspace(s) are not checked.

        :param configuration: The Scan configuration
        :type configuration: dict
        :raises InvalidScanConfiguration: If the given configuration is invalid
        """

        self._configuration = configuration

        # Convert old versions
        if 'version' in self._configuration and self._configuration['version'] == '1.0':
            self._configuration['version'] = '6'
        if 'version' not in self._configuration:
            self._configuration['version'] = '6'

        try:
            if do_validate:
                validate(self._configuration, SCAN_CONFIGURATION_SCHEMA)
        except ValidationError as ex:
            raise InvalidScanConfiguration('Invalid Scan configuration: %s' % unicode(ex))

        self._populate_default_values()
        if self._configuration['version'] != SCHEMA_VERSION:
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

    def get_configuration(self):
        """Returns the scan configuration represented by this JSON

        :returns: The scan configuration
        :rtype: :class:`ingest.scan.configuration.scan_configuration.ScanConfiguration`:
        """

        config = ScanConfiguration()
        
        config.scanner_type     = self._configuration['scanner']['type']
        config.scanner_config   = self._configuration['scanner']
        config.recursive        = self._configuration['recursive']
        config.file_handler     = self._file_handler
        config.workspace        = self._configuration['workspace']

        return config
        
    def get_dict(self):
        """Returns the internal dictionary that represents this Strike process configuration.

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration

    def _convert_schema(self, configuration):
        """Upgrade schema from a previous version

        :param configuration: The Scan configuration
        :type configuration: dict
        :returns: The converted configuration
        :rtype: dict
        """

        config = configuration
        if 'version' in config and config['version'] == '1.0':
            config['version'] = '6'
        return config

    def _populate_default_values(self):
        """Goes through the configuration and populates any missing values with defaults."""

        if 'version' not in self._configuration:
            self._configuration['version'] = SCHEMA_VERSION

        if 'recursive' not in self._configuration:
            self._configuration['recursive'] = True

        for file_dict in self._configuration['files_to_ingest']:
            if 'data_types' not in file_dict:
                file_dict['data_types'] = []