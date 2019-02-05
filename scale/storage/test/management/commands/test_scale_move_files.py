from __future__ import unicode_literals

import json
import os

import django
from django.test import TestCase
from mock import patch

from job.test import utils as job_test_utils
from storage.configuration.json.workspace_config_v6 import WorkspaceConfigurationV6
from storage.test import utils as storage_test_utils
from storage.models import Workspace
import trigger.test.utils as trigger_test_utils


class TestCallScaleMoveFiles(TestCase):

    def setUp(self):
        django.setup()

        self.file_1 = storage_test_utils.create_file()
        self.workspace = storage_test_utils.create_workspace()

    @patch('storage.management.commands.scale_move_files.move_files_job')
    def test_scale_move_files_bad_workspace(self, mock_move):
        """Tests calling Scale to move files"""

        os.environ['FILE_IDS'] = json.dumps([self.file_1.id])
        os.environ['NEW_WORKSPACE'] = json.dumps("BAD_NAME")

        with self.assertRaises(Workspace.DoesNotExist):
            django.core.management.call_command('scale_move_files')

    @patch('storage.management.commands.scale_move_files.move_files_job')
    def test_scale_move_files_good_workspace(self, mock_move):
        """Tests calling Scale to move files"""

        os.environ['FILE_IDS'] = json.dumps([self.file_1.id])
        os.environ['NEW_WORKSPACE'] = json.dumps(self.workspace.name)

        with self.assertRaises(SystemExit):
            django.core.management.call_command('scale_move_files')
            
    @patch('storage.management.commands.scale_move_files.move_files_job')
    def test_scale_move_files_no_workspace(self, mock_move):
        """Tests calling Scale to move files"""

        os.environ['FILE_IDS'] = json.dumps([self.file_1.id])
        os.environ['NEW_PATH'] = json.dumps('/new/path/to/file.txt')

        with self.assertRaises(SystemExit):
            django.core.management.call_command('scale_move_files')