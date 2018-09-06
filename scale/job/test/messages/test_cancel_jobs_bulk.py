from __future__ import unicode_literals

from datetime import timedelta

import django
from django.test import TestCase

import batch.test.utils as batch_test_utils
import recipe.test.utils as recipe_test_utils
from error.test import utils as error_test_utils
from job.configuration.data.job_data import JobData
from job.messages.cancel_jobs_bulk import CancelJobsBulk
from job.test import utils as job_test_utils


class TestCancelJobsBulk(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a CancelJobsBulk message to and from JSON"""

        sys_err = error_test_utils.create_error(category='SYSTEM')

        data = JobData()
        batch = batch_test_utils.create_batch()
        recipe = recipe_test_utils.create_recipe()
        job_type = job_test_utils.create_job_type()
        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err,
                                          input=data.get_dict())
        job_1.batch_id = batch.id
        job_1.recipe_id = recipe.id
        job_1.save()
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err,
                                          input=data.get_dict())

        # Create message
        message = CancelJobsBulk()
        message.started = job_1.last_modified - timedelta(seconds=1)
        message.ended = job_1.last_modified + timedelta(seconds=1)
        message.error_categories = ['SYSTEM']
        message.error_ids = [sys_err.id]
        message.job_ids = [job_1.id]
        message.job_type_ids = [job_type.id]
        message.status = 'FAILED'
        message.job_type_names = [job_type.name]
        message.batch_ids = [batch.id]
        message.recipe_ids = [recipe.id]
        message.is_superseded = False

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CancelJobsBulk.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        # Should be one cancel message for job 1
        self.assertEqual(len(new_message.new_messages), 1)
        message = new_message.new_messages[0]
        self.assertEqual(message.type, 'cancel_jobs')
        self.assertListEqual(message._job_ids, [job_1.id])

    def test_execute(self):
        """Tests calling CancelJobsBulk.execute() successfully"""

        # Importing module here to patch the max batch size
        import job.messages.cancel_jobs_bulk
        job.messages.cancel_jobs_bulk.MAX_BATCH_SIZE = 5

        sys_err = error_test_utils.create_error(category='SYSTEM')

        job_type = job_test_utils.create_job_type()
        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err)
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err)
        job_3 = job_test_utils.create_job(job_type=job_type, num_exes=1, status='COMPLETED')
        job_4 = job_test_utils.create_job(job_type=job_type, status='BLOCKED')
        job_5 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='CANCELED')
        job_6 = job_test_utils.create_job(job_type=job_type, status='PENDING')
        job_7 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err)

        # Create message
        message = job.messages.cancel_jobs_bulk.CancelJobsBulk()
        message.job_type_ids = [job_type.id]

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Should be two messages, one for next bulk cancel and one for canceling the specific jobs
        self.assertEqual(len(message.new_messages), 2)
        cancel_bulk_message = message.new_messages[0]
        cancel_message = message.new_messages[1]
        self.assertEqual(cancel_bulk_message.type, 'cancel_jobs_bulk')
        self.assertEqual(cancel_bulk_message.current_job_id, job_3.id)
        self.assertEqual(cancel_message.type, 'cancel_jobs')
        # Job 5 is skipped due to being CANCELED and job 3 is skipped due to being COMPLETED
        self.assertListEqual(cancel_message._job_ids, [job_7.id, job_6.id, job_4.id])

        # Test executing message again
        message.new_messages = []
        result = message.execute()
        self.assertTrue(result)

        # Should have same messages returned
        self.assertEqual(len(message.new_messages), 2)
        cancel_bulk_message = message.new_messages[0]
        cancel_message = message.new_messages[1]
        self.assertEqual(cancel_bulk_message.type, 'cancel_jobs_bulk')
        self.assertEqual(cancel_bulk_message.current_job_id, job_3.id)
        self.assertEqual(cancel_message.type, 'cancel_jobs')
        # Job 5 is skipped due to being CANCELED and job 3 is skipped due to being COMPLETED
        self.assertListEqual(cancel_message._job_ids, [job_7.id, job_6.id, job_4.id])
