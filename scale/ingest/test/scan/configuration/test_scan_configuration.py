from __future__ import unicode_literals

import os

import django
from django.test import TestCase

import storage.test.utils as storage_test_utils
from ingest.scan.configuration.exceptions import InvalidScanConfiguration
from ingest.scan.configuration.scan_configuration import ScanConfiguration
from ingest.scan.configuration.json.configuration_1_0 import ScanConfigurationV1
from ingest.scan.configuration.json.configuration_v6 import ScanConfigurationV6


class TestScanConfiguration(TestCase):
    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.new_workspace = storage_test_utils.create_workspace()
        self.inactive_workspace = storage_test_utils.create_workspace(is_active=False)

    def test_bare_min_v1(self):
        """Tests calling ScanConfigurationV1 constructor with bare minimum JSON"""

        # No exception is success
        ScanConfigurationV1({
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }, do_validate=True)
        
    def test_bare_min_v6(self):
        """Tests calling ScanConfigurationV6 constructor with bare minimum JSON"""

        # No exception is success
        ScanConfigurationV6({
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }, do_validate=True)

    def test_bad_version_v1(self):
        """Tests calling ScanConfigurationV1 constructor with bad version number."""

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
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV1, config, True)
        
    def test_bad_version_v1(self):
        """Tests calling ScanConfigurationV6 constructor with bad version number."""

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
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV6, config, True)

    def test_missing_workspace_v1(self):
        """Tests calling ScanConfigurationV1 constructor with missing workspace"""

        config = {
            'scanner': {
                'type': 'dir',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV1, config, True)

    def test_missing_workspace_v6(self):
        """Tests calling ScanConfigurationV6 constructor with missing workspace"""

        config = {
            'scanner': {
                'type': 'dir',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV6, config, True)
        
    def test_missing_scanner_v1(self):
        """Tests calling ScanConfigurationV1 constructor with missing scanner"""

        config = {
            'workspace': self.workspace.name,
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV1, config, True)

    def test_missing_scanner_v6(self):
        """Tests calling ScanConfigurationV6 constructor with missing scanner"""

        config = {
            'workspace': self.workspace.name,
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV6, config, True)
        
    def test_blank_filename_regex_v1(self):
        """Tests calling ScanConfigurationV1 constructor with blank filename_regex"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': ''
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV1, config, True)

    def test_blank_filename_regex_v6(self):
        """Tests calling ScanConfigurationV6 constructor with blank filename_regex"""

        config = {
            'workspace': self.workspace.name,
            'scanner': {
                'type': 'dir'
            },
            'files_to_ingest': [{
                'filename_regex': ''
            }],
        }
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV6, config, True)
        
    def test_absolute_workspace_path_v1(self):
        """Tests calling ScanConfigurationV1 constructor with absolute new_file_path."""

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
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV1, config, True)

    def test_absolute_workspace_path_v6(self):
        """Tests calling ScanConfigurationV6 constructor with absolute new_file_path."""

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
        self.assertRaises(InvalidScanConfiguration, ScanConfigurationV6, config, True)
        
    def test_successful_all_v1(self):
        """Tests calling ScanConfigurationV1 constructor successfully with all information"""

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
        ScanConfigurationV1(config, do_validate=True)

    def test_successful_all_v6(self):
        """Tests calling ScanConfigurationV6 constructor successfully with all information"""

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
        ScanConfigurationV6(config, do_validate=True)
        
    def test_validate_bad_scanner_type_v1(self):
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

        config = ScanConfigurationV1(config).get_configuration()
        self.assertRaises(InvalidScanConfiguration, config.validate)

    def test_validate_bad_scanner_type_v6(self):
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

        config = ScanConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidScanConfiguration, config.validate)
        
    def test_validate_mismatched_scanner_type_v1(self):
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

        config = ScanConfigurationV1(config).get_configuration()
        self.assertRaises(InvalidScanConfiguration, config.validate)
        
    def test_validate_mismatched_scanner_type_v6(self):
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

        config = ScanConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidScanConfiguration, config.validate)

    def test_validate_bad_workspace_v1(self):
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

        config = ScanConfigurationV1(config).get_configuration()
        self.assertRaises(InvalidScanConfiguration, config.validate)

    def test_validate_bad_workspace_v6(self):
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

        config = ScanConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidScanConfiguration, config.validate)
        
    def test_validate_workspace_not_active_v1(self):
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

        config = ScanConfigurationV1(config).get_configuration()
        self.assertRaises(InvalidScanConfiguration, config.validate)
        
    def test_validate_workspace_not_active_v6(self):
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

        config = ScanConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidScanConfiguration, config.validate)
        
    def test_validate_recursive_invalid_type_v1(self):
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
            ScanConfigurationV1(config).get_configuration().validate()

    def test_validate_recursive_invalid_type_v6(self):
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
            ScanConfigurationV6(config).get_configuration().validate()

    def test_validate_successful_all_v1(self):
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
        ScanConfigurationV1(config).get_configuration().validate()

    def test_validate_successful_all_v6(self):
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
        ScanConfigurationV6(config).get_configuration().validate()