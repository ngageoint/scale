from __future__ import unicode_literals

import django
from django.test import TestCase

from job.configuration.data.job_data import JobData
from job.models import Job
from job.test import utils as job_test_utils
from queue.messages.queued_jobs import QueuedJob
from queue.messages.requeue_jobs import RequeueJobs


class TestRequeueJobs(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a RequeueJobs message to and from JSON"""

        data = JobData()
        job_type = job_test_utils.create_job_type(max_tries=3)
        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', input=data.get_dict())
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', input=data.get_dict())
        job_ids = [job_1.id, job_2.id]

        # Add jobs to message
        message = RequeueJobs()
        message.priority = 1
        if message.can_fit_more():
            message.add_job(job_1.id, job_1.num_exes)
        if message.can_fit_more():
            message.add_job(job_2.id, job_2.num_exes - 1)  # Mismatched exe_num

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = RequeueJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should have been good to re-queue, job 2 should have had mismatched exe_num and not been re-queued
        self.assertEqual(jobs[0].max_tries, 6)
        self.assertEqual(jobs[1].max_tries, 3)
        self.assertEqual(len(new_message.new_messages), 1)
        message = new_message.new_messages[0]
        self.assertEqual(message.type, 'queued_jobs')
        self.assertListEqual(message._queued_jobs, [QueuedJob(job_1.id, job_1.num_exes)])
        self.assertEqual(message.priority, 1)

    def test_execute(self):
        """Tests calling RequeueJobs.execute() successfully"""

        data = JobData()
        job_type = job_test_utils.create_job_type(max_tries=3)
        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', input=data.get_dict())
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=3, status='FAILED', input=data.get_dict())
        job_3 = job_test_utils.create_job(job_type=job_type, num_exes=1, status='COMPLETED', input=data.get_dict())
        job_4 = job_test_utils.create_job(job_type=job_type, num_exes=0, status='PENDING', input=data.get_dict())
        job_5 = job_test_utils.create_job(job_type=job_type, num_exes=0, status='CANCELED')
        job_ids = [job_1.id, job_2.id, job_3.id, job_4.id, job_5.id]

        # Add jobs to message
        message = RequeueJobs()
        message.priority = 101
        if message.can_fit_more():
            message.add_job(job_1.id, job_1.num_exes)
        if message.can_fit_more():
            message.add_job(job_2.id, job_2.num_exes - 1)  # Mismatched exe_num
        if message.can_fit_more():
            message.add_job(job_3.id, job_3.num_exes)
        if message.can_fit_more():
            message.add_job(job_4.id, job_4.num_exes)
        if message.can_fit_more():
            message.add_job(job_5.id, job_5.num_exes)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should have been good (max_tries increased)
        self.assertEqual(jobs[0].max_tries, 6)
        # Job 2 had mismatched exe_num
        self.assertEqual(jobs[1].max_tries, 3)
        # Job 3 was already COMPLETED
        self.assertEqual(jobs[2].max_tries, 3)
        # Job 4 can't be re-queued since it had never been queued yet
        self.assertEqual(jobs[3].max_tries, 3)
        # Job 5 can't be re-queued since it had never been queued yet
        self.assertEqual(jobs[4].max_tries, 3)
        # Job 1 is only job that should be included in message to be queued
        self.assertEqual(len(message.new_messages), 2)
        queued_jobs_msg = message.new_messages[0]
        self.assertEqual(queued_jobs_msg.type, 'queued_jobs')
        self.assertListEqual(queued_jobs_msg._queued_jobs, [QueuedJob(job_1.id, job_1.num_exes)])
        self.assertEqual(queued_jobs_msg.priority, 101)
        # Job 5 is only job that should be included in message to uncancel
        uncancel_jobs_msg = message.new_messages[1]
        self.assertEqual(uncancel_jobs_msg.type, 'uncancel_jobs')
        self.assertListEqual(uncancel_jobs_msg._job_ids, [job_5.id])

        # Test executing message again
        message.new_messages = []
        result = message.execute()
        self.assertTrue(result)

        # All results should be the same
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should have been good (max_tries increased)
        self.assertEqual(jobs[0].max_tries, 6)
        # Job 2 had mismatched exe_num
        self.assertEqual(jobs[1].max_tries, 3)
        # Job 3 was already COMPLETED
        self.assertEqual(jobs[2].max_tries, 3)
        # Job 4 can't be re-queued since it had never been queued yet
        self.assertEqual(jobs[3].max_tries, 3)
        # Job 5 can't be re-queued since it had never been queued yet
        self.assertEqual(jobs[4].max_tries, 3)
        # Job 1 is only job that should be included in message to be queued
        self.assertEqual(len(message.new_messages), 2)
        queued_jobs_msg = message.new_messages[0]
        self.assertEqual(queued_jobs_msg.type, 'queued_jobs')
        self.assertListEqual(queued_jobs_msg._queued_jobs, [QueuedJob(job_1.id, job_1.num_exes)])
        self.assertEqual(queued_jobs_msg.priority, 101)
        # Job 5 is only job that should be included in message to uncancel
        uncancel_jobs_msg = message.new_messages[1]
        self.assertEqual(uncancel_jobs_msg.type, 'uncancel_jobs')
        self.assertListEqual(uncancel_jobs_msg._job_ids, [job_5.id])
