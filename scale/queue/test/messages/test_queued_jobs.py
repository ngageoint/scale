from __future__ import unicode_literals

import datetime

import django
from django.utils.timezone import now
from django.test import TransactionTestCase

from job.configuration.data.job_data import JobData
from job.models import Job
from job.test import utils as job_test_utils
from queue.messages.queued_jobs import QueuedJobs
from queue.models import Queue


class TestQueuedJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a QueuedJobs message to and from JSON"""

        data = JobData()
        job_1 = job_test_utils.create_job(num_exes=0, status='PENDING', data=data.get_dict())
        job_2 = job_test_utils.create_job(num_exes=1, status='FAILED', data=data.get_dict())
        job_3 = job_test_utils.create_job(num_exes=1, status='COMPLETED', data=data.get_dict())
        job_ids = [job_1.id, job_2.id, job_3.id]

        # Add jobs to message
        message = QueuedJobs()
        message.priority = 1
        if message.can_fit_more():
            message.add_job(job_1.id, job_1.num_exes)
        if message.can_fit_more():
            message.add_job(job_2.id, job_2.num_exes - 1)  # Mismatched exe_num
        if message.can_fit_more():
            message.add_job(job_3.id, job_3.num_exes)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = QueuedJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        self.assertEqual(jobs[0].status, 'QUEUED')
        self.assertEqual(jobs[0].num_exes, 1)
        self.assertEqual(jobs[1].status, 'FAILED')
        self.assertEqual(jobs[1].num_exes, 1)
        self.assertEqual(jobs[2].status, 'COMPLETED')
        self.assertEqual(jobs[2].num_exes, 1)
        # Ensure priority is correctly set
        queue = Queue.objects.get(job_id=job_1.id)
        self.assertEqual(queue.priority, 1)

    def test_execute(self):
        """Tests calling QueuedJobs.execute() successfully"""

        data = JobData()
        job_1 = job_test_utils.create_job(num_exes=0, status='PENDING', data=data.get_dict())
        job_2 = job_test_utils.create_job(num_exes=1, status='FAILED', data=data.get_dict())
        job_3 = job_test_utils.create_job(num_exes=1, status='RUNNING', data=data.get_dict())
        job_4 = job_test_utils.create_job(num_exes=0, status='CANCELED', data=data.get_dict())
        job_5 = job_test_utils.create_job(num_exes=1, status='QUEUED', data=data.get_dict())
        job_6 = job_test_utils.create_job(num_exes=1, status='COMPLETED', data=data.get_dict())
        job_7 = job_test_utils.create_job(num_exes=1, status='RUNNING', data=data.get_dict())
        job_8 = job_test_utils.create_job(num_exes=0, status='CANCELED')
        job_ids = [job_1.id, job_2.id, job_3.id, job_4.id, job_5.id, job_6.id, job_7.id, job_8.id]

        # Add jobs to message
        message = QueuedJobs()
        message.priority = 101
        if message.can_fit_more():
            message.add_job(job_1.id, job_1.num_exes)
        if message.can_fit_more():
            message.add_job(job_2.id, job_2.num_exes)
        if message.can_fit_more():
            message.add_job(job_3.id, job_3.num_exes)
        if message.can_fit_more():
            message.add_job(job_4.id, job_4.num_exes)
        if message.can_fit_more():
            message.add_job(job_5.id, job_5.num_exes)
        if message.can_fit_more():
            message.add_job(job_6.id, job_6.num_exes)
        if message.can_fit_more():
            message.add_job(job_7.id, job_7.num_exes - 1)  # Mismatched exe_num
        if message.can_fit_more():
            message.add_job(job_8.id, job_8.num_exes)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should have been successfully QUEUED
        self.assertEqual(jobs[0].status, 'QUEUED')
        self.assertEqual(jobs[0].num_exes, 1)
        # Job 2 should have been successfully QUEUED
        self.assertEqual(jobs[1].status, 'QUEUED')
        self.assertEqual(jobs[1].num_exes, 2)
        # Job 3 should have been successfully QUEUED
        self.assertEqual(jobs[2].status, 'QUEUED')
        self.assertEqual(jobs[2].num_exes, 2)
        # Job 4 should have been successfully QUEUED
        self.assertEqual(jobs[3].status, 'QUEUED')
        self.assertEqual(jobs[3].num_exes, 1)
        # Job 5 should have been successfully QUEUED
        self.assertEqual(jobs[4].status, 'QUEUED')
        self.assertEqual(jobs[4].num_exes, 2)
        # Job 6 should not have been queued since it is already completed
        self.assertEqual(jobs[5].status, 'COMPLETED')
        self.assertEqual(jobs[5].num_exes, 1)
        # Job 7 should not have been queued since it is an old message
        self.assertEqual(jobs[6].status, 'RUNNING')
        self.assertEqual(jobs[6].num_exes, 1)
        # Job 8 should not have been queued since it doesn't have any input data
        self.assertEqual(jobs[7].status, 'CANCELED')
        self.assertEqual(jobs[7].num_exes, 0)
