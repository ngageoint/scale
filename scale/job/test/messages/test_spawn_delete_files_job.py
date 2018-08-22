from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
from django.utils import timezone

from job.messages.spawn_delete_files_job import SpawnDeleteFilesJob
from job.models import Job, JobExecution
from job.test import utils as job_test_utils
from storage.test import utils as storage_test_utils


class TestSpawnDeleteFilesJob(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a PurgeJobs message to and from JSON"""

        job_exe = job_test_utils.create_job_exe(status='COMPLETED')
        wp1 = storage_test_utils.create_workspace()
        wp2 = storage_test_utils.create_workspace()
        prod1 = storage_test_utils.create_file(file_type='PRODUCT', workspace=wp1)
        prod2 = storage_test_utils.create_file(file_type='PRODUCT', workspace=wp1)
        prod3 = storage_test_utils.create_file(file_type='PRODUCT', workspace=wp2)
        job = job_exe.job

        # Add job to message
        message = SpawnDeleteFilesJob()
        message.job_id = job.id
        message.purge = True

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = PurgeJobs.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

    #     # Check that job is deleted
    #     self.assertEqual(Job.objects.filter(id=job.id).count(), 0)
    #     self.assertEqual(JobExecution.objects.filter(id=job_exe.id).count(), 0)

    # def test_execute(self):
    #     """Tests calling PurgeJobs.execute() successfully"""

    #     job_exe = job_test_utils.create_job_exe(status='COMPLETED')
    #     job = job_exe.job

    #     # Add job to message
    #     message = PurgeJobs()
    #     message._purge_job_ids = [job.id]
    #     message.status_change = timezone.now()

    #     # Execute message
    #     result = message.execute()
    #     self.assertTrue(result)

    #     # Check that job is deleted
    #     self.assertEqual(Job.objects.filter(id=job.id).count(), 0)
    #     self.assertEqual(JobExecution.objects.filter(id=job_exe.id).count(), 0)
