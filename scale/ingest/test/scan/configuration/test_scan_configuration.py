from __future__ import unicode_literals

import os

import django
from django.test import TestCase

import storage.test.utils as storage_test_utils
from ingest.scan.configuration.exceptions import InvalidScanConfiguration
from ingest.scan.configuration.scan_configuration import ScanConfiguration


class TestScanConfiguration(TestCase):
    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.new_workspace = storage_test_utils.create_workspace()
        self.inactive_workspace = storage_test_utils.create_workspace(is_active=False)

    def test_bare_min(self):
        """Tests calling ScanConfiguration constructor with bare minimum JSON"""

        # No exception is success
        ScanConfiguration({
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        })

    def test_bad_version(self):
        """Tests calling ScanConfiguration constructor with bad version number."""

        config = {
            'version': 'BAD VERSION',
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfiguration, config)

    def test_missing_workspace(self):
        """Tests calling ScanConfiguration constructor with missing workspace"""

        config = {
            'scanner': {
                'type': 'dir',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfiguration, config)

    def test_missing_scanner(self):
        """Tests calling ScanConfiguration constructor with missing scanner"""

        config = {
            'workspace': self.workspace.name,
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfiguration, config)

    def test_blank_filename_regex(self):
        """Tests calling ScanConfiguration constructor with blank filename_regex"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': ''
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfiguration, config)

    def test_absolute_workspace_path(self):
        """Tests calling ScanConfiguration constructor with absolute new_file_path."""

        config = {
            'version': 'BAD VERSION',
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_file_path': '/absolute/path'
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfiguration, config)

    def test_successful_all(self):
        """Tests calling ScanConfiguration constructor successfully with all information"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['one', 'two'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': self.workspace.name,
            }],
        }
        # No exception is success
        ScanConfiguration(config)

    def test_validate_bad_scanner_type(self):
        """Tests calling ScanConfiguration.validate() with a bad scanner type"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'BAD'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
            }],
        }

        self.assertRaises(InvalidScanConfiguration, ScanConfiguration(config).validate)

    def test_validate_mismatched_scanner_type(self):
        """Tests calling ScanConfiguration.validate() with a scanner type that does not match the broker type"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 's3',
                'sqs_name': 'my-sqs',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
            }],
        }

        self.assertRaises(InvalidScanConfiguration, ScanConfiguration(config).validate)

    def test_validate_bad_workspace(self):
        """Tests calling ScanConfiguration.validate() with a bad workspace"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_workspace': 'BADWORKSPACE',
            }],
        }

        self.assertRaises(InvalidScanConfiguration, ScanConfiguration(config).validate)

    def test_validate_workspace_not_active(self):
        """Tests calling ScanConfiguration.validate() with a new workspace that is not active"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_workspace': self.inactive_workspace.name,
            }],
        }

        self.assertRaises(InvalidScanConfiguration, ScanConfiguration(config).validate)

    def test_validate_recursive_invalid_type(self):
        """Tests calling ScanConfiguration.validate() with recursive set to invalid type"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'recursive': 'true',
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_workspace': self.inactive_workspace.name,
            }],
        }

        with self.assertRaises(InvalidScanConfiguration):
            ScanConfiguration(config).validate()

    def test_validate_successful_all(self):
        """Tests calling ScanConfiguration.validate() successfully with all information"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'recursive': True,
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['one', 'two'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': self.new_workspace.name,
            }],
        }

        # No exception is success
        ScanConfiguration(config).validate()
