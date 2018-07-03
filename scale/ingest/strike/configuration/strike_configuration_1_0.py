"""Defines the configuration for running an instance of Strike"""
from __future__ import unicode_literals

import os
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from storage.models import Workspace

DEFAULT_VERSION = '1.0'

STRIKE_CONFIGURATION_SCHEMA = {
    'type': 'object',
    'required': ['mount', 'transfer_suffix', 'files_to_ingest'],
    'additionalProperties': False,
    'properties': {
        'version': {
            'description': 'Version of the Strike configuration schema',
            'type': 'string'
        },
        'mount': {
            'type': 'string',
            'minLength': 1
        },
        'transfer_suffix': {
            'type': 'string',
            'minLength': 1
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
            'required': ['filename_regex', 'workspace_path', 'workspace_name'],
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
                'workspace_path': {
                    'type': 'string',
                    'minLength': 1
                },
                'workspace_name': {
                    'type': 'string'
                }
            }
        }
    }
}


class StrikeConfiguration(object):
    """Represents the configuration for a running Strike instance. The configuration includes details about mounting the
    transfer NFS directory, the suffix for identifying files still being transferred, and regular expressions to
    identify files to ingest and how to store them.
    """

    def __init__(self, configuration):
        """Creates a Strike configuration object from the given dictionary. The general format is checked for
        correctness, but the specified workspace(s) are not checked.

        :param configuration: The Strike configuration
        :type configuration: dict
        :raises InvalidStrikeConfiguration: If the given configuration is invalid
        """

        self._configuration = configuration

        try:
            validate(configuration, STRIKE_CONFIGURATION_SCHEMA)
        except ValidationError as ex:
            raise InvalidStrikeConfiguration('Invalid Strike configuration: %s' % unicode(ex))

        self._populate_default_values()
        if not self._configuration['version'] == '1.0':
            msg = 'Invalid Strike configuration: %s is an unsupported version number'
            raise InvalidStrikeConfiguration(msg % self._configuration['version'])

        # Normalize paths
        for file_dict in self._configuration['files_to_ingest']:
            if os.path.isabs(file_dict['workspace_path']):
                msg = 'Invalid Strike configuration: workspace_path may not be an absolute path'
                raise InvalidStrikeConfiguration(msg)
            file_dict['workspace_path'] = os.path.normpath(file_dict['workspace_path'])

        # Build a mapping of required workspaces
        self._workspace_map = self._get_workspace_map(self._configuration['files_to_ingest'])

        # Compile and organize regular expressions
        self.file_regex_entries = []  # List of (regex pattern, list of data types, workspace path, workspace)
        for file_dict in self._configuration['files_to_ingest']:
            try:
                regex_pattern = re.compile(file_dict['filename_regex'])
            except re.error:
                raise InvalidStrikeConfiguration('Invalid file name regex: %s' % file_dict['filename_regex'])
            regex_tuple = (regex_pattern, file_dict['data_types'], file_dict['workspace_path'],
                           self._workspace_map[file_dict['workspace_name']])
            self.file_regex_entries.append(regex_tuple)

    def get_dict(self):
        """Returns the internal dictionary that represents this Strike process configuration.

        :returns: The internal dictionary
        :rtype: dict
        """

        return self._configuration

    def get_mount(self):
        """Returns the "mount" value

        :returns: The mount value
        :rtype: str
        """

        return self._configuration['mount']

    def get_transfer_suffix(self):
        """Returns the "transfer_suffix" value

        :returns: The transfer_suffix value
        :rtype: str
        """

        return self._configuration['transfer_suffix']

    def match_file_name(self, file_name):
        """Attempts to match the given file name against this configuration and if a match is made, returns the details
        about how to ingest the file. If no match is found, None is returned

        :param file_name: The name of the file
        :type file_name: str
        :returns: A tuple of the list of data types to add to the file, the remote path for storing the file within the
            workspace, and the workspace, or None if no file name match is found
        :rtype: tuple(list of str, str, :class:`storage.models.Workspace`)
        """

        for regex_entry in self.file_regex_entries:
            if regex_entry[0].match(file_name):
                return regex_entry[1], regex_entry[2], regex_entry[3]
        return None

    def _populate_default_values(self):
        """Goes through the configuration and populates any missing values with defaults."""

        if 'version' not in self._configuration:
            self._configuration['version'] = DEFAULT_VERSION

        for file_dict in self._configuration['files_to_ingest']:
            if 'data_types' not in file_dict:
                file_dict['data_types'] = []

    def _get_workspace_map(self, configuration):
        """Builds a mapping for a workspace and configuration of name to model instance.

        :param configuration: A list of configurations that specify system names of models to fetch and map.
        :type configuration: list[dict]
        :returns: A mapping of workspace system names to associated model instances.
        :rtype: dict[string, :class:`storage.models.Workspace`]
        """

        # Build a mapping of required workspaces
        results = {file_dict['workspace_name']: None for file_dict in configuration}
        for workspace in Workspace.objects.filter(name__in=results.keys()):
            if not workspace.is_active:
                raise InvalidStrikeConfiguration('Workspace is not active: %s' % workspace.name)
            results[workspace.name] = workspace

        # Check for any missing workspace model declarations
        for name, workspace in results.iteritems():
            if not workspace:
                raise InvalidStrikeConfiguration('Unknown workspace reference: %s' % name)
        return results
