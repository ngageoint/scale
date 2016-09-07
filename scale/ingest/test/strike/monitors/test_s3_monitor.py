from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import MagicMock, Mock, patch

from ingest.strike.monitors.exceptions import InvalidMonitorConfiguration
from ingest.strike.monitors.s3_monitor import S3Monitor


class TestS3Monitor(TestCase):

    def setUp(self):
        django.setup()

    def test_validate_configuration_missing_sqs_name(self):
        """Tests calling S3Monitor.validate_configuration() with missing sqs_name"""

        config = {
            'type': 's3'
        }
        self.assertRaises(InvalidMonitorConfiguration, S3Monitor().validate_configuration, config)

    def test_validate_configuration_bad_sqs_name(self):
        """Tests calling S3Monitor.validate_configuration() with bad type for sqs_name"""

        config = {
            'type': 's3',
            'sqs_name': 1
        }
        self.assertRaises(InvalidMonitorConfiguration, S3Monitor().validate_configuration, config)

    def test_validate_configuration_empty_sqs_name(self):
        """Tests calling S3Monitor.validate_configuration() with empty sqs_name"""

        config = {
            'type': 's3',
            'sqs_name': ''
        }
        self.assertRaises(InvalidMonitorConfiguration, S3Monitor().validate_configuration, config)

    @patch('util.aws.SQSClient')
    def test_validate_configuration_success(self, mock_client_class):
        """Tests calling S3Monitor.validate_configuration() successfully"""

        config = {
            'type': 's3',
            'sqs_name': 'my-sqs'
        }

        mock_client = MagicMock()
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)

        S3Monitor().validate_configuration(config)
        S3Monitor().validate_configuration(config)
