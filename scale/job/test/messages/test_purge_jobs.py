from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
from django.utils import timezone

from job.messages.purge_jobs import PurgeJobs
from job.models import Job, JobExecution
from job.test import utils as job_test_utils
from recipe.test import utils as recipe_test_utils
from storage.models import PurgeResults
from storage.test import utils as storage_test_utils
from trigger.test import utils as trigger_test_utils


class TestPurgeJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a PurgeJobs message to and from JSON"""

        job_exe = job_test_utils.create_job_exe(status='COMPLETED')
        job = job_exe.job

        # Add job to message
        message = PurgeJobs()
        message._purge_job_ids = [job.id]
        message.status_change = timezone.now()

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = PurgeJobs.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # Check that job is deleted
        self.assertEqual(Job.objects.filter(id=job.id).count(), 0)
        self.assertEqual(JobExecution.objects.filter(id=job_exe.id).count(), 0)

    def test_execute(self):
        """Tests calling PurgeJobs.execute() successfully"""

        job_exe = job_test_utils.create_job_exe(status='COMPLETED')
        job = job_exe.job

        # Add job to message
        message = PurgeJobs()
        message._purge_job_ids = [job.id]
        message.status_change = timezone.now()

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check that job is deleted
        self.assertEqual(Job.objects.filter(id=job.id).count(), 0)
        self.assertEqual(JobExecution.objects.filter(id=job_exe.id).count(), 0)

    def test_execute_with_input_file(self):
        """Tests calling PurgeJobs.execute() successfully"""

        input_file = storage_test_utils.create_file(file_type='SOURCE')
        job_exe = job_test_utils.create_job_exe(status='COMPLETED')
        job = job_exe.job
        job_test_utils.create_input_file(job=job, input_file=input_file)

        # Add job to message
        message = PurgeJobs()
        message._purge_job_ids = [job.id]
        message.source_file_id = input_file.id
        message.status_change = timezone.now()

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check that a new message to purge source file was created
        msgs = [msg for msg in message.new_messages if msg.type == 'purge_source_file']
        self.assertEqual(len(msgs), 1)
        for msg in msgs:
            self.assertEqual(msg.source_file_id, input_file.id)

    def test_execute_with_recipe(self):
        """Tests calling PurgeJobs.execute() successfully"""

        recipe = recipe_test_utils.create_recipe()
        job_exe = job_test_utils.create_job_exe(status='COMPLETED')
        job = job_exe.job
        recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', job=job, save=True)
        input_file = storage_test_utils.create_file(file_type='SOURCE')

        # Add job to message
        message = PurgeJobs()
        message._purge_job_ids = [job.id]
        message.source_file_id = input_file.id
        message.status_change = timezone.now()

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check that a new message to purge source file was created
        msgs = [msg for msg in message.new_messages if msg.type == 'purge_recipe']
        self.assertEqual(len(msgs), 1)
        for msg in msgs:
            self.assertEqual(msg.recipe_id, recipe.id)

    def test_execute_check_results(self):
        """Tests calling PurgeJobs.execute() successfully"""

        # Create PurgeResults entry
        source_file = storage_test_utils.create_file()
        trigger = trigger_test_utils.create_trigger_event()
        PurgeResults.objects.create(source_file_id=source_file.id, trigger_event=trigger)
        self.assertEqual(PurgeResults.objects.values_list('num_jobs_deleted', flat=True).get(
            source_file_id=source_file.id), 0)

        job_exe_1 = job_test_utils.create_job_exe(status='COMPLETED')
        job_exe_2 = job_test_utils.create_job_exe(status='COMPLETED')
        job_exe_3 = job_test_utils.create_job_exe(status='COMPLETED')
        job_1 = job_exe_1.job
        job_2 = job_exe_2.job
        job_3 = job_exe_3.job

        # Add job to message
        message = PurgeJobs()
        message.source_file_id = source_file.id
        message._purge_job_ids = [job_1.id, job_2.id, job_3.id]
        message.status_change = timezone.now()

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check results are accurate
        self.assertEqual(PurgeResults.objects.values_list('num_jobs_deleted', flat=True).get(
            source_file_id=source_file.id), 3)
