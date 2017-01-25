from __future__ import unicode_literals

import django
from botocore.exceptions import ParamValidationError
from django.test import TestCase

from util.aws import AWSClient, S3Client, AWSCredentials
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


class TestS3Client(TestCase):

    def setUp(self):
        self.credentials = AWSCredentials('fake', 'key')
        django.setup()

    def test_list_objects_prefix_no_objects(self):
        raise NotImplementedError

    def test_list_objects_prefix_with_objects(self):
        raise NotImplementedError

    def test_list_objects_prefix_recursive(self):
        raise NotImplementedError

    def test_list_objects_empty_bucket(self):
        raise NotImplementedError

    def test_list_objects_invalid_bucket_name(self):
        with self.assertRaises(ParamValidationError):
            with S3Client(self.credentials) as client:
                client.list_objects('invalid:bucket:name')

    def test_list_objects_bucket_not_found(self):
        raise NotImplementedError

    def test_list_objects_over_10k(self):
        raise NotImplementedError

    def test_list_objects_is_truncated_missing_token(self):
        raise NotImplementedError

    def test_list_objects_is_truncated_with_token(self):
        raise NotImplementedError

