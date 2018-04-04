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
    @patch('messaging.manager.CommandMessageManager.send_messages')
    def test_scale_destroy_file(self, mock_message, mock_destroy):
        """Tests calling Scale to delete files"""

        def new_destroy(files, job_id, volume_path, broker):
            return 0
        mock_destroy.side_effect = new_destroy

        config = WorkspaceConfiguration(self.workspace.json_config)

        files_str = '-f {"file_path":"/dir/file.name", "id":"12300"}'
        job_id_str = '-j %i' % (self.job_1.id)
        workspace_str = '-w "%s"' % (config.get_dict())
        purge_str = '-p False'

        msg = django.core.management.call_command('scale_destroy_file', files_str, job_id_str, workspace_str, purge_str)
        
        self.assertEqual(msg, 0)