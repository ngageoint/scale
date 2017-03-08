from __future__ import unicode_literals

import os

import django
from django.test import TestCase

import storage.test.utils as storage_test_utils
from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from ingest.strike.configuration.strike_configuration import StrikeConfiguration
from storage.models import Workspace


class TestStrikeConfiguration(TestCase):
    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.new_workspace = storage_test_utils.create_workspace()
        self.inactive_workspace = storage_test_utils.create_workspace(is_active=False)

    def test_bare_min(self):
        """Tests calling StrikeConfiguration constructor with bare minimum JSON"""

        # No exception is success
        StrikeConfiguration({
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        })

    def test_bad_version(self):
        """Tests calling StrikeConfiguration constructor with bad version number."""

        config = {
            'version': 'BAD VERSION',
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_missing_workspace(self):
        """Tests calling StrikeConfiguration constructor with missing workspace"""

        config = {
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_missing_monitor(self):
        """Tests calling StrikeConfiguration constructor with missing monitor"""

        config = {
            'workspace': self.workspace.name,
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_blank_filename_regex(self):
        """Tests calling StrikeConfiguration constructor with blank filename_regex"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': ''
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_absolute_workspace_path(self):
        """Tests calling StrikeConfiguration constructor with absolute new_file_path."""

        config = {
            'version': 'BAD VERSION',
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_file_path': '/absolute/path'
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_successful_all(self):
        """Tests calling StrikeConfiguration constructor successfully with all information"""

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
                'new_workspace': self.workspace.name,
            }],
        }
        # No exception is success
        StrikeConfiguration(config)

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

        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration(config).validate)

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

        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration(config).validate)

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

        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration(config).validate)

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

        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration(config).validate)

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
        StrikeConfiguration(config).validate()

    def test_conversion_from_1_0(self):
        """Tests calling StrikeConfiguration.validate() after converting from schema version 1.0"""

        old_config = {
            'version': '1.0',
            'transfer_suffix': '_tmp',
            'mount': 'host:/my/path',
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['one', 'two'],
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.new_workspace.name,
            }],
        }

        strike_config = StrikeConfiguration(old_config)
        strike_config.validate()

        auto_workspace = Workspace.objects.get(name__contains='auto')
        new_config = {
            'version': '2.0',
            'workspace': auto_workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['one', 'two'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': self.new_workspace.name,
            }]
        }
        self.assertDictEqual(strike_config._configuration, new_config)

        auto_workspace_config = {
            'version': '1.0',
            'broker': {
                'type': 'host',
                'host_path': '/my/path'
            }
        }
        self.assertDictEqual(auto_workspace.json_config, auto_workspace_config)
