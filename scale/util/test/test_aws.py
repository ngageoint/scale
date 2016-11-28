from __future__ import unicode_literals

import datetime

import django
import django.utils.timezone as timezone
import mock
from django.test import TestCase

from util.aws import AWSClient
from util.exceptions import InvalidAWSCredentials


class TestAws(TestCase):

    def setUp(self):
        django.setup()

    def test_instantiate_credentials_from_config(self):
        """Tests instantiating AWS Credentials from a valid configuration."""
        config = { 'credentials': { 'access_key_id': 'ACCESSKEY', 'secret_access_key': 'SECRETKEY'}}
        credential = AWSClient.instantiate_credentials_from_config(config)
        self.assertEqual(credential.access_key_id, 'ACCESSKEY')
        self.assertEqual(credential.secret_access_key, 'SECRETKEY')

    def test_instantiate_credentials_from_config_missing_access_key(self):
        """Tests instantiating AWS Credentials from a configuration missing access key."""
        config = { 'credentials': { 'secret_access_key': 'SECRETKEY' }}
        with self.assertRaises(InvalidAWSCredentials):
            AWSClient.instantiate_credentials_from_config(config)

    def test_instantiate_credentials_from_config_missing_secret_key(self):
        """Tests instantiating AWS Credentials from a configuration missing secret key."""
        config = { 'credentials': { 'access_key_id': 'ACCESSKEY' }}
        with self.assertRaises(InvalidAWSCredentials):
            AWSClient.instantiate_credentials_from_config(config)

    def test_instantiate_credentials_from_config_empty_access_key(self):
        """Tests instantiating AWS Credentials from a configuration with an empty access key."""
        config = { 'credentials': { 'access_key_id': '', 'secret_access_key': 'SECRETKEY' }}
        self.assertIsNone(AWSClient.instantiate_credentials_from_config(config))

    def test_instantiate_credentials_from_config_empty_secret_key(self):
        """Tests instantiating AWS Credentials from a configuration with an empty secret key."""
        config = { 'credentials': { 'access_key_id': 'ACCESSKEY', 'secret_access_key': ' ' }}
        self.assertIsNone(AWSClient.instantiate_credentials_from_config(config))
