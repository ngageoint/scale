from __future__ import unicode_literals

import os

import django
from django.test import TestCase
from mock import call, patch

from job.test import utils as job_test_utils
from storage.brokers.host_broker import HostBroker
from storage.destroy_files_job import destroy_files
from storage.configuration.workspace_configuration import WorkspaceConfiguration
from storage.test import utils as storage_test_utils


class TestCallScaleDestroyFile(TestCase):

    def setUp(self):
        django.setup()

        self.job_1 = job_test_utils.create_job()
        self.file_1 = storage_test_utils.create_file()
        self.workspace = storage_test_utils.create_workspace()

    @patch('storage.destroy_files_job.destroy_files')
    def test_scale_destroy_file(self, mock_destroy):
        """Tests calling Scale to delete files"""

        def new_destroy(files, job_id, volume_path, broker):
            return 0
        mock_destroy.side_effect = new_destroy

        config = WorkspaceConfiguration(self.workspace.json_config)

        files_str = '-f {"file_path":"/dir/file.name", "id":"12300"}'
        job_id_str = '-j %i' % (self.job_1.id)
        workspace_str = '-w "%s"' % (config.get_dict())
        purge_str = '-p False'

        django.core.management.call_command('scale_destroy_file', files_str, job_id_str, workspace_str, purge_str)



        # volume_path = os.path.join('the', 'volume', 'path')
        # file_path_1 = os.path.join('my_dir', 'my_file.txt')
        # file_path_2 = os.path.join('my_dir', 'my_file.json')
        # full_path_file_1 = os.path.join(volume_path, file_path_1)
        # full_path_file_2 = os.path.join(volume_path, file_path_2)

        # file_1 = storage_test_utils.create_file(file_path=file_path_1)
        # file_2 = storage_test_utils.create_file(file_path=file_path_2)

        # # Call function
        # test_1 = destroy_files([file_1], job_1.id, volume_path, self.broker)
        # self.assertEqual(test_1, 0)

        # test_2 = destroy_files([file_2], job_1.id, volume_path, self.broker)
        # self.assertEqual(test_2, 0)

        # # Check results
        # two_calls = [call(full_path_file_1), call(full_path_file_2)]
        # mock_remove.assert_has_calls(two_calls)