from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
from django.utils.timezone import now

from error.test import utils as error_test_utils
from job.configuration.data.job_data import JobData
from job.messages.failed_jobs import FailedJob, FailedJobs
from job.models import Job
from job.test import utils as job_test_utils
from queue.models import Queue


class TestFailedJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a FailedJobs message to and from JSON"""

        error = error_test_utils.create_error(should_be_retried=True)

        data = JobData()
        job_1 = job_test_utils.create_job(num_exes=1, status='QUEUED', input=data.get_dict(), max_tries=2)
        job_2 = job_test_utils.create_job(num_exes=1, status='RUNNING', input=data.get_dict(), max_tries=1)
        job_3 = job_test_utils.create_job(num_exes=0, status='PENDING')
        job_ids = [job_1.id, job_2.id, job_3.id]

        from recipe.test import utils as recipe_test_utils
        recipe_1 = recipe_test_utils.create_recipe()
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_2)

        when_ended = now()

        # Add jobs to message
        message = FailedJobs()
        message.ended = when_ended
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_1.id, job_1.num_exes, error.id))
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_2.id, job_2.num_exes, error.id))
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_3.id, job_3.num_exes, error.id))

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = FailedJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        queued_jobs_msg = None
        update_recipes_msg = None
        update_recipe_metrics_msg = None
        self.assertEqual(len(new_message.new_messages), 3)
        for msg in new_message.new_messages:
            if msg.type == 'queued_jobs':
                queued_jobs_msg = msg
            elif msg.type == 'update_recipes':
                update_recipes_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_recipe_metrics_msg = msg
        # Job 1 should be retried and put back on the queue
        self.assertEqual(jobs[0].status, 'QUEUED')
        self.assertEqual(jobs[0].num_exes, 1)
        self.assertEqual(len(queued_jobs_msg._queued_jobs), 1)
        self.assertEqual(queued_jobs_msg._queued_jobs[0].job_id, job_1.id)
        self.assertTrue(queued_jobs_msg.requeue)
        # Job 2 should be failed since max_tries is used up
        self.assertEqual(jobs[1].status, 'FAILED')
        self.assertEqual(jobs[1].num_exes, 1)
        self.assertEqual(jobs[1].error_id, error.id)
        self.assertEqual(jobs[1].ended, when_ended)
        self.assertEqual(len(update_recipes_msg._recipe_ids), 1)
        self.assertTrue(recipe_1.id in update_recipes_msg._recipe_ids)
        # Job 3 should ignore update
        self.assertEqual(jobs[2].status, 'PENDING')
        self.assertEqual(jobs[2].num_exes, 0)

    def test_execute(self):
        """Tests calling FailedJobs.execute() successfully"""

        error_1 = error_test_utils.create_error(should_be_retried=True)
        error_2 = error_test_utils.create_error(should_be_retried=False)

        data = JobData()
        job_1 = job_test_utils.create_job(num_exes=1, status='QUEUED', input=data.get_dict(), max_tries=2)
        job_2 = job_test_utils.create_job(num_exes=1, status='RUNNING', input=data.get_dict(), max_tries=2)
        job_3 = job_test_utils.create_job(num_exes=1, status='RUNNING', input=data.get_dict(), max_tries=1)
        job_4 = job_test_utils.create_job(num_exes=1, status='RUNNING', input=data.get_dict(), max_tries=2)
        job_5 = job_test_utils.create_job(num_exes=1, status='RUNNING', input=data.get_dict(), max_tries=2)
        job_6 = job_test_utils.create_job(num_exes=1, status='FAILED', input=data.get_dict(), max_tries=2)
        job_7 = job_test_utils.create_job(num_exes=0, status='CANCELED')
        job_ids = [job_1.id, job_2.id, job_3.id, job_4.id, job_5.id, job_6.id, job_7.id]

        from recipe.test import utils as recipe_test_utils
        recipe_1 = recipe_test_utils.create_recipe()
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_3)
        recipe_2 = recipe_test_utils.create_recipe()
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_4)

        when_ended = now()

        # Add jobs to message
        message = FailedJobs()
        message.ended = when_ended
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_1.id, job_1.num_exes, error_1.id))
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_2.id, job_2.num_exes, error_1.id))
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_3.id, job_3.num_exes, error_1.id))
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_4.id, job_4.num_exes, error_2.id))  # Error that cannot be retried
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_5.id, job_5.num_exes - 1, error_1.id))  # Mismatched exe_num
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_6.id, job_6.num_exes, error_1.id))
        if message.can_fit_more():
            message.add_failed_job(FailedJob(job_7.id, job_7.num_exes - 1, error_1.id))

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        queued_jobs_msg = None
        update_recipes_msg = None
        update_recipe_metrics_msg = None
        self.assertEqual(len(message.new_messages), 3)
        for msg in message.new_messages:
            if msg.type == 'queued_jobs':
                queued_jobs_msg = msg
            elif msg.type == 'update_recipes':
                update_recipes_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_recipe_metrics_msg = msg
        self.assertTrue(queued_jobs_msg.requeue)
        self.assertEqual(len(queued_jobs_msg._queued_jobs), 2)  # 2 jobs should have been retried
        self.assertEqual(len(update_recipes_msg._recipe_ids), 2)  # 2 jobs should have been failed

        # Job 1 should be retried and put back on the queue
        self.assertEqual(jobs[0].status, 'QUEUED')
        self.assertEqual(jobs[0].num_exes, 1)
        self.assertEqual(queued_jobs_msg._queued_jobs[0].job_id, job_1.id)
        # Job 2 should be retried and put back on the queue
        self.assertEqual(jobs[1].status, 'RUNNING')
        self.assertEqual(jobs[1].num_exes, 1)
        self.assertEqual(queued_jobs_msg._queued_jobs[1].job_id, job_2.id)
        # Job 3 should be failed since max_tries is used up
        self.assertEqual(jobs[2].status, 'FAILED')
        self.assertEqual(jobs[2].num_exes, 1)
        self.assertEqual(jobs[2].error_id, error_1.id)
        self.assertEqual(jobs[2].ended, when_ended)
        self.assertTrue(recipe_1.id in update_recipes_msg._recipe_ids)
        # Job 4 should be failed since error cannot be retried
        self.assertEqual(jobs[3].status, 'FAILED')
        self.assertEqual(jobs[3].num_exes, 1)
        self.assertEqual(jobs[3].error_id, error_2.id)
        self.assertEqual(jobs[3].ended, when_ended)
        self.assertTrue(recipe_2.id in update_recipes_msg._recipe_ids)
        # Job 5 should be ignored since mismatched exe_num
        self.assertEqual(jobs[4].status, 'RUNNING')
        self.assertEqual(jobs[4].num_exes, 1)
        # Job 6 should be ignored since it is already failed
        self.assertEqual(jobs[5].status, 'FAILED')
        self.assertEqual(jobs[5].num_exes, 1)
        # Job 6 should be ignored since it is canceled
        self.assertEqual(jobs[6].status, 'CANCELED')
        self.assertEqual(jobs[6].num_exes, 0)

        # Test executing message again
        message_json_dict = message.to_json()
        message = FailedJobs.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        queued_jobs_msg = None
        update_recipes_msg = None
        update_recipe_metrics_msg = None
        self.assertEqual(len(message.new_messages), 2)
        for msg in message.new_messages:
            if msg.type == 'queued_jobs':
                queued_jobs_msg = msg
            elif msg.type == 'update_recipes':
                update_recipes_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_recipe_metrics_msg = msg
        self.assertEqual(queued_jobs_msg.type, 'queued_jobs')
        self.assertTrue(queued_jobs_msg.requeue)
        # The same 2 jobs should have been retried
        self.assertEqual(len(queued_jobs_msg._queued_jobs), 2)

        # Job 1 should be retried and put back on the queue
        self.assertEqual(jobs[0].status, 'QUEUED')
        self.assertEqual(jobs[0].num_exes, 1)
        self.assertEqual(queued_jobs_msg._queued_jobs[0].job_id, job_1.id)
        # Job 2 should be retried and put back on the queue
        self.assertEqual(jobs[1].status, 'RUNNING')
        self.assertEqual(jobs[1].num_exes, 1)
        self.assertEqual(queued_jobs_msg._queued_jobs[1].job_id, job_2.id)
        # Job 3 should be failed from first execution
        self.assertEqual(jobs[2].status, 'FAILED')
        self.assertEqual(jobs[2].num_exes, 1)
        self.assertEqual(jobs[2].error_id, error_1.id)
        # Job 4 should be failed from first execution
        self.assertEqual(jobs[3].status, 'FAILED')
        self.assertEqual(jobs[3].num_exes, 1)
        self.assertEqual(jobs[3].error_id, error_2.id)
        # Job 5 should be ignored since mismatched exe_num
        self.assertEqual(jobs[4].status, 'RUNNING')
        self.assertEqual(jobs[4].num_exes, 1)
        # Job 6 should be ignored since it is already failed
        self.assertEqual(jobs[5].status, 'FAILED')
        self.assertEqual(jobs[5].num_exes, 1)
        # Job 6 should be ignored since it is canceled
        self.assertEqual(jobs[6].status, 'CANCELED')
        self.assertEqual(jobs[6].num_exes, 0)
