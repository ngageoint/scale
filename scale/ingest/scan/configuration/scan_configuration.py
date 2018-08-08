"""Defines the configuration for running an instance of Scan"""
from __future__ import unicode_literals

import logging
import os
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ingest.handlers.file_handler import FileHandler
from ingest.handlers.file_rule import FileRule
from ingest.scan.configuration.exceptions import InvalidScanConfiguration
from ingest.scan.scanners import factory
from storage.models import Workspace

logger = logging.getLogger(__name__)

CURRENT_VERSION = '1.0'

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

    def __init__(self):
        """Creates a Scan configuration object.

        :param configuration: The Scan configuration
        :type configuration: dict
        :raises InvalidScanConfiguration: If the given configuration is invalid
        """
        
        self.scanner_type = ''
        
        self.scanner_confg = {}
        
        self.recursive = True

        self.file_handler = FileHandler()
        
        self.workspace = ''

    def get_scanner(self):
        """Returns the configured scanner for this Scan configuration

        :returns: The configured scanner
        :rtype: :class:`ingest.scan.scanners.scanner.Scanner`
        """

        scanner = factory.get_scanner(self.scanner_type)
        self.load_scanner_configuration(scanner)
        return scanner

    def get_workspace(self):
        """Returns the workspace name to be scanned for this Scan configuration

        :returns: The workspace name
        :rtype: string
        """

        return self.workspace

    def load_scanner_configuration(self, scanner):
        """Loads the configuration into the given scanner

        :param scanner: The configuration as a dictionary
        :type scanner: :class:`ingest.scan.scanners.scanner.Scanner`
        """

        # Only load configuration if scanner type is unchanged
        if self.scanner_type == scanner.scanner_type:
            scanner.setup_workspaces(self.workspace, self.file_handler)
            scanner.load_configuration(self.scanner_confg)
            scanner.set_recursive(self.recursive)
        else:
            msg = 'Scan scanner type has been changed from %s to %s. Cannot reload configuration.'
            logger.warning(msg, scanner.scanner_type, self.scanner_type)

    def validate(self):
        """Validates the Scan configuration

        :returns: A list of warnings discovered during validation
        :rtype: list[:class:`ingest.scan.configuration.scan_configuration.ValidationWarning`]

        :raises :class:`ingest.scan.configuration.exceptions.InvalidScanConfiguration`: If the configuration is
            invalid.
        """

        warnings = []

        scanner_type = self.scanner_type
        if scanner_type not in factory.get_scanner_types():
            raise InvalidScanConfiguration('\'%s\' is an invalid scanner' % scanner_type)

        scanned_workspace_name = self.workspace
        workspace_names = {scanned_workspace_name}
        for rule in self.file_handler.rules:
            if rule.new_workspace:
                workspace_names.add(rule.new_workspace)

        for workspace in Workspace.objects.filter(name__in=workspace_names):
            if workspace.name == scanned_workspace_name:
                broker_type = workspace.get_broker().broker_type
                scanner = factory.get_scanner(scanner_type)
                if broker_type not in scanner.supported_broker_types:
                    msg = 'Scanner type %s does not support broker type %s'
                    raise InvalidScanConfiguration(msg % (scanner_type, broker_type))
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

        for file_dict in self._configuration['files_to_ingest']:
            if 'data_types' not in file_dict:
                file_dict['data_types'] = []
