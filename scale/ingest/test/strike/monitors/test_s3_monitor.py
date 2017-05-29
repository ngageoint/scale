from __future__ import unicode_literals

import collections
import json

import django
from django.test import TestCase
from mock import patch

from ingest.strike.monitors.exceptions import (InvalidMonitorConfiguration, SQSNotificationError)
from ingest.strike.monitors.s3_monitor import S3Monitor

SQSMessage = collections.namedtuple('SQSMessage', ['body'])


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

    @patch('ingest.strike.monitors.s3_monitor.SQSClient')
    def test_validate_configuration_success(self, mock_client_class):
        """Tests calling S3Monitor.validate_configuration() successfully"""

        config = {
            'type': 's3',
            'sqs_name': 'my-sqs'
        }

        S3Monitor().validate_configuration(config)

    @patch('ingest.strike.monitors.s3_monitor.S3Monitor._ingest_s3_notification_object')
    def test_process_s3_notification_success(self, ingest_mock):
        """Tests calling S3Monitor._process_s3_notification() successfully"""

        message = {
            "Records": [
                {
                    "eventVersion": "2.0",
                    "awsRegion": "us-east-1",
                    "eventTime": "1970-01-01T00:00:00.000Z",
                    "eventName": "ObjectCreated:Put",
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "testConfigRule",
                        "bucket": {
                            "name": "mybucket",
                            "ownerIdentity": {
                                "principalId": "A3NL1KOZZKExample"
                            },
                            "arn": "arn:aws:s3:::mybucket"
                        },
                        "object": {
                            "key": "HappyFace.jpg",
                            "size": 1024,
                            "eTag": "d41d8cd98f00b204e9800998ecf8427e",
                            "versionId": "096fKKXTRTtl3on89fVO.nfljtsv6qko",
                            "sequencer": "0055AED6DCD90281E5"
                        }
                    }
                }
            ]
        }
        payload = {
            "Message": json.dumps(message)
        }

        sqs_message = SQSMessage(json.dumps(payload))

        monitor = S3Monitor()
        monitor._process_s3_notification(sqs_message)
        self.assertEqual(ingest_mock.call_count, 1)

    def test_process_s3_notification_invalid_json(self):
        """Tests calling S3Monitor._process_s3_notification() with invalid JSON"""

        message = SQSMessage('')

        monitor = S3Monitor()
        with self.assertRaises(SQSNotificationError):
            monitor._process_s3_notification(message)

    def test_process_s3_notification_invalid_message(self):
        """Tests calling S3Monitor._process_s3_notification() with incomplete message"""

        message = SQSMessage('{"incomplete":"message"}')

        monitor = S3Monitor()
        with self.assertRaises(SQSNotificationError):
            monitor._process_s3_notification(message)
