"""Manages the v6 batch configuration schema"""
from __future__ import unicode_literals

import logging
import os
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ingest.handlers.file_handler import FileHandler
from ingest.handlers.file_rule import FileRule
from ingest.strike.configuration.strike_configuration import StrikeConfiguration
from ingest.strike.configuration.json.configuration_1_0 import StrikeConfigurationV1
from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from ingest.strike.monitors import factory
from storage.models import Workspace

logger = logging.getLogger(__name__)

SCHEMA_VERSION = '6'

STRIKE_CONFIGURATION_SCHEMA = {
    'type': 'object',
    'required': ['workspace', 'monitor', 'files_to_ingest'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the Strike configuration schema',
            'type': 'string'
        },
        'workspace': {
            'type': 'string',
            'minLength': 1
        },
        'monitor': {
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


class StrikeConfigurationV6(object):
    """Represents the configuration for a running Strike instance. The configuration includes details about mounting the
    transfer NFS directory, the suffix for identifying files still being transferred, and regular expressions to
    identify files to ingest and how to store them.
    """

    def __init__(self, configuration, do_validate=False):
        """Creates a Strike configuration object from the given dictionary. The general format is checked for
        correctness, but the specified workspace(s) are not checked.

        :param configuration: The Strike configuration
        :type configuration: dict
        :raises InvalidStrikeConfiguration: If the given configuration is invalid
        """

        self._configuration = configuration

        # Convert old versions
        if 'version' in self._configuration and self._configuration['version'] == '1.0':
            self._configuration = self._convert_schema(configuration)
            
        if 'version' in self._configuration and self._configuration['version'] == '2.0':
            self._configuration['version'] = '6'

        try:
            if do_validate:
                validate(configuration, STRIKE_CONFIGURATION_SCHEMA)
        except ValidationError as ex:
            raise InvalidStrikeConfiguration('Invalid Strike configuration: %s' % unicode(ex))

        self._populate_default_values()
        if self._configuration['version'] != SCHEMA_VERSION:
            msg = 'Invalid Strike configuration: %s is an unsupported version number'
            raise InvalidStrikeConfiguration(msg % self._configuration['version'])

        self._file_handler = FileHandler()
        for file_dict in self._configuration['files_to_ingest']:
            try:
                regex_pattern = re.compile(file_dict['filename_regex'])
            except re.error:
                raise InvalidStrikeConfiguration('Invalid file name regex: %s' % file_dict['filename_regex'])
            new_workspace = None
            if 'new_workspace' in file_dict:
                new_workspace = file_dict['new_workspace']
            new_file_path = None
            if 'new_file_path' in file_dict:
                if os.path.isabs(file_dict['new_file_path']):
                    msg = 'Invalid Strike configuration: new_file_path may not be an absolute path'
                    raise InvalidStrikeConfiguration(msg)
                file_dict['new_file_path'] = os.path.normpath(file_dict['new_file_path'])
                new_file_path = file_dict['new_file_path']
            rule = FileRule(regex_pattern, file_dict['data_types'], new_workspace, new_file_path)
            self._file_handler.add_rule(rule)

    def get_dict(self):
        """Returns the internal dictionary that represents this Strike process configuration.

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration
        
    def get_configuration(self):
        """Returns the strike configuration represented by this JSON

        :returns: The strike configuration
        :rtype: :class:`ingest.strike.configuration.strike_configuration.StrikeConfiguration`:
        """

        config = StrikeConfiguration()
        
        config.configuration    = self._configuration
        config.file_handler     = self._file_handler

        return config

    def _convert_schema(self, configuration):
        """Tries to validate the configuration as version 1.0 and convert it to version 6

        :param configuration: The Strike configuration
        :type configuration: dict
        :returns: The converted configuration
        :rtype: dict
        """

        # Try converting from 1.0
        converted_configuration = StrikeConfigurationV1(configuration).get_dict()
        converted_configuration['version'] = SCHEMA_VERSION

        mount = converted_configuration['mount']
        mount_path = mount.split(':')[1]
        transfer_suffix = converted_configuration['transfer_suffix']
        del converted_configuration['mount']
        del converted_configuration['transfer_suffix']
        auto_workspace_name = 'auto_wksp_for_%s' % mount.replace(':', '_').replace('/', '_')
        auto_workspace_name = auto_workspace_name[:50]  # Truncate to max name length of 50 chars
        title = 'Auto Workspace for %s' % mount
        title = title[:50]  # Truncate to max title length of 50 chars
        try:
            Workspace.objects.get(name=auto_workspace_name)
        except Workspace.DoesNotExist:
            workspace = Workspace()
            workspace.name = auto_workspace_name
            workspace.title = title
            desc = 'This workspace was automatically created for mount %s to support converting Strike from 1.0 to 2.0'
            workspace.description = desc % mount
            workspace.json_config = {'version': '1.0', 'broker': {'type': 'host', 'host_path': mount_path}}
            workspace.save()

        converted_configuration['workspace'] = auto_workspace_name
        converted_configuration['monitor'] = {'type': 'dir-watcher', 'transfer_suffix': transfer_suffix}
        for file_dict in converted_configuration['files_to_ingest']:
            file_dict['new_workspace'] = file_dict['workspace_name']
            file_dict['new_file_path'] = file_dict['workspace_path']
            del file_dict['workspace_name']
            del file_dict['workspace_path']

        return converted_configuration

    def _populate_default_values(self):
        """Goes through the configuration and populates any missing values with defaults."""

        if 'version' not in self._configuration:
            self._configuration['version'] = SCHEMA_VERSION

        for file_dict in self._configuration['files_to_ingest']:
            if 'data_types' not in file_dict:
                file_dict['data_types'] = []
