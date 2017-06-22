"""Utility functions for testing AWS credentials and access to required resources"""
import logging
from collections import namedtuple

from boto3 import Session
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

from storage.brokers.broker import FileDetails
from util.exceptions import InvalidAWSCredentials, FileDoesNotExist

logger = logging.getLogger(__name__)

AWSCredentials = namedtuple('AWSCredentials', ['access_key_id', 'secret_access_key'])


class AWSClient(object):
    """Manages automatically creating and destroying clients to AWS services."""

    def __init__(self, resource, config, credentials=None, region_name=None):
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
        """

        self.credentials = credentials
        self.region_name = region_name
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

        self._client = self._session.client(self._resource_name, config=self._config)
        self._resource = self._session.resource(self._resource_name, config=self._config)
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

            return AWSCredentials(access_key, secret_key)


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

    def send_message(self, queue_name, message):
        """Send a message to SQS queue.

        :param queue_name: The unique name of the SQS queue
        :type queue_name: string
        :param message: Message to send to SQS queue
        :type message: string
        """

        queue = self.get_queue_by_name(queue_name)

        queue.send_message(MessageBody=message)

    def send_messages(self, queue_name, messages):
        """Send a batch of messages to SQS queue.

        :param queue_name: The unique name of the SQS queue
        :type queue_name: string
        :param messages: Messages to send to SQS queue
        :type messages: [`SendMessageBatchRequestEntry`]
        """

        queue = self.get_queue_by_name(queue_name)

        batches = [messages[i:i + 10] for i in xrange(0, len(messages), 10)]

        for batch in batches:
            queue.send_messages(Entries=batch)

    def receive_messages(self,
                         queue_name,
                         batch_size=100,
                         wait_time_seconds=20,
                         visibility_timeout_seconds=30):
        """Receive a batch of messages from an SQS queue

        :param queue_name:
        :param batch_size: Number of messages to retrieve in a single pass
        :type batch_size: int
        :param wait_time_seconds: Long-poll duration of request (max of 20). Ends immediately when message published.
        :type wait_time_seconds: int
        :param visibility_timeout_seconds: Duration for a message to be hidden after retrieved from the queue.
        :type visibility_timeout_seconds: int
        :return: Generator of messages
        :rtype: Generator[`boto3.sqs.Message`]
        """
        queue = self.get_queue_by_name(queue_name)

        # Set max_messages to lesser of 10 or batch_size
        max_messages = batch_size if batch_size < 10 else 10

        # Generate individual batch sizes up to given size, capped at 10
        count = 0
        while count < batch_size:
            for message in queue.receive_messages(MaxNumberOfMessages=max_messages,
                                                  WaitTimeSeconds=wait_time_seconds,
                                                  VisibilityTimeout=visibility_timeout_seconds):
                count += 1
                yield message

            # If count isn't evenly divisible by ten we're done
            if count % 10 != 0:
                break


class S3Client(AWSClient):
    def __init__(self, credentials=None, region_name=None):
        """Constructor

        :param credentials: Authentication values needed to access AWS. If no credentials are passed, then IAM
            role-based access is assumed.
        :type credentials: :class:`util.aws.AWSCredentials`
        :param region_name: The AWS region the resource resides in.
        :type region_name: string
        """
        config = Config(s3={'addressing_style': getattr(settings, 'S3_ADDRESSING_STYLE', 'auto')})
        AWSClient.__init__(self, 's3', config, credentials, region_name)

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

    def list_objects(self, bucket_name, recursive=False, prefix=None):
        """Generator function to retrieve list of objects within an S3 bucket

        Retrieval of objects is provided by the boto3 paginator over 
        list_objects. This allows for simple paging support with unbounded
        object counts. As a result of the time that may be required for the full
        result set to be returned, the results are returned via a generator. 
        This generator will contain objects of type `storage.brokers.broker.FileDetails`.
        
        :param bucket_name: The unique name of the bucket to retrieve.
        :type bucket_name: string
        :param recursive: Whether the bucket should be recursively searched from the given prefix
        :type recursive: bool
        :param prefix: The parent key from which to search bucket. Trailing slash is optional
        :type prefix: string
        :return: Generator of S3 objects that were found.
        :rtype: Generator[:class:`storage.brokers.broker.FileDetails`]
        """

        params = {'Bucket': bucket_name}
        if prefix:
            params['Prefix'] = prefix
        if not recursive:
            params['Delimiter'] = '/'

        paginator = self._client.get_paginator('list_objects')
        iterator = paginator.paginate(**params)

        for page in iterator:
            # In the event of 0 results, exit loop
            if 'Contents' not in page:
                break

            for result in page['Contents']:
                # Filter out 0 size keys, these are directory keys as S3 objects must be at least 1 Byte
                if result['Size'] > 0:
                    yield FileDetails(result['Key'], result['Size'])
