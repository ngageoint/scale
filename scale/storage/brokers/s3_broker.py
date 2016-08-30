"""Defines an S3 broker that utilizes the Amazon Web Services Simple Storage Service (S3) as its storage system"""
from __future__ import unicode_literals

import logging
import os
import ssl
import time
from collections import namedtuple

from boto3.session import Session
from botocore.client import Config
from botocore.exceptions import ClientError

import storage.settings as settings
from storage.brokers.broker import Broker, BrokerVolume
from storage.brokers.exceptions import InvalidBrokerConfiguration
from storage.configuration.workspace_configuration import ValidationWarning
from storage.exceptions import FileDoesNotExist
from util.command import execute_command_line

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

        with S3Client(self._credentials) as client:
            for scale_file in files:
                s3_object = client.get_object(self._bucket_name, scale_file.file_path)

                self._delete_file(s3_object, scale_file)

                # Update model attributes
                scale_file.set_deleted()
                scale_file.save()

    def download_files(self, volume_path, file_downloads):
        """See :meth:`storage.brokers.broker.Broker.download_files`"""

        with S3Client(self._credentials) as client:
            for file_download in file_downloads:
                # If file supports partial mount and volume is configured attempt sym-link
                if file_download.partial and self._volume:
                    logger.debug('Partial S3 file accessed by mounted bucket.')
                    path_to_download = os.path.join(volume_path, file_download.file.file_path)

                    # Create symlink to the file in the host mount
                    logger.info('Creating link %s -> %s', file_download.local_path, path_to_download)
                    execute_command_line(['ln', '-s', path_to_download, file_download.local_path])
                # Fall-back to default S3 file download
                else:
                    s3_object = client.get_object(self._bucket_name, file_download.file.file_path)

                    self._download_file(s3_object, file_download.file, file_download.local_path)



    def load_configuration(self, config):
        """See :meth:`storage.brokers.broker.Broker.load_configuration`"""

        self._bucket_name = config['bucket_name']

        # TODO Change credentials to use an encrypted store key reference
        if 'credentials' in config:
            credentials_dict = config['credentials']
            self._credentials = S3Credentials(credentials_dict['access_key_id'], credentials_dict['secret_access_key'])

        if 'host_path' in config:
            volume = BrokerVolume(None, config['host_path'])
            volume.host = True
            self._volume = volume

    def move_files(self, volume_path, file_moves):
        """See :meth:`storage.brokers.broker.Broker.move_files`"""

        with S3Client(self._credentials) as client:
            for file_move in file_moves:
                s3_object_src = client.get_object(self._bucket_name, file_move.file.file_path)
                s3_object_dest = client.get_object(self._bucket_name, file_move.new_path, False)

                self._move_file(s3_object_src, s3_object_dest, file_move.file, file_move.new_path)

                # Update model attributes
                file_move.file.file_path = file_move.new_path
                file_move.file.save()

    def upload_files(self, volume_path, file_uploads):
        """See :meth:`storage.brokers.broker.Broker.upload_files`"""

        with S3Client(self._credentials) as client:
            for file_upload in file_uploads:
                s3_object = client.get_object(self._bucket_name, file_upload.file.file_path, False)

                self._upload_file(s3_object, file_upload.file, file_upload.local_path)

                # Create new model
                file_upload.file.save()

    def validate_configuration(self, config):
        """See :meth:`storage.brokers.broker.Broker.validate_configuration`"""

        warnings = []
        if 'bucket_name' not in config or not config['bucket_name']:
            raise InvalidBrokerConfiguration('S3 broker requires "bucket_name" to be populated')

        credentials = None
        if 'credentials' in config and config['credentials']:
            credentials_dict = config['credentials']
            if 'access_key_id' not in credentials_dict or not credentials_dict['access_key_id']:
                raise InvalidBrokerConfiguration('S3 broker requires "access_key_id" to be populated')
            if 'secret_access_key' not in credentials_dict or not credentials_dict['secret_access_key']:
                raise InvalidBrokerConfiguration('S3 broker requires "secret_access_key" to be populated')
            credentials = S3Credentials(credentials_dict['access_key_id'], credentials_dict['secret_access_key'])

        if 'host_path' in config:
            # TODO: Can we do some validation here to ensure path is valid?
            pass

        # Check whether the bucket can actually be accessed
        with S3Client(credentials) as client:
            try:
                client.get_bucket(config['bucket_name'])
            except ClientError:
                warnings.append(ValidationWarning('bucket_access',
                                                  'Unable to access bucket. Check the bucket name and credentials.'))

        return warnings

    def _delete_file(self, s3_object, scale_file, retries=settings.S3_RETRY_COUNT):
        """Deletes a file from the S3 file system.

        This method will attempt to retry the delete if :class:`ssl.SSLError` is raised up to a number of retries given.

        :param s3_object: The S3 object representing the file to delete.
        :type s3_object: :class:`boto3.s3.Object`
        :param scale_file: The model associated with the file to delete.
        :type scale_file: :class:`storage.models.ScaleFile`
        """

        logger.info('Deleting %s', scale_file.file_path)
        for attempt in range(retries):
            try:
                s3_object.delete()
                return
            except ssl.SSLError:
                if attempt >= retries:
                    raise
                time.sleep(settings.S3_RETRY_DELAY * attempt)
                logger.exception('Retrying S3 delete attempt: %i', attempt + 1)

    def _download_file(self, s3_object, scale_file, path, retries=settings.S3_RETRY_COUNT):
        """Downloads a file in S3 storage to the local file system.

        This method will attempt to retry the delete if :class:`ssl.SSLError` is raised up to a number of retries given.

        :param s3_object: The S3 object representing the file to download.
        :type s3_object: :class:`boto3.s3.Object`
        :param scale_file: The model associated with the file to download.
        :type scale_file: :class:`storage.models.ScaleFile`
        :param path: The destination path for the file download.
        :type path: string
        """

        logger.info('Downloading %s -> %s', scale_file.file_path, path)
        for attempt in range(retries):
            try:
                s3_object.download_file(path)
                return
            except ssl.SSLError:
                if attempt >= retries:
                    raise
                time.sleep(settings.S3_RETRY_DELAY * attempt)
                logger.exception('Retrying S3 download attempt: %i', attempt + 1)

    def _move_file(self, s3_object_src, s3_object_dest, scale_file, path, retries=settings.S3_RETRY_COUNT):
        """Moves a file within the S3 file system.

        Note that S3 does not support an atomic move, so this operation is implemented as a copy and delete.

        This method will attempt to retry the move if :class:`ssl.SSLError` is raised up to a number of retries given.
        Note that since S3 does not support an atomic move, this method copies the file to the new destination and then
        attempts to delete the original file content.

        :param s3_object_src: The S3 object representing the source of the file to move.
        :type s3_object_src: :class:`boto3.s3.Object`
        :param s3_object_dest: The S3 object representing the destination of the file to move.
        :type s3_object_dest: :class:`boto3.s3.Object`
        :param scale_file: The model associated with the file to move.
        :type scale_file: :class:`storage.models.ScaleFile`
        :param path: The destination path for the file move.
        :type path: string
        """

        logger.info('Copying %s -> %s', scale_file.file_path, path)
        options = dict()
        options['CopySource'] = {
            'Bucket': s3_object_src.bucket_name,
            'Key': s3_object_src.key,
        }
        options['StorageClass'] = settings.S3_STORAGE_CLASS
        if settings.S3_SERVER_SIDE_ENCRYPTION:
            options['ServerSideEncryption'] = settings.S3_SERVER_SIDE_ENCRYPTION
        if scale_file.media_type:
            options['ContentType'] = scale_file.media_type

        for attempt in range(retries):
            try:
                s3_object_dest.copy_from(**options)
                break
            except ssl.SSLError:
                if attempt >= retries:
                    raise
                time.sleep(settings.S3_RETRY_DELAY * attempt)
                logger.exception('Retrying S3 copy attempt: %i', attempt + 1)

        self._delete_file(s3_object_src, scale_file)

    def _upload_file(self, s3_object, scale_file, path, retries=settings.S3_RETRY_COUNT):
        """Uploads a file in local storage to the S3 remote file system.

        This method will attempt to retry the delete if :class:`ssl.SSLError` is raised up to a number of retries given.

        :param s3_object: The S3 object representing the file to upload.
        :type s3_object: :class:`boto3.s3.Object`
        :param scale_file: The model associated with the file to upload.
        :type scale_file: :class:`storage.models.ScaleFile`
        :param path: The source path for the file upload.
        :type path: string
        """

        options = dict()
        options['StorageClass'] = settings.S3_STORAGE_CLASS
        if settings.S3_SERVER_SIDE_ENCRYPTION:
            options['ServerSideEncryption'] = settings.S3_SERVER_SIDE_ENCRYPTION
        if scale_file.media_type:
            options['ContentType'] = scale_file.media_type

        logger.info('Uploading %s -> %s', path, scale_file.file_path)
        for attempt in range(retries):
            try:
                s3_object.upload_file(path, options)
                return
            except ssl.SSLError:
                if attempt >= retries:
                    raise
                time.sleep(settings.S3_RETRY_DELAY * attempt)
                logger.exception('Retrying S3 upload attempt: %i', attempt + 1)


class S3Client(object):
    """Manages automatically creating and destroying clients to the S3 service."""

    def __init__(self, credentials=None):
        """Constructor

        :param credentials: Authentication values needed to access S3 storage. If no credentials are passed, then IAM
            role-based access is assumed.
        :type credentials: :class:`storage.brokers.s3_broker.S3Credentials`
        """

        self.credentials = credentials
        self._client = None

    def __enter__(self):
        """Callback handles creating a new client for S3 access."""

        logger.debug('Setting up S3 client...')
        session_args = {
            'region_name': settings.S3_REGION,
        }
        if self.credentials:
            session_args['aws_access_key_id'] = self.credentials.access_key_id
            session_args['aws_secret_access_key'] = self.credentials.secret_access_key
        self._session = Session(**session_args)

        s3_args = {
            'addressing_style': settings.S3_ADDRESSING_STYLE,
        }
        self._client = self._session.client('s3', config=Config(s3=s3_args))
        self._resource = self._session.resource('s3', config=Config(s3=s3_args))
        return self

    def __exit__(self, type, value, traceback):
        """Callback handles destroying an existing client to S3."""
        pass

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
