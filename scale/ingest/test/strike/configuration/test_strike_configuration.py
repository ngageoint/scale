from __future__ import unicode_literals

import os

import django
from django.test import TestCase

import storage.test.utils as storage_test_utils
from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from ingest.strike.configuration.strike_configuration import StrikeConfiguration
from ingest.strike.configuration.json.configuration_v6 import StrikeConfigurationV6


from storage.models import Workspace


class TestStrikeConfiguration(TestCase):
    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.new_workspace = storage_test_utils.create_workspace()
        self.inactive_workspace = storage_test_utils.create_workspace(is_active=False)


    def test_validate_bad_monitor_type(self):
        """Tests calling StrikeConfiguration.validate() with a bad monitor type"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'BAD',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
            }],
        }

        configuration = StrikeConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidStrikeConfiguration, configuration.validate)

    def test_validate_mismatched_monitor_type(self):
        """Tests calling StrikeConfiguration.validate() with a monitor type that does not match the broker type"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 's3',
                'sqs_name': 'my-sqs',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
            }],
        }

        configuration = StrikeConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidStrikeConfiguration, configuration.validate)

    def test_validate_bad_workspace(self):
        """Tests calling StrikeConfiguration.validate() with a bad workspace"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_workspace': 'BADWORKSPACE',
            }],
        }

        configuration = StrikeConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidStrikeConfiguration, configuration.validate)

    def test_validate_workspace_not_active(self):
        """Tests calling StrikeConfiguration.validate() with a new workspace that is not active"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_workspace': self.inactive_workspace.name,
            }],
        }

        configuration = StrikeConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidStrikeConfiguration, configuration.validate)

    def test_validate_successful_all(self):
        """Tests calling StrikeConfiguration.validate() successfully with all information"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['one', 'two'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': self.new_workspace.name,
            }],
        }

        # No exception is success
        configuration = StrikeConfigurationV6(config).get_configuration()
        configuration.validate()
