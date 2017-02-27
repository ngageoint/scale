from __future__ import unicode_literals

from util.aws import S3Client

import django
from django.test import TestCase
from mock import MagicMock, Mock, patch

from ingest.scan.scanners.s3_scanner import S3Scanner


class TestS3Monitor(TestCase):

    def setUp(self):
        django.setup()

    def test_set_recursive_false(self):
        """Tests calling S3Scanner.set_recursive() to false"""

        scanner = S3Scanner()
        scanner.set_recursive(False)
        self.assertFalse(scanner._recursive)
        
    def test_recursive_default(self):
        """Tests default property of recursive on S3Scanner instance"""

        scanner = S3Scanner()
        self.assertTrue(scanner._recursive)

    def test_validate_configuration_extra_key(self):
        """Tests calling S3Scanner.validate_configuration() with extra key"""

        config = {
            'type': 's3',
            'random_key': ''
        }
        S3Scanner().validate_configuration(config)

    def test_validate_configuration_success(self):
        """Tests calling S3Scanner.validate_configuration() successfully"""

        config = {
            'type': 's3'
        }
        S3Scanner().validate_configuration(config)
