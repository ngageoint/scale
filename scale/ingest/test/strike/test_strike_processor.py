#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import json
import os
import time

import django
from django.test import TestCase
from mock import patch

import ingest.test.utils as ingest_test_utils
import job.test.utils as job_test_utils
import storage.test.utils as storage_test_utils
from ingest.container import SCALE_INGEST_MOUNT_PATH
from ingest.models import Ingest
from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from ingest.strike.configuration.strike_configuration import StrikeConfiguration
from ingest.strike.exceptions import SQSNotificationError, S3NoDataNotificationError
from ingest.strike.strike_processor import StrikeProcessor


class TestStrikeDeferFile(TestCase):

    def setUp(self):
        django.setup()

        self.ingest = ingest_test_utils.create_ingest(file_name='my_file.txt')

        self.mount = 'host:/path'
        self.mount_on = os.path.join('my', 'test')
        self.workspace = storage_test_utils.create_workspace()
        self.config = StrikeConfiguration({
            'version': '1.0',
            'mount': self.mount,
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'workspace_path': 'foo',
                'workspace_name': self.workspace.name,
            }],
        })
        self.job_exe = job_test_utils.create_job_exe()

        self.strike_proc = StrikeProcessor(1, self.job_exe.id, self.config)
        self.strike_dir = SCALE_INGEST_MOUNT_PATH

    def test_config_bad_filename_regex(self):
        '''Tests failing validation for invalid filename regex.'''

        config = {
            'version': '1.0',
            'mount': self.mount,
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': '*.txt',
                'workspace_path': 'foo',
                'workspace_name': self.workspace.name,
            }],
        }

        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)
        
    @patch('ingest.strike.strike_processor.os.path.exists')
    @patch('ingest.strike.strike_processor.os.rename')
    def test_defer_file_successful(self, mock_rename, mock_exists):
        '''Tests successfully deferring a file.'''
        # Set up mocks
        def new_exists(file_path):
            return True
        mock_exists.side_effect = new_exists

        # Set up data
        self.ingest.status = 'TRANSFERRED'

        # Call method to test
        self.strike_proc._defer_file(self.ingest)

        # Check results
        file_path = os.path.join(self.strike_dir, 'my_file.txt')
        deferred_path = os.path.join(self.strike_dir, 'deferred', 'my_file.txt')
        mock_rename.assert_called_with(file_path, deferred_path)
        saved_ingest = Ingest.objects.get(id=self.ingest.id)
        self.assertEqual(saved_ingest.status, 'DEFERRED')

    def test_complete_transfer_duplicate(self):
        '''Tests failing to complete an ingest in the wrong state.'''

        self.ingest.status = 'TRANSFERRED'

        self.assertRaises(Exception, self.strike_proc._complete_transfer, self.ingest, 0)

    @patch('ingest.strike.strike_processor.os.path.getmtime', lambda f: time.time())
    def test_complete_transfer_successful(self):
        '''Tests successfully completing an ingest transfer.'''

        self.strike_proc._complete_transfer(self.ingest, 1024)

        self.assertEqual(self.ingest.status, 'TRANSFERRED')
        self.assertEqual(self.ingest.file_size, 1024)
        self.assertEqual(self.ingest.workspace, self.workspace)
        self.assertTrue(self.ingest.file_path)
        self.assertTrue(self.ingest.ingest_path)


class TestStrikeSQSNotification(TestCase):

    def setUp(self):
        django.setup()

        self.valid_s3_object = '{"s3SchemaVersion": "1.0",' \
                               '"bucket": {"name": "scale-s3-create-retrieve-test","arn": ' \
                               '"arn:aws:s3:::scale-s3-create-retrieve-test"},' \
                               '"object": {"key": "test-40GiB.file","size": 42949672960}' \
                               '}'
        self.valid_s3_object = json.loads(self.valid_s3_object)
        self.invalid_s3_object = {}

        self.config = StrikeConfiguration({
            'version': '1.0',
            'mount': self.mount,
            'sqs_name': 'test',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'workspace_path': 'foo',
                'workspace_name': self.workspace.name,
            }],
        })
        self.job_exe = job_test_utils.create_job_exe()

        self.strike_proc = StrikeProcessor(1, self.job_exe.id, self.config)

    def test_process_s3_notification(self):
        """Tests successfully validating and S3 notification"""
        pass

    @patch(ingest.strike.strike_processor._ingest_s3_file)
    def test_ingest_s3_notification_object_success(self):
        """Test successfully ingesting a S3 object"""

        result = self.strike_proc._ingest_s3_notification_object(self.valid_s3_object)
        self.assertIsNone(result)

    @patch(ingest.strike.strike_processor._ingest_s3_file)
    def test_ingest_s3_notification_object_failure(self):
        """Test failing to ingest an S3 object"""

        with self.assertRaises(SQSNotificationError):
            self.strike_proc._ingest_s3_notification_object(self.invalid_s3_object)
