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
    def test_process_s3_sqs_direct_notification_success(self, ingest_mock):
        """Tests calling S3Monitor._process_s3_notification() successfully with minimal v2.0 direct S3 event"""

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

        sqs_message = SQSMessage(json.dumps(message))

        monitor = S3Monitor()
        monitor._process_s3_notification(sqs_message)
        self.assertEqual(ingest_mock.call_count, 1)

    @patch('ingest.strike.monitors.s3_monitor.S3Monitor._ingest_s3_notification_object')
    def test_process_s3_minimal_notification_success(self, ingest_mock):
        """Tests calling S3Monitor._process_s3_notification() successfully with minimal v2.0 message from SNS->SQS"""

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

        payload = { "Message": json.dumps(message)}
        sqs_message = SQSMessage(json.dumps(payload))

        monitor = S3Monitor()
        monitor._process_s3_notification(sqs_message)
        self.assertEqual(ingest_mock.call_count, 1)

    @patch('ingest.strike.monitors.s3_monitor.S3Monitor._ingest_s3_notification_object')
    def test_process_s3_notional_v2_notification_success(self, ingest_mock):
        """Tests calling S3Monitor._process_s3_notification() successfully with notional v2 message"""

        message = {
            "Records": [
                {
                    "eventVersion": "2.x",
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

        payload = { "Message": json.dumps(message)}
        sqs_message = SQSMessage(json.dumps(payload))

        monitor = S3Monitor()
        monitor._process_s3_notification(sqs_message)
        self.assertEqual(ingest_mock.call_count, 1)

    @patch('ingest.strike.monitors.s3_monitor.S3Monitor._ingest_s3_notification_object')
    def test_process_s3_v21_notification_success(self, ingest_mock):
        """Tests calling S3Monitor._process_s3_notification() successfully with eventVersion 2.1"""

        message = {
            "Records": [
                {
                    "eventVersion": "2.1",
                    "eventSource": "aws:s3",
                    "awsRegion": "us-west-2",
                    "eventTime": "1970-01-01T00:00:00.000Z",
                    "eventName": "ObjectCreated:Put",
                    "userIdentity": {
                        "principalId": "Amazon-customer-ID-of-the-user-who-caused-the-event"
                    },
                    "requestParameters": {
                        "sourceIPAddress": "ip-address-where-request-came-from"
                    },
                    "responseElements": {
                        "x-amz-request-id": "Amazon S3 generated request ID",
                        "x-amz-id-2": "Amazon S3 host that processed the request"
                    },
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "ID found in the bucket notification configuration",
                        "bucket": {
                            "name": "bucket-name",
                            "ownerIdentity": {
                                "principalId": "Amazon-customer-ID-of-the-bucket-owner"
                            },
                            "arn": "bucket-ARN"
                        },
                        "object": {
                            "key": "object-key",
                            "size": 1024,
                            "eTag": "object eTag",
                            "versionId": "object version if bucket is versioning-enabled, otherwise null",
                            "sequencer": "0055AED6DCD90281E5"
                        }
                    },
                    "glacierEventData": {
                        "restoreEventData": {
                            "lifecycleRestorationExpiryTime": "1970-01-01T00:00:00.000Z",
                            "lifecycleRestoreStorageClass": "Source storage class for restore"
                        }
                    }
                }
            ]
        }

        payload = { "Message": json.dumps(message)}
        sqs_message = SQSMessage(json.dumps(payload))

        monitor = S3Monitor()
        monitor._process_s3_notification(sqs_message)
        self.assertEqual(ingest_mock.call_count, 1)

    @patch('ingest.strike.monitors.s3_monitor.S3Monitor._ingest_s3_notification_object')
    def test_process_s3_v20_notification_success(self, ingest_mock):
        """Tests calling S3Monitor._process_s3_notification() successfully with eventVersion 2.0"""

        message = {
            "Records": [
                {
                    "eventVersion": "2.0",
                    "eventSource": "aws:s3",
                    "awsRegion": "us-west-2",
                    "eventTime": "1970-01-01T00:00:00.000Z",
                    "eventName": "ObjectCreated:Put",
                    "userIdentity": {
                        "principalId": "Amazon-customer-ID-of-the-user-who-caused-the-event"
                    },
                    "requestParameters": {
                        "sourceIPAddress": "ip-address-where-request-came-from"
                    },
                    "responseElements": {
                        "x-amz-request-id": "Amazon S3 generated request ID",
                        "x-amz-id-2": "Amazon S3 host that processed the request"
                    },
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "ID found in the bucket notification configuration",
                        "bucket": {
                            "name": "bucket-name",
                            "ownerIdentity": {
                                "principalId": "Amazon-customer-ID-of-the-bucket-owner"
                            },
                            "arn": "bucket-ARN"
                        },
                        "object": {
                            "key": "object-key",
                            "size": 1024,
                            "eTag": "object eTag",
                            "versionId": "object version if bucket is versioning-enabled, otherwise null",
                            "sequencer": "0055AED6DCD90281E5"
                        }
                    }
                }
            ]
        }

        payload = { "Message": json.dumps(message)}
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

    def test_process_s3_notification_invalid_event_name(self):
        """Tests calling S3Monitor._process_s3_notification() with invalid JSON"""

        message = {
            "Records": [
                {
                    "eventVersion": "2.0",
                    "awsRegion": "us-east-1",
                    "eventTime": "1970-01-01T00:00:00.000Z",
                    "eventName": "ObjectDeleted:Put",
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

        payload = { "Message": json.dumps(message)}
        sqs_message = SQSMessage(json.dumps(payload))

        monitor = S3Monitor()
        with self.assertRaises(SQSNotificationError):
            monitor._process_s3_notification(sqs_message)

    def test_process_s3_notification_invalid_event_version(self):
        """Tests calling S3Monitor._process_s3_notification() with invalid JSON"""

        message = {
            "Records": [
                {
                    "eventVersion": "1.0",
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

        payload = { "Message": json.dumps(message)}
        sqs_message = SQSMessage(json.dumps(payload))

        monitor = S3Monitor()
        with self.assertRaises(SQSNotificationError):
            monitor._process_s3_notification(sqs_message)

    def test_process_s3_notification_invalid_message(self):
        """Tests calling S3Monitor._process_s3_notification() with incomplete message"""

        message = SQSMessage('{"incomplete":"message"}')

        monitor = S3Monitor()
        with self.assertRaises(SQSNotificationError):
            monitor._process_s3_notification(message)
