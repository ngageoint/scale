from __future__ import unicode_literals

from util.aws import S3Client

import django
from django.test import TestCase
from mock import MagicMock, Mock, patch

from ingest.scan.scanners.exceptions import InvalidScannerConfiguration
from ingest.scan.scanners.s3_scanner import S3Scanner


class TestS3Monitor(TestCase):

    def setUp(self):
        django.setup()

    def test_validate_configuration_missing_sqs_name(self):
        """Tests calling S3Scanner.validate_configuration() with missing bucket_name"""

        config = {
            'type': 's3'
        }
        self.assertRaises(InvalidScannerConfiguration, S3Scanner().validate_configuration, config)

    def test_validate_configuration_bad_sqs_name(self):
        """Tests calling S3Scanner.validate_configuration() with bad type for bucket_name"""

        config = {
            'type': 's3',
            'bucket_name': 1
        }
        self.assertRaises(InvalidScannerConfiguration, S3Scanner().validate_configuration, config)

    def test_validate_configuration_empty_sqs_name(self):
        """Tests calling S3Scanner.validate_configuration() with empty bucket_name"""

        config = {
            'type': 's3',
            'bucket_name': ''
        }
        self.assertRaises(InvalidScannerConfiguration, S3Scanner().validate_configuration, config)

    @patch('ingest.scan.scanners.s3_scanner.S3Client')
    def test_validate_configuration_success(self, mock_client_class):
        """Tests calling S3Scanner.validate_configuration() successfully"""

        config = {
            'type': 's3',
            'bucket_name': 'my-s3'
        }

        S3Scanner().validate_configuration(config)
