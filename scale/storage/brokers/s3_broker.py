"""Defines an S3 broker that utilizes the Amazon Web Services Simple Storage Service (S3) as its storage system"""
from __future__ import unicode_literals

import logging
import ssl
import time
from collections import namedtuple

import boto
import django.utils.timezone as timezone
from boto.exception import S3ResponseError
from boto.s3.connection import S3Connection
from boto.s3.key import Key

import storage.settings as settings
from storage.brokers.broker import Broker
from storage.brokers.exceptions import InvalidBrokerConfiguration
from storage.configuration.workspace_configuration import ValidationWarning
from storage.exceptions import FileDoesNotExist

logger = logging.getLogger(__name__)

S3Credentials = namedtuple('S3Credentials', ['access_key_id', 'secret_access_key'])


class S3Broker(Broker):
    """Broker that utilizes the AWS Boto library to read/write files to S3 cloud storage."""

    def __init__(self):
        """Constructor"""

        super(S3Broker, self).__init__('s3')

        self._credentials = None
        self._bucket_name = None

    def delete_files(self, volume_path, files):
        """See :meth:`storage.brokers.broker.Broker.delete_files`"""

        with BrokerConnection(self._credentials) as conn:
            for scale_file in files:
                s3_key = conn.get_key(self._bucket_name, scale_file.file_path)

                self._delete_file(s3_key, scale_file)

                scale_file.is_deleted = True
                scale_file.deleted = timezone.now()

    def download_files(self, volume_path, file_downloads):
        """See :meth:`storage.brokers.broker.Broker.download_files`"""

        with BrokerConnection(self._credentials) as conn:
            for file_download in file_downloads:
                s3_key = conn.get_key(self._bucket_name, file_download.file.file_path)

                self._download_file(s3_key, file_download.file, file_download.local_path)

    def load_configuration(self, config):
        """See :meth:`storage.brokers.broker.Broker.load_configuration`"""

        self._bucket_name = config['bucket_name']

        # TODO Change credentials to use an encrypted store key reference
        credentials_dict = config['credentials']
        self._credentials = S3Credentials(credentials_dict['access_key_id'], credentials_dict['secret_access_key'])

    def move_files(self, volume_path, file_moves):
        """See :meth:`storage.brokers.broker.Broker.move_files`"""

        with BrokerConnection(self._credentials) as conn:
            for file_move in file_moves:
                s3_key = conn.get_key(self._bucket_name, file_move.file.file_path)

                self._move_file(s3_key, file_move.file, file_move.new_path)

                file_move.file.file_path = file_move.new_path

    def upload_files(self, volume_path, file_uploads):
        """See :meth:`storage.brokers.broker.Broker.upload_files`"""

        with BrokerConnection(self._credentials) as conn:
            for file_upload in file_uploads:
                bucket = conn.get_bucket(self._bucket_name)

                s3_key = Key(bucket)
                s3_key.key = file_upload.file.file_path
                s3_key.storage_class = settings.S3_STORAGE_CLASS
                s3_key.encrypted = settings.S3_ENCRYPTED

                self._upload_file(s3_key, file_upload.file, file_upload.local_path)

    def validate_configuration(self, config):
        """See :meth:`storage.brokers.broker.Broker.validate_configuration`"""

        warnings = []
        if 'bucket_name' not in config or not config['bucket_name']:
            raise InvalidBrokerConfiguration('S3 broker requires "bucket_name" to be populated')

        if 'credentials' not in config or not config['credentials']:
            raise InvalidBrokerConfiguration('S3 broker requires "credentials" to be populated')

        credentials_dict = config['credentials']
        if 'access_key_id' not in credentials_dict or not credentials_dict['access_key_id']:
            raise InvalidBrokerConfiguration('S3 broker requires "access_key_id" to be populated')
        if 'secret_access_key' not in credentials_dict or not credentials_dict['secret_access_key']:
            raise InvalidBrokerConfiguration('S3 broker requires "secret_access_key" to be populated')

        # Check whether the bucket can actually be accessed
        credentials = S3Credentials(credentials_dict['access_key_id'], credentials_dict['secret_access_key'])
        with BrokerConnection(credentials) as conn:
            try:
                conn.get_bucket(config['bucket_name'], True)
            except S3ResponseError:
                warnings.append(ValidationWarning('bucket_access',
                                                  'Unable to access bucket. Check the bucket name and credentials.'))

        return warnings

    def _delete_file(self, s3_key, scale_file, retries=settings.S3_RETRY_COUNT):
        """Deletes a file from the S3 file system.

        This method will attempt to retry the delete if :class:`ssl.SSLError` is raised up to a number of retries given.

        :param s3_key: The S3 key representing the file to delete.
        :type s3_key: :class:`boto.s3.key.Key`
        :param scale_file: The model associated with the file to delete.
        :type scale_file: :class:`storage.models.ScaleFile`
        """

        logger.info('Deleting %s', scale_file.file_path)
        for attempt in range(retries):
            try:
                s3_key.delete()
                return
            except ssl.SSLError:
                if attempt >= retries:
                    raise
                time.sleep(settings.S3_RETRY_DELAY * attempt)
                logger.exception('Retrying S3 delete attempt: %i', attempt + 1)

    def _download_file(self, s3_key, scale_file, path, retries=settings.S3_RETRY_COUNT):
        """Downloads a file in S3 storage to the local file system.

        This method will attempt to retry the delete if :class:`ssl.SSLError` is raised up to a number of retries given.

        :param s3_key: The S3 key representing the file to download.
        :type s3_key: :class:`boto.s3.key.Key`
        :param scale_file: The model associated with the file to download.
        :type scale_file: :class:`storage.models.ScaleFile`
        :param path: The destination path for the file download.
        :type path: string
        """

        logger.info('Downloading %s -> %s', scale_file.file_path, path)
        for attempt in range(retries):
            try:
                with open(path, 'wb') as fp:
                    s3_key.get_contents_to_file(fp)
                    return
            except ssl.SSLError:
                if attempt >= retries:
                    raise
                time.sleep(settings.S3_RETRY_DELAY * attempt)
                logger.exception('Retrying S3 download attempt: %i', attempt + 1)

    def _move_file(self, s3_key, scale_file, path, retries=settings.S3_RETRY_COUNT):
        """Moves a file within the S3 file system.

        Note that S3 does not support an atomic move, so this operation is implemented as a copy and delete.

        This method will attempt to retry the move if :class:`ssl.SSLError` is raised up to a number of retries given.
        Note that since S3 does not support an atomic move, this method copies the file to the new destination and then
        attempts to delete the original file content.

        :param s3_key: The S3 key representing the file to move.
        :type s3_key: :class:`boto.s3.key.Key`
        :param scale_file: The model associated with the file to move.
        :type scale_file: :class:`storage.models.ScaleFile`
        :param path: The destination path for the file move.
        :type path: string
        """

        logger.info('Copying %s -> %s', scale_file.file_path, path)
        for attempt in range(retries):
            try:
                s3_key.copy(self._bucket_name, path,
                            reduced_redundancy=(settings.S3_STORAGE_CLASS == 'REDUCED_REDUNDANCY'),
                            encrypt_key=settings.S3_ENCRYPTED, preserve_acl=True, validate_dst_bucket=False)
                break
            except ssl.SSLError:
                if attempt >= retries:
                    raise
                time.sleep(settings.S3_RETRY_DELAY * attempt)
                logger.exception('Retrying S3 copy attempt: %i', attempt + 1)

        self._delete_file(s3_key, scale_file)

    def _upload_file(self, s3_key, scale_file, path, retries=settings.S3_RETRY_COUNT):
        """Uploads a file in local storage to the S3 remote file system.

        This method will attempt to retry the delete if :class:`ssl.SSLError` is raised up to a number of retries given.

        :param s3_key: The S3 key representing the file to upload.
        :type s3_key: :class:`boto.s3.key.Key`
        :param scale_file: The model associated with the file to upload.
        :type scale_file: :class:`storage.models.ScaleFile`
        :param path: The source path for the file upload.
        :type path: string
        """

        # Determine the proper mime-type for the file
        headers = dict()
        if scale_file.media_type:
            headers['Content-Type'] = scale_file.media_type

        logger.info('Uploading %s -> %s', path, scale_file.file_path)
        for attempt in range(retries):
            try:
                with open(path, 'rb') as fp:
                    s3_key.set_contents_from_file(fp, headers)
                    return
            except ssl.SSLError:
                if attempt >= retries:
                    raise
                time.sleep(settings.S3_RETRY_DELAY * attempt)
                logger.exception('Retrying S3 upload attempt: %i', attempt + 1)


