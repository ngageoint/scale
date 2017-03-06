from __future__ import unicode_literals

from copy import deepcopy
from datetime import datetime

import django
from botocore.exceptions import ParamValidationError, ClientError
from django.test import TestCase
from mock import patch

from util.aws import AWSClient, S3Client, AWSCredentials
from util.exceptions import InvalidAWSCredentials


class TestAws(TestCase):
    def setUp(self):
        django.setup()

    def test_instantiate_credentials_from_config(self):
        """Tests instantiating AWS Credentials from a valid configuration."""
        config = {'credentials': {'access_key_id': 'ACCESSKEY', 'secret_access_key': 'SECRETKEY'}}
        credential = AWSClient.instantiate_credentials_from_config(config)
        self.assertEqual(credential.access_key_id, 'ACCESSKEY')
        self.assertEqual(credential.secret_access_key, 'SECRETKEY')

    def test_instantiate_credentials_from_config_missing_access_key(self):
        """Tests instantiating AWS Credentials from a configuration missing access key."""
        config = {'credentials': {'secret_access_key': 'SECRETKEY'}}
        with self.assertRaises(InvalidAWSCredentials):
            AWSClient.instantiate_credentials_from_config(config)

    def test_instantiate_credentials_from_config_missing_secret_key(self):
        """Tests instantiating AWS Credentials from a configuration missing secret key."""
        config = {'credentials': {'access_key_id': 'ACCESSKEY'}}
        with self.assertRaises(InvalidAWSCredentials):
            AWSClient.instantiate_credentials_from_config(config)

    def test_instantiate_credentials_from_config_empty_access_key(self):
        """Tests instantiating AWS Credentials from a configuration with an empty access key."""
        config = {'credentials': {'access_key_id': '', 'secret_access_key': 'SECRETKEY'}}
        self.assertIsNone(AWSClient.instantiate_credentials_from_config(config))

    def test_instantiate_credentials_from_config_empty_secret_key(self):
        """Tests instantiating AWS Credentials from a configuration with an empty secret key."""
        config = {'credentials': {'access_key_id': 'ACCESSKEY', 'secret_access_key': ' '}}
        self.assertIsNone(AWSClient.instantiate_credentials_from_config(config))


class TestS3Client(TestCase):
    def setUp(self):
        self.credentials = AWSCredentials('ACCCESSKEY', 'SECRETKEY')

        self.sample_content = {
            'Key': 'test/string',
            'LastModified': datetime(2015, 1, 1),
            'ETag': 'string',
            'Size': 123,
            'StorageClass': 'STANDARD',
            'Owner': {
                'DisplayName': 'string',
                'ID': 'string'
            }
        }

        self.sample_response = {
            'IsTruncated': False,
            'Marker': 'string',
            'NextMarker': 'string',
            'Contents': [
                self.sample_content
            ],
            'Name': 'string',
            'Prefix': 'string',
            'Delimiter': 'string',
            'MaxKeys': 123,
            'CommonPrefixes': [
                {
                    'Prefix': 'string'
                },
            ],
            'EncodingType': 'url'
        }

        django.setup()

    @patch('botocore.paginate.PageIterator._make_request')
    def test_list_objects_prefix(self, mock_func):
        mock_func.return_value = self.sample_response

        with S3Client(self.credentials) as client:
            results = client.list_objects('sample-bucket', False, 'test/')

        self.assertEqual(len(list(results)), 1)

    @patch('botocore.paginate.PageIterator._make_request')
    def test_list_objects_prefix_recursive(self, mock_func):
        response = self.sample_response
        response['Contents'] = [deepcopy(self.sample_content), deepcopy(self.sample_content)]
        response['Contents'][0]['Key'] = 'string'
        mock_func.return_value = response

        with S3Client(self.credentials) as client:
            results = client.list_objects('sample-bucket', True)

        self.assertEqual(len(list(results)), 2)

    @patch('botocore.paginate.PageIterator._make_request')
    def test_list_objects_empty_bucket(self, mock_func):
        response = self.sample_response
        del response['Contents']
        mock_func.return_value = response

        with S3Client(self.credentials) as client:
            results = client.list_objects('empty-bucket', True)

        self.assertEqual(len(list(results)), 0)

    def test_list_objects_invalid_bucket_name(self):
        with self.assertRaises(ParamValidationError):
            with S3Client(self.credentials) as client:
                items = list(client.list_objects('invalid:bucket:name'))
                

    @patch('botocore.paginate.Paginator.paginate')
    def test_list_objects_bucket_not_found(self, mock_func):
        error_response = {'Error': {'Code': 'NoSuchBucket', 'Message': 'The specified bucket does not exist'}}
        mock_func.side_effect = ClientError(error_response, 'ListObjects')

        with self.assertRaises(ClientError):
            with S3Client(self.credentials) as client:
                items = list(client.list_objects('nonexistent-bucket'))

    @patch('botocore.paginate.PageIterator._make_request')
    def test_list_objects_iteration(self, mock_func):
        response1 = self.sample_response
        response1['IsTruncated'] = True
        response2 = deepcopy(response1)
        response2['IsTruncated'] = False
        mock_func.side_effect = [response1, response2]

        with S3Client(self.credentials) as client:
            results = client.list_objects('iterating-bucket', True)

        self.assertEqual(len(list(results)), 2)
