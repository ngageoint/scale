from __future__ import unicode_literals

import os

import django
from django.test import TestCase
from mock import call, patch

from storage.brokers.host_broker import HostBroker
from storage.delete_files_job import delete_files
from storage.configuration.workspace_configuration import WorkspaceConfiguration
from storage.test import utils as storage_test_utils


class TestCallScaleDeleteFiles(TestCase):

    def setUp(self):
        django.setup()

        self.file_1 = storage_test_utils.create_file()
        self.workspace = storage_test_utils.create_workspace()

    @patch('storage.management.commands.scale_delete_files.delete_files_job')
    @patch('storage.management.commands.scale_delete_files.CommandMessageManager')
    def test_scale_delete_files(self, mock_message, mock_delete):
        """Tests calling Scale to delete files"""

        def new_delete(files, volume_path, broker):
            return
        mock_delete.side_effect = new_delete

        config = WorkspaceConfiguration(self.workspace.json_config)

        files_str = '-f {"file_path":"/dir/file.name", "id":"12300", "workspace":"workspace_1"}'
        workspace_str = '-w {"workspace_1": %s}' % (config.get_dict())
        purge_str = '-p False'

        with self.assertRaises(SystemExit):
            django.core.management.call_command('scale_delete_files', files_str, workspace_str, purge_str)
