from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from job.messages.spawn_delete_files_job import create_spawn_delete_files_job, SpawnDeleteFilesJob
from job.models import Job, JobType
from job.test import utils as job_test_utils
from storage.test import utils as storage_test_utils
from trigger.test import utils as trigger_test_utils


class TestSpawnDeleteFilesJob(TransactionTestCase):

    fixtures = ['delete_files_job_type.json']

    def setUp(self):
        django.setup()

        self.count = 1
        self.job_type = job_test_utils.create_job_type()
        self.job = job_test_utils.create_job(job_type=self.job_type)
        self.job_exe = job_test_utils.create_job_exe(status='COMPLETED', job=self.job)
        self.wp1 = storage_test_utils.create_workspace()
        self.wp2 = storage_test_utils.create_workspace()
        self.prod1 = storage_test_utils.create_file(file_type='PRODUCT', workspace=self.wp1, job_exe=self.job_exe)
        self.prod2 = storage_test_utils.create_file(file_type='PRODUCT', workspace=self.wp1, job_exe=self.job_exe)
        self.prod3 = storage_test_utils.create_file(file_type='PRODUCT', workspace=self.wp2, job_exe=self.job_exe)
        self.event = trigger_test_utils.create_trigger_event()
        self.file_1 = storage_test_utils.create_file(file_type='SOURCE')

    def test_json(self):
        """Tests coverting a SpawnDeleteFilesJob message to and from JSON"""

        # Make the message
        message = create_spawn_delete_files_job(job_id=self.job.pk, trigger_id=self.event.id,
                                                source_file_id=self.file_1.id, purge=True)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = SpawnDeleteFilesJob.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)
        self.assertEqual(new_message.job_id, self.job.pk)
        self.assertEqual(new_message.trigger_id, self.event.id)

        # Check for create_jobs messages
        self.assertEqual(len(new_message.new_messages), self.count)
        for msg in new_message.new_messages:
            self.assertEqual(msg.type, 'create_jobs')

    def test_execute(self):
        """Tests calling SpawnDeleteFilesJob.execute successfully"""

        job_type_id = JobType.objects.values_list('id', flat=True).get(name='scale-delete-files')

        # Make the message
        message = create_spawn_delete_files_job(job_id=self.job.pk, trigger_id=self.event.id,
                                                source_file_id=self.file_1.id, purge=True)

        # Capture message that creates job
        result = message.execute()
        self.assertTrue(result)

        for msg in message.new_messages:
            msg.execute()

        # Check that job is created
        self.assertEqual(Job.objects.filter(job_type_id=job_type_id, event_id=self.event.id).count(), self.count)

    def test_execute_no_job(self):
        """Tests calling SpawnDeleteFilesJob.execute with the id of a job that does not exist"""

        job_type_id = JobType.objects.values_list('id', flat=True).get(name='scale-delete-files')
        job_id = 1234574223462
        # Make the message
        message = create_spawn_delete_files_job(job_id=job_id, trigger_id=self.event.id,
                                                source_file_id=self.file_1.id, purge=True)

        # Capture message that creates job
        result = message.execute()
        self.assertTrue(result)

        # Check that no message was created
        self.assertEqual(len(message.new_messages), 0)
