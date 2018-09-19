from __future__ import unicode_literals

import json
import os

import django
from django.test import TestCase
from mock import call, patch

from job.test import utils as job_test_utils
from storage.brokers.host_broker import HostBroker
from storage.delete_files_job import delete_files
from storage.configuration.workspace_configuration import WorkspaceConfiguration
from storage.test import utils as storage_test_utils


class TestCallScaleDeleteFiles(TestCase):

    def setUp(self):
        django.setup()

        self.job_1 = job_test_utils.create_job()
        self.job_exe_1 = job_test_utils.create_job_exe(job=self.job_1)
        self.file_1 = storage_test_utils.create_file(job_exe=self.job_exe_1)
        self.workspace = storage_test_utils.create_workspace()

    @patch('storage.management.commands.scale_delete_files.delete_files_job')
    @patch('storage.management.commands.scale_delete_files.CommandMessageManager')
    def test_scale_delete_files(self, mock_message, mock_delete):
        """Tests calling Scale to delete files"""

        def new_delete(files, volume_path, broker):
            return
        mock_delete.side_effect = new_delete

        config = WorkspaceConfiguration(self.workspace.json_config)

        os.environ['FILES'] = json.dumps([{"file_path":"/dir/file.name", "id":"12300", "workspace":"workspace_1"}])
        os.environ['WORKSPACES'] = json.dumps([{"workspace_1": config.get_dict()}])
        os.environ['PURGE'] = str(False)
        os.environ['JOB_ID'] = str(self.job_1.id)


        with self.assertRaises(SystemExit):
            django.core.management.call_command('scale_delete_files')
