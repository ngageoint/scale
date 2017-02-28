"""Utility functions for testing AWS credentials and access to required resources"""
import logging
from collections import namedtuple

from boto3 import Session
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

from util.exceptions import InvalidAWSCredentials, FileDoesNotExist

logger = logging.getLogger(__name__)

AWSCredentials = namedtuple('AWSCredentials', ['access_key_id', 'secret_access_key', 'endpoint_url'])


class AWSClient(object):
    """Manages automatically creating and destroying clients to AWS services."""

    def __init__(self, resource, config, credentials=None, region_name=None, endpoint_url=None):
        """Constructor

        :param resource: AWS specific token for resource type. e.g., 's3', 'sqs', etc.
        :type resource: string
        :param config: Resource specific configuration
        :type config: :class:`botocore.client.Config`
        :param credentials: Authentication values needed to access AWS. If no credentials are passed, then IAM
            role-based access is assumed.
        :type credentials: :class:`util.aws.AWSCredentials`
        :param region_name: The AWS region the resource resides in.
        :type region_name: string
        :param endpoint_url: The AWS endpoint URL the resource resides in.
        :type endpoint_url: string
        """

        self.credentials = credentials
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self._client = None
        self._resource_name = resource
        self._config = config

    def __enter__(self):
        """Callback handles creating a new client for AWS access."""

        logger.debug('Setting up AWS client...')

        session_args = {}
        if self.credentials:
            session_args['aws_access_key_id'] = self.credentials.access_key_id
            session_args['aws_secret_access_key'] = self.credentials.secret_access_key
        if self.region_name:
            session_args['region_name'] = self.region_name
        self._session = Session(**session_args)

        self._client = self._session.client(self._resource_name, config=self._config, endpoint_url=self.endpoint_url)
        self._resource = self._session.resource(self._resource_name, config=self._config, endpoint_url=self.endpoint_url)
        return self

    def __exit__(self, type, value, traceback):
        """Callback handles destroying an existing client."""
        pass

    @staticmethod
    def instantiate_credentials_from_config(config):
        """Extract credential keys from configuration and return instantiated credential object

        If values provided in the `access_key_id` or `secret_access_key` keys of `credentials` configuration object are
        empty, None will be returned. In this case, role-based authentication should be attempted.

        :param config: Resource specific configuration
        :type config: :class:`botocore.client.Config`
        :return: instantiated credential object or None if keys provided were empty
        :rtype: :class:`util.aws.AWSCredentials`

        :raises :class:`util.exceptions.InvalidAWSCredentials`: If the credentials provided are incomplete.
        """
        if 'credentials' in config and config['credentials']:
            credentials_dict = config['credentials']
            if 'access_key_id' not in credentials_dict:
                raise InvalidAWSCredentials('"credentials" requires "access_key_id" to be populated')
            if 'secret_access_key' not in credentials_dict:
                raise InvalidAWSCredentials('"credentials" requires "secret_access_key" to be populated')

            access_key = credentials_dict['access_key_id'].strip()
            secret_key = credentials_dict['secret_access_key'].strip()

            # If either Access Key or Secret Access Key are empty, fail-over to role-based auth.
            # TODO: This should be changed to also raise as above, once the UI has been improved to prune unset values.
            if not len(access_key) or not len(secret_key):
                return None

            endpoint_url = config.get('endpoint_url', '').strip()
            endpoint_url = None if len(endpoint_url) == 0 else endpoint_url

            return AWSCredentials(access_key, secret_key, endpoint_url)


class SQSClient(AWSClient):
    def __init__(self, credentials=None, region_name=None):
        """Constructor

        :param credentials: Authentication values needed to access AWS. If no credentials are passed, then IAM
            role-based access is assumed.
        :type credentials: :class:`util.aws.AWSCredentials`
        :param region_name: The AWS region the resource resides in.
        :type region_name: string
        """
        AWSClient.__init__(self, 'sqs', None, credentials, region_name)

    def get_queue_by_name(self, queue_name):
        """Gets a SQS queue by the given name

        :param queue_name: The unique name of the SQS queue
        :type queue_name: string
        :return: Queue resource to perform queue operations
        :rtype: :class:`boto3.sqs.Queue`
        """

        return self._resource.get_queue_by_name(QueueName=queue_name)


class S3Client(AWSClient):
    def __init__(self, credentials=None, region_name=None, endpoint_url=None):
        """Constructor

        :param credentials: Authentication values needed to access AWS. If no credentials are passed, then IAM
            role-based access is assumed.
        :type credentials: :class:`util.aws.AWSCredentials`
        :param region_name: The AWS region the resource resides in.
        :type region_name: string
        :param endpoint_url: The AWS endpoibt URL the resource resides in.
        :type endpoint_url: string
        """
        config = Config(s3={'addressing_style': getattr(settings, 'S3_ADDRESSING_STYLE', 'auto')})
        AWSClient.__init__(self, 's3', config, credentials, region_name, endpoint_url)

    def get_bucket(self, bucket_name, validate=True):
        """Gets a reference to an S3 bucket with the given identifier.

        :param bucket_name: The unique name of the bucket to retrieve.
        :type bucket_name: string
        :param validate: Whether to perform a request that verifies the bucket actually exists.
        :type validate: bool
        :returns: The bucket object for the given name.
        :rtype: :class:`boto3.s3.Bucket`

        :raises :class:`botocore.exceptions.ClientError`: If the bucket fails to validate.
        """

        logger.debug('Accessing S3 bucket: %s', bucket_name)
        if validate:
            self._client.head_bucket(Bucket=bucket_name)
        return self._resource.Bucket(bucket_name)

    def get_object(self, bucket_name, key_name, validate=True):
        """Gets a reference to an S3 object with the given identifier.

        :param bucket_name: The unique name of the bucket to retrieve.
        :type bucket_name: string
        :param key_name: The unique name of the object to retrieve that is associated with a file.
        :type key_name: string
        :param validate: Whether to perform a request that verifies the object actually exists.
        :type validate: bool
        :returns: The S3 object for the given name.
        :rtype: :class:`boto3.s3.Object`

        :raises :class:`botocore.exceptions.ClientError`: If the request is invalid.
        :raises :class:`storage.exceptions.FileDoesNotExist`: If the file is not found in the bucket.
        """
        s3_object = self._resource.Object(bucket_name, key_name)

        try:
            if validate:
                s3_object.get()
        except ClientError as err:
            error_code = err.response['ResponseMetadata']['HTTPStatusCode']
            if error_code == 404:
                raise FileDoesNotExist('Unable to access remote file: %s %s' % (bucket_name, key_name))
            raise
        return s3_object





