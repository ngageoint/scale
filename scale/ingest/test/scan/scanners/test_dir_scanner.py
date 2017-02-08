from __future__ import unicode_literals

import django
from django.test import TestCase

from ingest.scan.scanners.dir_scanner import DirScanner
from ingest.scan.configuration.exceptions import InvalidScanConfiguration


class TestDirScanner(TestCase):

    def setUp(self):
        django.setup()

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
