from __future__ import unicode_literals

from mock import Mock, patch

import django
from django.test import TestCase

from ingest.scan.scanners.dir_scanner import DirScanner
from ingest.scan.configuration.exceptions import InvalidScanConfiguration


class TestDirScanner(TestCase):

    def setUp(self):
        django.setup()

    def test_load_configuration(self):
        """Tests calling DirScanner.load_configuration() successfully"""
        config = {
            'type': 'dir',
            'transfer_suffix': '_tmp'
        }
        
        scanner = DirScanner()
        
        self.assertIsNone(scanner._transfer_suffix)
        
        scanner.load_configuration(config)
        
        self.assertEquals('_tmp', scanner._transfer_suffix)

    def test_validate_configuration_missing_transfer_suffix(self):
        """Tests calling DirScanner.validate_configuration() with missing transfer_suffix"""

        config = {
            'type': 'dir'
        }
        self.assertRaises(InvalidScanConfiguration, DirScanner().validate_configuration, config)

    def test_validate_configuration_bad_transfer_suffix(self):
        """Tests calling DirScanner.validate_configuration() with bad type for transfer_suffix"""

        config = {
            'type': 'dir',
            'transfer_suffix': 1
        }
        self.assertRaises(InvalidScanConfiguration, DirScanner().validate_configuration, config)

    def test_validate_configuration_empty_transfer_suffix(self):
        """Tests calling DirScanner.validate_configuration() with empty transfer_suffix"""

        config = {
            'type': 'dir',
            'transfer_suffix': ''
        }
        self.assertRaises(InvalidScanConfiguration, DirScanner().validate_configuration, config)

    def test_validate_configuration_success(self):
        """Tests calling DirScanner.validate_configuration() successfully"""

        config = {
            'type': 'dir',
            'transfer_suffix': '_tmp'
        }
        DirScanner().validate_configuration(config)

    @patch('ingest.scan.scanners.dir_scanner.DirScanner._process_ingest')
    def test_ingest_file(self, process_ingest):
        """Tests calling DirScanner._ingest_file() with dry_run off successfully"""

        file_name = 'file_name'
        process_ingest.return_value = file_name
        
        config = {
            'type': 'dir',
            'transfer_suffix': '_tmp'
        }
        
        scanner = DirScanner()
        scanner._scanned_workspace = Mock()
        scanner.load_configuration(config)
        
        ingest_file = scanner._ingest_file(file_name, 0)
        
        self.assertTrue(process_ingest.called)
        self.assertEquals(ingest_file, file_name)
        
    def test_ingest_file_in_transit(self):
        """Tests calling DirScanner._ingest_file() with dry_run off and transfer in-progress"""
        
        config = {
            'type': 'dir',
            'transfer_suffix': '_tmp'
        }
        
        scanner = DirScanner()
        scanner._scanned_workspace = Mock()
        scanner.load_configuration(config)
        
        ingest_file = scanner._ingest_file('file_name_tmp', 0)
        
        self.assertIsNone(ingest_file)
        
    def test_ingest_file_dry_run(self):
        """Tests calling DirScanner._ingest_file() in dry_run mode"""
        
        scanner = DirScanner()
        scanner._dry_run = True
        scanner._scanned_workspace = Mock()
        
        ingest_file = scanner._ingest_file('file_name', 0)
        
        self.assertIsNone(ingest_file)
