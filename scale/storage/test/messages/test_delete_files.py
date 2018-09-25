from __future__ import unicode_literals

import os

import django
from django.test import TestCase

from job.test import utils as job_test_utils
from storage.messages.delete_files import create_delete_files_messages, DeleteFiles
from storage.models import ScaleFile
from storage.test import utils as storage_test_utils
import trigger.test.utils as trigger_test_utils


class TestDeleteFiles(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a DeleteFiles message to and from JSON"""

        job = job_test_utils.create_job()
        job_exe = job_test_utils.create_job_exe(job=job)

        file_path_1 = os.path.join('my_dir', 'my_file.txt')
        file_path_2 = os.path.join('my_dir', 'my_file.json')

        file_1 = storage_test_utils.create_file(file_path=file_path_1, job_exe=job_exe)
        file_2 = storage_test_utils.create_file(file_path=file_path_2, job_exe=job_exe)

        # Add files to message
        message = DeleteFiles()
        message.purge = True
        message.job_id = job.id
        if message.can_fit_more():
            message.add_file(file_1.id)
        if message.can_fit_more():
            message.add_file(file_2.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = DeleteFiles.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # Both files should have been deleted
        self.assertEqual(ScaleFile.objects.filter(id=file_1.id).count(), 0)
        self.assertEqual(ScaleFile.objects.filter(id=file_2.id).count(), 0)

        # One new job for create_purge_jobs_messages
        self.assertEqual(len(new_message.new_messages), 1)

    def test_execute(self):
        """Tests calling DeleteFile.execute() successfully"""

        job = job_test_utils.create_job()
        job_exe = job_test_utils.create_job_exe(job=job)
        
        file_path_1 = os.path.join('my_dir', 'my_file.txt')
        file_path_2 = os.path.join('my_dir', 'my_file1.json')
        file_path_3 = os.path.join('my_dir', 'my_file2.json')
        file_path_4 = os.path.join('my_dir', 'my_file3.json')

        file_1 = storage_test_utils.create_file(file_path=file_path_1, job_exe=job_exe)
        file_2 = storage_test_utils.create_file(file_path=file_path_2, job_exe=job_exe)
        file_3 = storage_test_utils.create_file(file_path=file_path_3, job_exe=job_exe)
        file_4 = storage_test_utils.create_file(file_path=file_path_4, job_exe=job_exe)

        # Add files to message
        message = DeleteFiles()
        message.purge = False
        message.job_id = job.id
        if message.can_fit_more():
            message.add_file(file_1.id)
        if message.can_fit_more():
            message.add_file(file_2.id)
        if message.can_fit_more():
            message.add_file(file_3.id)
        if message.can_fit_more():
            message.add_file(file_4.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # All files should have marked as deleted
        self.assertTrue(ScaleFile.objects.filter(id=file_1.id).values('is_deleted'))
        self.assertTrue(ScaleFile.objects.filter(id=file_2.id).values('is_deleted'))
        self.assertTrue(ScaleFile.objects.filter(id=file_3.id).values('is_deleted'))
        self.assertTrue(ScaleFile.objects.filter(id=file_4.id).values('is_deleted'))

        file_5 = storage_test_utils.create_file(file_path=file_path_1)
        file_6 = storage_test_utils.create_file(file_path=file_path_2)
        file_7 = storage_test_utils.create_file(file_path=file_path_3)
        file_8 = storage_test_utils.create_file(file_path=file_path_4)

        # Add files to message
        message = DeleteFiles()
        message.purge = True
        message.job_id = job.id
        if message.can_fit_more():
            message.add_file(file_5.id)
        if message.can_fit_more():
            message.add_file(file_6.id)
        if message.can_fit_more():
            message.add_file(file_7.id)
        if message.can_fit_more():
            message.add_file(file_8.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # All files should have been purged
        self.assertEqual(ScaleFile.objects.filter(id=file_5.id).count(), 0)
        self.assertEqual(ScaleFile.objects.filter(id=file_6.id).count(), 0)
        self.assertEqual(ScaleFile.objects.filter(id=file_7.id).count(), 0)
        self.assertEqual(ScaleFile.objects.filter(id=file_8.id).count(), 0)

    def test_create_message(self):
        """
        Tests calling the create message function for DeleteFiles
        """

        job = job_test_utils.create_job()
        job_exe = job_test_utils.create_job_exe(job=job)

        trigger = trigger_test_utils.create_trigger_event()

        file_path_1 = os.path.join('my_dir', 'my_file.txt')
        file_path_2 = os.path.join('my_dir', 'my_file1.json')
        file_path_3 = os.path.join('my_dir', 'my_file2.json')
        file_path_4 = os.path.join('my_dir', 'my_file3.json')

        file_1 = storage_test_utils.create_file(file_path=file_path_1, job_exe=job_exe)
        file_2 = storage_test_utils.create_file(file_path=file_path_2, job_exe=job_exe)
        file_3 = storage_test_utils.create_file(file_path=file_path_3, job_exe=job_exe)
        file_4 = storage_test_utils.create_file(file_path=file_path_4, job_exe=job_exe)

        files = [file_1, file_2, file_3, file_4]

        # No exception is success
        create_delete_files_messages(files=files, job_id=job.id, trigger_id=trigger.id, purge=True)
