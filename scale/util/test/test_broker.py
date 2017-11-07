from __future__ import unicode_literals

import django
from django.test import TestCase
from util.broker import BrokerDetails
from util.exceptions import InvalidBrokerUrl


class TestBroker(TestCase):
    def setUp(self):
        django.setup()

    def test_valid_sqs_broker_url(self):
        """Tests instantiating broker from URL for SQS with Access and Secret Key."""
        broker_url = 'sqs://access:secret@us-east-1//'
        broker = BrokerDetails.from_broker_url(broker_url)

        self.assertEqual(broker.get_type(), 'sqs')
        self.assertEqual(broker.get_user_name(), 'access')
        self.assertEqual(broker.get_password(), 'secret')
        self.assertEqual(broker.get_address(), 'us-east-1')
        self.assertEqual(broker.get_virtual_host(), '/')

    def test_valid_sqs_broker_url_no_credentials(self):
        """Tests instantiating broker from URL for SQS without keys."""
        broker_url = 'sqs://us-east-1'
        broker = BrokerDetails.from_broker_url(broker_url)

        self.assertEqual(broker.get_type(), 'sqs')
        self.assertIsNone(broker.get_user_name())
        self.assertIsNone(broker.get_password())
        self.assertEqual(broker.get_address(), 'us-east-1')
        self.assertIsNone(broker.get_virtual_host())

    def test_valid_rabbitmq_broker_url(self):
        """Tests instantiating broker from URL for RabbitMQ."""
        broker_url = 'amqp://guest:pass@localhost:5672/custom'
        broker = BrokerDetails.from_broker_url(broker_url)

        self.assertEqual(broker.get_type(), 'amqp')
        self.assertEqual(broker.get_user_name(), 'guest')
        self.assertEqual(broker.get_password(), 'pass')
        self.assertEqual(broker.get_address(), 'localhost:5672')
        self.assertEqual(broker.get_virtual_host(), 'custom')

    def test_bad_credentials_broker_url(self):
        """Tests instantiating broker from invalid URL with credential delimiter."""
        broker_url = 'sqs://@us-east-1'
        with self.assertRaises(InvalidBrokerUrl):
            BrokerDetails.from_broker_url(broker_url)

    def test_missing_solidus_credentials_broker_url(self):
        """Tests instantiating broker from invalid URL missing double solidus delimiter."""
        broker_url = 'sqs:/us-east-1'
        with self.assertRaises(InvalidBrokerUrl):
            BrokerDetails.from_broker_url(broker_url)
