from __future__ import unicode_literals

from datetime import timedelta

import django
from django.test import TestCase

import batch.test.utils as batch_test_utils
import recipe.test.utils as recipe_test_utils
from error.test import utils as error_test_utils
from job.configuration.data.job_data import JobData
from job.test import utils as job_test_utils
from queue.messages.queued_jobs import QueuedJob
from queue.messages.requeue_jobs_bulk import RequeueJobsBulk


class TestRequeueJobsBulk(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a RequeueJobsBulk message to and from JSON"""

        sys_err = error_test_utils.create_error(category='SYSTEM')

        data = JobData()
        batch = batch_test_utils.create_batch()
        recipe = recipe_test_utils.create_recipe()
        job_type = job_test_utils.create_job_type()
        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err,
                                          input=data.get_dict())
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='CANCELED', error=sys_err,
                                          input=data.get_dict())

        # Create message
        message = RequeueJobsBulk()
        message.started = job_1.last_modified - timedelta(seconds=1)
        message.ended = job_1.last_modified + timedelta(seconds=1)
        message.error_categories = ['SYSTEM']
        message.error_ids = [sys_err.id]
        message.job_ids = [job_1.id]
        message.job_type_ids = [job_type.id]
        message.priority = 1
        message.status = 'FAILED'
        message.job_type_names = [job_type.name]
        message.batch_ids = [batch.id]
        message.recipe_ids = [recipe.id]
        message.is_superseded = False

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = RequeueJobsBulk.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        # Should be one re-queue message for job 1
        self.assertEqual(len(new_message.new_messages), 1)
        message = new_message.new_messages[0]
        self.assertEqual(message.type, 'requeue_jobs')
        self.assertListEqual(message._requeue_jobs, [QueuedJob(job_1.id, job_1.num_exes)])
        self.assertEqual(message.priority, 1)

    def test_execute(self):
        """Tests calling RequeueJobsBulk.execute() successfully"""

        # Importing module here to patch the max batch size
        import queue.messages.requeue_jobs_bulk
        queue.messages.requeue_jobs_bulk.MAX_BATCH_SIZE = 5

        sys_err = error_test_utils.create_error(category='SYSTEM')

        data = JobData()
        job_type = job_test_utils.create_job_type()
        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err,
                                          input=data.get_dict())
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err,
                                          input=data.get_dict())
        job_3 = job_test_utils.create_job(job_type=job_type, num_exes=0, status='FAILED', error=sys_err)
        job_4 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err,
                                          input=data.get_dict())
        job_5 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='CANCELED', error=sys_err,
                                          input=data.get_dict())
        job_6 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err,
                                          input=data.get_dict())
        job_7 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', error=sys_err,
                                          input=data.get_dict())

        # Create message
        message = queue.messages.requeue_jobs_bulk.RequeueJobsBulk()
        message.error_ids = [sys_err.id]
        message.job_type_ids = [job_type.id]
        message.priority = 10001
        message.status = 'FAILED'

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Should be two messages, one for next bulk re-queue and one for re-queuing the specific jobs
        self.assertEqual(len(message.new_messages), 2)
        requeue_bulk_message = message.new_messages[0]
        requeue_message = message.new_messages[1]
        self.assertEqual(requeue_bulk_message.type, 'requeue_jobs_bulk')
        self.assertEqual(requeue_bulk_message.current_job_id, job_2.id)
        self.assertEqual(requeue_message.type, 'requeue_jobs')
        # Job 5 is skipped due to CANCELED and job 3 has not been queued yet (forced illegal state)
        self.assertListEqual(requeue_message._requeue_jobs, [QueuedJob(job_7.id, job_7.num_exes),
                                                             QueuedJob(job_6.id, job_6.num_exes),
                                                             QueuedJob(job_4.id, job_4.num_exes),
                                                             QueuedJob(job_2.id, job_2.num_exes)])
        self.assertEqual(requeue_message.priority, 10001)

        # Test executing message again
        message.new_messages = []
        result = message.execute()
        self.assertTrue(result)

        # Should have same messages returned
        self.assertEqual(len(message.new_messages), 2)
        requeue_bulk_message = message.new_messages[0]
        requeue_message = message.new_messages[1]
        self.assertEqual(requeue_bulk_message.type, 'requeue_jobs_bulk')
        self.assertEqual(requeue_bulk_message.current_job_id, job_2.id)
        self.assertEqual(requeue_message.type, 'requeue_jobs')
        # Job 5 is skipped due to CANCELED and job 3 has not been queued yet (forced illegal state)
        self.assertListEqual(requeue_message._requeue_jobs, [QueuedJob(job_7.id, job_7.num_exes),
                                                             QueuedJob(job_6.id, job_6.num_exes),
                                                             QueuedJob(job_4.id, job_4.num_exes),
                                                             QueuedJob(job_2.id, job_2.num_exes)])
        self.assertEqual(requeue_message.priority, 10001)

    def test_execute_canceled(self):
        """Tests calling RequeueJobsBulk.execute() successfully to requeue canceled jobs"""

        data = JobData()
        job_type = job_test_utils.create_job_type()
        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='CANCELED', input=data.get_dict())
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=0, status='CANCELED')

        # Create message
        message = RequeueJobsBulk()
        message.job_type_ids = [job_type.id]
        message.priority = 10001

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Should be one message for re-queuing both jobs
        self.assertEqual(len(message.new_messages), 1)
        requeue_message = message.new_messages[0]
        self.assertEqual(requeue_message.type, 'requeue_jobs')
        self.assertListEqual(requeue_message._requeue_jobs, [QueuedJob(job_2.id, job_2.num_exes),
                                                             QueuedJob(job_1.id, job_1.num_exes)])
        self.assertEqual(requeue_message.priority, 10001)

        # Test executing message again
        message.new_messages = []
        result = message.execute()
        self.assertTrue(result)

        # Should have same message returned
        self.assertEqual(len(message.new_messages), 1)
        requeue_message = message.new_messages[0]
        self.assertEqual(requeue_message.type, 'requeue_jobs')
        self.assertListEqual(requeue_message._requeue_jobs, [QueuedJob(job_2.id, job_2.num_exes),
                                                             QueuedJob(job_1.id, job_1.num_exes)])
        self.assertEqual(requeue_message.priority, 10001)
