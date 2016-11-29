from __future__ import unicode_literals

import os

import django
from django.test import TestCase
from mock import MagicMock, Mock, call, mock_open, patch

import storage.test.utils as storage_test_utils
from storage.brokers.broker import FileDownload, FileMove, FileUpload
from storage.brokers.exceptions import InvalidBrokerConfiguration
from storage.brokers.s3_broker import S3Broker
from util.aws import S3Client


class TestS3Broker(TestCase):

    def setUp(self):
        django.setup()

        self.broker = S3Broker()
        self.broker.load_configuration({
            'type': S3Broker().broker_type,
            'bucket_name': 'my_bucket.domain.com',
            'host_path': '/my_bucket_mounted',
            'credentials': {
                'access_key_id': 'ABC',
                'secret_access_key': '123',
            },
        })

    @patch('storage.brokers.s3_broker.S3Client')
    def test_delete_files(self, mock_client_class):
        """Tests deleting files successfully"""

        s3_object_1 = MagicMock()
        s3_object_2 = MagicMock()
        mock_client = MagicMock(S3Client)
        mock_client.get_object.side_effect = [s3_object_1, s3_object_2]
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)

        file_path_1 = os.path.join('my_dir', 'my_file.txt')
        file_path_2 = os.path.join('my_dir', 'my_file.json')

        file_1 = storage_test_utils.create_file(file_path=file_path_1)
        file_2 = storage_test_utils.create_file(file_path=file_path_2)

        # Call method to test
        self.broker.delete_files(None, [file_1, file_2])

        # Check results
        self.assertTrue(s3_object_1.delete.called)
        self.assertTrue(s3_object_2.delete.called)
        self.assertTrue(file_1.is_deleted)
        self.assertIsNotNone(file_1.deleted)
        self.assertTrue(file_2.is_deleted)
        self.assertIsNotNone(file_2.deleted)

    @patch('storage.brokers.s3_broker.S3Client')
    def test_download_files(self, mock_client_class):
        """Tests downloading files successfully"""

        s3_object_1 = MagicMock()
        s3_object_2 = MagicMock()
        mock_client = MagicMock(S3Client)
        mock_client.get_object.side_effect = [s3_object_1, s3_object_2]
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)

        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_name_1)
        local_path_file_2 = os.path.join('my_dir_2', file_name_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_name_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_name_2)

        file_1 = storage_test_utils.create_file(file_path=workspace_path_file_1)
        file_2 = storage_test_utils.create_file(file_path=workspace_path_file_2)
        file_1_dl = FileDownload(file_1, local_path_file_1, False)
        file_2_dl = FileDownload(file_2, local_path_file_2, False)

        # Call method to test
        mo = mock_open()
        with patch('__builtin__.open', mo, create=True):
            self.broker.download_files(None, [file_1_dl, file_2_dl])

        # Check results
        self.assertTrue(s3_object_1.download_file.called)
        self.assertTrue(s3_object_2.download_file.called)

    # Patching in storage.brokers.s3_broker as opposed to util.aws / util.command because patch must be applied where
    # import is made, not on source
    @patch('storage.brokers.s3_broker.S3Client')
    @patch('storage.brokers.s3_broker.execute_command_line')
    def test_host_link_files(self, mock_execute, mock_client_class):
        """Tests sym-linking files successfully"""

        volume_path = os.path.join('the', 'volume', 'path')
        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_name_1)
        local_path_file_2 = os.path.join('my_dir_2', file_name_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_name_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_name_2)
        full_workspace_path_file_1 = os.path.join(volume_path, workspace_path_file_1)
        full_workspace_path_file_2 = os.path.join(volume_path, workspace_path_file_2)
        file_1 = storage_test_utils.create_file(file_path=workspace_path_file_1)
        file_2 = storage_test_utils.create_file(file_path=workspace_path_file_2)

        file_1_dl = FileDownload(file_1, local_path_file_1, True)
        file_2_dl = FileDownload(file_2, local_path_file_2, True)

        # Call method to test
        self.broker.download_files(volume_path, [file_1_dl, file_2_dl])

        # Check results
        two_calls = [call(['ln', '-s', full_workspace_path_file_1, local_path_file_1]),
                     call(['ln', '-s', full_workspace_path_file_2, local_path_file_2])]
        mock_execute.assert_has_calls(two_calls)

    def test_load_configuration(self):
        """Tests loading a valid configuration successfully"""

        json_config = {
            'type': S3Broker().broker_type,
            'bucket_name': 'my_bucket.domain.com',
            'host_path': '/my_bucket_mounted',
            'credentials': {
                'access_key_id': 'ABC',
                'secret_access_key': '123',
            },
        }
        broker = S3Broker()
        broker.load_configuration(json_config)

        self.assertEqual(broker._bucket_name, 'my_bucket.domain.com')
        self.assertEqual(broker._volume.remote_path, '/my_bucket_mounted')
        self.assertEqual(broker._credentials.access_key_id, 'ABC')
        self.assertEqual(broker._credentials.secret_access_key, '123')

    def test_load_configuration_whitespace_filled_host_path(self):
        """Tests loading a valid configuration successfully while purging empty host_path value"""

        json_config = {
            'type': S3Broker().broker_type,
            'bucket_name': 'my_bucket.domain.com',
            'host_path': '  ',
            'credentials': {
                'access_key_id': 'ABC',
                'secret_access_key': '123',
            },
        }
        broker = S3Broker()
        broker.load_configuration(json_config)

        self.assertEqual(broker._bucket_name, 'my_bucket.domain.com')
        self.assertIsNone(broker._volume)
        self.assertEqual(broker._credentials.access_key_id, 'ABC')
        self.assertEqual(broker._credentials.secret_access_key, '123')

    @patch('storage.brokers.s3_broker.S3Client')
    def test_move_files(self, mock_client_class):
        """Tests moving files successfully"""

        s3_object_1a = MagicMock()
        s3_object_1b = MagicMock()
        s3_object_2a = MagicMock()
        s3_object_2b = MagicMock()
        mock_client = MagicMock(S3Client)
        mock_client.get_object.side_effect = [s3_object_1a, s3_object_1b, s3_object_2a, s3_object_2b]
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)

        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        old_workspace_path_1 = os.path.join('my_dir_1', file_name_1)
        old_workspace_path_2 = os.path.join('my_dir_2', file_name_2)
        new_workspace_path_1 = os.path.join('my_new_dir_1', file_name_1)
        new_workspace_path_2 = os.path.join('my_new_dir_2', file_name_2)

        file_1 = storage_test_utils.create_file(file_path=old_workspace_path_1)
        file_2 = storage_test_utils.create_file(file_path=old_workspace_path_2)
        file_1_mv = FileMove(file_1, new_workspace_path_1)
        file_2_mv = FileMove(file_2, new_workspace_path_2)

        # Call method to test
        self.broker.move_files(None, [file_1_mv, file_2_mv])

        # Check results
        self.assertTrue(s3_object_1b.copy_from.called)
        self.assertTrue(s3_object_1a.delete.called)
        self.assertTrue(s3_object_2b.copy_from.called)
        self.assertTrue(s3_object_2a.delete.called)
        self.assertEqual(file_1.file_path, new_workspace_path_1)
        self.assertEqual(file_2.file_path, new_workspace_path_2)

    @patch('storage.brokers.s3_broker.S3Client')
    def test_upload_files(self, mock_client_class):
        """Tests uploading files successfully"""

        s3_object_1 = MagicMock()
        s3_object_2 = MagicMock()
        mock_client = MagicMock(S3Client)
        mock_client.get_object.side_effect = [s3_object_1, s3_object_2]
        mock_client_class.return_value.__enter__ = Mock(return_value=mock_client)

        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_name_1)
        local_path_file_2 = os.path.join('my_dir_2', file_name_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_name_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_name_2)

        file_1 = storage_test_utils.create_file(file_path=workspace_path_file_1, media_type='text/plain')
        file_2 = storage_test_utils.create_file(file_path=workspace_path_file_2, media_type='application/json')
        file_1_up = FileUpload(file_1, local_path_file_1)
        file_2_up = FileUpload(file_2, local_path_file_2)

        # Call method to test
        mo = mock_open()
        with patch('__builtin__.open', mo, create=True):
            self.broker.upload_files(None, [file_1_up, file_2_up])

        # Check results
        self.assertTrue(s3_object_1.upload_file.called)
        self.assertTrue(s3_object_2.upload_file.called)
        self.assertEqual(s3_object_1.upload_file.call_args[0][1]['ContentType'], 'text/plain')
        self.assertEqual(s3_object_2.upload_file.call_args[0][1]['ContentType'], 'application/json')

    def test_validate_configuration_roles(self):
        """Tests validating a configuration based on IAM roles successfully"""

        json_config = {
            'type': S3Broker().broker_type,
            'bucket_name': 'my_bucket.domain.com',
        }
        broker = S3Broker()

        # No exception is success
        broker.load_configuration(json_config)

    def test_validate_configuration_keys(self):
        """Tests validating a configuration based on IAM keys successfully"""

        json_config = {
            'type': S3Broker().broker_type,
            'bucket_name': 'my_bucket.domain.com',
            'credentials': {
                'access_key_id': 'ABC',
                'secret_access_key': '123',
            },
        }
        broker = S3Broker()

        # No exception is success
        broker.load_configuration(json_config)

    def test_validate_configuration_missing(self):
        """Tests validating a configuration with missing attributes"""

        json_config = {
            'type': S3Broker().broker_type,
        }
        broker = S3Broker()

        self.assertRaises(InvalidBrokerConfiguration, broker.validate_configuration, json_config)
