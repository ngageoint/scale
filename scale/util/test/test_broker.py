from __future__ import unicode_literals

from copy import deepcopy
from datetime import datetime

import django
from botocore.exceptions import ParamValidationError, ClientError
from django.test import TestCase
from mock import patch

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
        self.assertEqual(broker.get_broker(), 'us-east-1')
        
    def test_valid_sqs_broker_url_no_credentials(self):
        """Tests instantiating broker from URL for SQS without keys."""
        broker_url = 'sqs://us-east-1//'
        broker = BrokerDetails.from_broker_url(broker_url)
        
        self.assertEqual(broker.get_type(), 'sqs')
        self.assertIsNone(broker.get_user_name())
        self.assertIsNone(broker.get_password())
        self.assertEqual(broker.get_broker(), 'us-east-1')

    def test_valid_rabbitmq_broker_url(self):
        """Tests instantiating broker from URL for RabbitMQ."""
        broker_url = 'amqp://guest:pass@localhost:5672//'
        broker = BrokerDetails.from_broker_url(broker_url)
        
        self.assertEqual(broker.get_type(), 'amqp')
        self.assertEqual(broker.get_user_name(), 'guest')
        self.assertEqual(broker.get_password(), 'pass')
        self.assertEqual(broker.get_broker(), 'localhost:5672')

    def test_bad_credentials_broker_url(self):
        """Tests instantiating broker from invalid URL with credential delimiter."""
        broker_url = 'sqs://@us-east-1//'
        with self.assertRaises(InvalidBrokerUrl):
            BrokerDetails.from_broker_url(broker_url)

    def test_missing_solidus_credentials_broker_url(self):
        """Tests instantiating broker from invalid URL missing double solidus delimiter."""
        broker_url = 'sqs:/us-east-1//'
        with self.assertRaises(InvalidBrokerUrl):
            BrokerDetails.from_broker_url(broker_url)
            
    def test_missing_terminators_credentials_broker_url(self):
        """Tests instantiating broker from invalid URL missing terminating double solidus."""
        broker_url = 'sqs://us-east-1'
        with self.assertRaises(InvalidBrokerUrl):
            BrokerDetails.from_broker_url(broker_url)