class BrokerConnection(object):
    """Manages automatically opening and closing connections to the S3 service."""

    def __init__(self, credentials):
        """Constructor

        :param credentials: Authentication values needed to access S3 storage.
        :type credentials: :class:`storage.brokers.s3_broker.S3Credentials`
        """

        self.credentials = credentials
        self._connection = None

        # Check whether to use a local mock S3 or the real services
        if settings.S3_CALLING_FORMAT:
            self._calling_format = settings.S3_CALLING_FORMAT
        else:
            self._calling_format = boto.config.get(
                's3', 'calling_format',
                'boto.s3.connection.OrdinaryCallingFormat'
            )

    def __enter__(self):
        """Callback handles opening a new connection to S3."""

        host = settings.S3_HOST or S3Connection.DefaultHost
        logger.debug('Connecting to S3 host: %s', host)
        self._connection = boto.connect_s3(
            self.credentials.access_key_id, self.credentials.secret_access_key,
            calling_format=self._calling_format, is_secure=settings.S3_SECURE,
            host=host, port=settings.S3_PORT,
        )
        return self

    def __exit__(self, type, value, traceback):
        """Callback handles closing an existing connection to S3."""

        if self._connection:
            self._connection.close()

    def get_bucket(self, bucket_name, validate=False):
        """Gets a reference to an S3 bucket with the given identifier.

        :param bucket_name: The unique name of the bucket to retrieve.
        :type bucket_name: string
        :param validate: Whether to perform a request that verifies the bucket actually exists.
        :type validate: bool
        :returns: The bucket object for the given name.
        :rtype: :class:`boto.s3.bucket.Bucket`

        :raises :class:`boto.exceptions.S3ResponseError`: If the bucket fails to validate.
        """

        logger.debug('Accessing S3 bucket: %s', bucket_name)
        return self._connection.get_bucket(bucket_name, validate=validate)

    def get_key(self, bucket_name, key_name):
        """Gets a reference to an S3 key with the given identifier.

        :param bucket_name: The unique name of the bucket to retrieve.
        :type bucket_name: string
        :param key_name: The unique name of the key to retrieve that is associated with a file.
        :type key_name: string
        :returns: The key object for the given name.
        :rtype: :class:`boto.s3.key.Key`

        :raises :class:`boto.exceptions.S3ResponseError`: If the bucket fails to validate.
        :raises :class:`storage.exceptions.FileDoesNotExist`: If the file is not found in the bucket.
        """

        bucket = self.get_bucket(bucket_name)

        s3_key = bucket.get_key(key_name)
        if not s3_key:
            raise FileDoesNotExist('Unable to access remote file: %s %s' % (bucket_name, key_name))
        return s3_key
