from __future__ import unicode_literals

import os

import django
from boto.s3.key import Key
from django.test import TestCase
from mock import MagicMock, Mock, mock_open, patch

from storage.brokers.broker import FileDownload, FileMove, FileUpload
from storage.brokers.exceptions import InvalidBrokerConfiguration
from storage.brokers.s3_broker import S3Broker, BrokerConnection
from storage.models import ScaleFile


class TestS3Broker(TestCase):

    def setUp(self):
        django.setup()

        self.broker = S3Broker()
        self.broker.load_configuration({
            'type': S3Broker().broker_type,
            'bucket_name': 'my_bucket.domain.com',
            'credentials': {
                'access_key_id': 'ABC',
                'secret_access_key': '123',
            },
        })

    @patch('storage.brokers.s3_broker.BrokerConnection')
    def test_delete_files(self, mock_conn_class):
        """Tests deleting files successfully"""

        s3_key_1 = MagicMock(Key)
        s3_key_2 = MagicMock(Key)
        mock_conn = MagicMock(BrokerConnection)
        mock_conn.get_key.side_effect = [s3_key_1, s3_key_2]
        mock_conn_class.return_value.__enter__ = Mock(return_value=mock_conn)

        file_path_1 = os.path.join('my_dir', 'my_file.txt')
        file_path_2 = os.path.join('my_dir', 'my_file.json')

        file_1 = ScaleFile(file_path=file_path_1)
        file_2 = ScaleFile(file_path=file_path_2)

        # Call method to test
        self.broker.delete_files(None, [file_1, file_2])

        # Check results
        self.assertTrue(s3_key_1.delete.called)
        self.assertTrue(s3_key_2.delete.called)
        self.assertTrue(file_1.is_deleted)
        self.assertIsNotNone(file_1.deleted)
        self.assertTrue(file_2.is_deleted)
        self.assertIsNotNone(file_2.deleted)

    @patch('storage.brokers.s3_broker.BrokerConnection')
    def test_download_files(self, mock_conn_class):
        """Tests downloading files successfully"""

        s3_key_1 = MagicMock(Key)
        s3_key_2 = MagicMock(Key)
        mock_conn = MagicMock(BrokerConnection)
        mock_conn.get_key.side_effect = [s3_key_1, s3_key_2]
        mock_conn_class.return_value.__enter__ = Mock(return_value=mock_conn)

        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_name_1)
        local_path_file_2 = os.path.join('my_dir_2', file_name_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_name_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_name_2)

        file_1 = ScaleFile(file_path=workspace_path_file_1)
        file_2 = ScaleFile(file_path=workspace_path_file_2)
        file_1_dl = FileDownload(file_1, local_path_file_1)
        file_2_dl = FileDownload(file_2, local_path_file_2)

        # Call method to test
        mo = mock_open()
        with patch('__builtin__.open', mo, create=True):
            self.broker.download_files(None, [file_1_dl, file_2_dl])

        # Check results
        self.assertTrue(s3_key_1.get_contents_to_file.called)
        self.assertTrue(s3_key_2.get_contents_to_file.called)

    def test_load_configuration(self):
        """Tests loading a valid configuration successfully"""

        json_config = {
            'type': S3Broker().broker_type,
            'bucket_name': 'my_bucket.domain.com',
            'credentials': {
                'access_key_id': 'ABC',
                'secret_access_key': '123',
            },
        }
        broker = S3Broker()
        broker.load_configuration(json_config)

        self.assertEqual(broker._bucket_name, 'my_bucket.domain.com')
        self.assertEqual(broker._credentials.access_key_id, 'ABC')
        self.assertEqual(broker._credentials.secret_access_key, '123')

    @patch('storage.brokers.s3_broker.BrokerConnection')
    def test_move_files(self, mock_conn_class):
        """Tests moving files successfully"""

        s3_key_1 = MagicMock(Key)
        s3_key_2 = MagicMock(Key)
        mock_conn = MagicMock(BrokerConnection)
        mock_conn.get_key.side_effect = [s3_key_1, s3_key_2]
        mock_conn_class.return_value.__enter__ = Mock(return_value=mock_conn)

        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        old_workspace_path_1 = os.path.join('my_dir_1', file_name_1)
        old_workspace_path_2 = os.path.join('my_dir_2', file_name_2)
        new_workspace_path_1 = os.path.join('my_new_dir_1', file_name_1)
        new_workspace_path_2 = os.path.join('my_new_dir_2', file_name_2)

        file_1 = ScaleFile(file_path=old_workspace_path_1)
        file_2 = ScaleFile(file_path=old_workspace_path_2)
        file_1_mv = FileMove(file_1, new_workspace_path_1)
        file_2_mv = FileMove(file_2, new_workspace_path_2)

        # Call method to test
        self.broker.move_files(None, [file_1_mv, file_2_mv])

        # Check results
        self.assertTrue(s3_key_1.copy.called)
        self.assertTrue(s3_key_2.copy.called)
        self.assertEqual(file_1.file_path, new_workspace_path_1)
        self.assertEqual(file_2.file_path, new_workspace_path_2)

    @patch('storage.brokers.s3_broker.BrokerConnection')
    def test_upload_files(self, mock_conn_class):
        """Tests uploading files successfully"""

        s3_key_1 = MagicMock(Key)
        s3_key_2 = MagicMock(Key)
        mock_conn = MagicMock(BrokerConnection)
        mock_conn.get_key.side_effect = [s3_key_1, s3_key_2]
        mock_conn_class.return_value.__enter__ = Mock(return_value=mock_conn)

        file_name_1 = 'my_file.txt'
        file_name_2 = 'my_file.json'
        local_path_file_1 = os.path.join('my_dir_1', file_name_1)
        local_path_file_2 = os.path.join('my_dir_2', file_name_2)
        workspace_path_file_1 = os.path.join('my_wrk_dir_1', file_name_1)
        workspace_path_file_2 = os.path.join('my_wrk_dir_2', file_name_2)

        file_1 = ScaleFile(file_path=workspace_path_file_1, media_type='text/plain')
        file_2 = ScaleFile(file_path=workspace_path_file_2, media_type='application/json')
        file_1_up = FileUpload(file_1, local_path_file_1)
        file_2_up = FileUpload(file_2, local_path_file_2)

        # Call method to test
        mo = mock_open()
        with patch('__builtin__.open', mo, create=True):
            self.broker.upload_files(None, [file_1_up, file_2_up])

        # Check results
        self.assertTrue(s3_key_1.set_contents_from_file.called)
        self.assertTrue(s3_key_2.set_contents_from_file.called)
        self.assertEqual(s3_key_1.set_contents_from_file.call_args[0][1]['Content-Type'], 'text/plain')
        self.assertEqual(s3_key_2.set_contents_from_file.call_args[0][1]['Content-Type'], 'application/json')

    def test_validate_configuration(self):
        """Tests validating a configuration successfully"""

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
