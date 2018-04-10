from __future__ import unicode_literals

import os

import django
from django.test import TestCase
from mock import call, patch

import job.test.utils as job_test_utils
from storage.brokers.host_broker import HostBroker
from storage.delete_files_job import delete_files
from storage.test import utils as storage_test_utils


class TestDeleteFiles(TestCase):

    def setUp(self):
        django.setup()

        self.broker = HostBroker()
        self.broker.load_configuration({'type': HostBroker().broker_type, 'host_path': '/host/path'})

    @patch('storage.brokers.host_broker.os.path.exists')
    @patch('storage.brokers.host_broker.os.remove')
    def test_delete_file(self, mock_remove, mock_exists):
        """Tests removing a file"""

        def new_exists(path):
            return True
        mock_exists.side_effect = new_exists

        job_1 = job_test_utils.create_job()

        volume_path = os.path.join('the', 'volume', 'path')
        file_path_1 = os.path.join('my_dir', 'my_file.txt')
        file_path_2 = os.path.join('my_dir', 'my_file.json')
        full_path_file_1 = os.path.join(volume_path, file_path_1)
        full_path_file_2 = os.path.join(volume_path, file_path_2)

        file_1 = storage_test_utils.create_file(file_path=file_path_1)
        file_2 = storage_test_utils.create_file(file_path=file_path_2)

        # Call function
        test_1 = delete_files([file_1], job_1.id, volume_path, self.broker)
        self.assertEqual(test_1, None)

        test_2 = delete_files([file_2], job_1.id, volume_path, self.broker)
        self.assertEqual(test_2, None)

        # Check results
        two_calls = [call(full_path_file_1), call(full_path_file_2)]
        mock_remove.assert_has_calls(two_calls)
