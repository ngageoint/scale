from __future__ import unicode_literals

import datetime

import django
from django.utils.timezone import now
from django.test import TransactionTestCase

from job.messages.blocked_jobs import BlockedJobs
from job.models import Job
from job.test import utils as job_test_utils


class TestBlockedJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a BlockedJobs message to and from JSON"""

        original_status_change = now()

        job_1 = job_test_utils.create_job(num_exes=0, status='PENDING', last_status_change=original_status_change)
        job_2 = job_test_utils.create_job(num_exes=0, status='BLOCKED', last_status_change=original_status_change)
        job_3 = job_test_utils.create_job(num_exes=0, status='CANCELED', last_status_change=original_status_change)
        job_4 = job_test_utils.create_job(num_exes=1, status='CANCELED', last_status_change=original_status_change)
        job_5 = job_test_utils.create_job(num_exes=1, status='QUEUED', last_status_change=original_status_change)
        job_ids = [job_1.id, job_2.id, job_3.id, job_4.id, job_5.id]

        # Add jobs to message
        status_change = original_status_change + datetime.timedelta(minutes=1)
        message = BlockedJobs()
        message.status_change = status_change
        if message.can_fit_more():
            message.add_job(job_1.id)
        if message.can_fit_more():
            message.add_job(job_2.id)
        if message.can_fit_more():
            message.add_job(job_3.id)
        if message.can_fit_more():
            message.add_job(job_4.id)
        if message.can_fit_more():
            message.add_job(job_5.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = BlockedJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        self.assertEqual(jobs[0].status, 'BLOCKED')
        self.assertEqual(jobs[0].last_status_change, status_change)
        self.assertEqual(jobs[1].status, 'BLOCKED')
        self.assertEqual(jobs[1].last_status_change, original_status_change)
        self.assertEqual(jobs[2].status, 'BLOCKED')
        self.assertEqual(jobs[2].last_status_change, status_change)
        self.assertEqual(jobs[3].status, 'CANCELED')
        self.assertEqual(jobs[3].last_status_change, original_status_change)
        self.assertEqual(jobs[4].status, 'QUEUED')
        self.assertEqual(jobs[4].last_status_change, original_status_change)

    def test_execute(self):
        """Tests calling BlockedJobs.execute() successfully"""

        original_status_change = now()

        job_1 = job_test_utils.create_job(num_exes=0, status='PENDING', last_status_change=original_status_change)
        job_2 = job_test_utils.create_job(num_exes=0, status='BLOCKED', last_status_change=original_status_change)
        job_3 = job_test_utils.create_job(num_exes=0, status='CANCELED', last_status_change=original_status_change)
        job_4 = job_test_utils.create_job(num_exes=1, status='CANCELED', last_status_change=original_status_change)
        job_5 = job_test_utils.create_job(num_exes=1, status='QUEUED', last_status_change=original_status_change)
        job_ids = [job_1.id, job_2.id, job_3.id, job_4.id, job_5.id]

        # Add jobs to message
        status_change = original_status_change + datetime.timedelta(minutes=1)
        message = BlockedJobs()
        message.status_change = status_change
        if message.can_fit_more():
            message.add_job(job_1.id)
        if message.can_fit_more():
            message.add_job(job_2.id)
        if message.can_fit_more():
            message.add_job(job_3.id)
        if message.can_fit_more():
            message.add_job(job_4.id)
        if message.can_fit_more():
            message.add_job(job_5.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should have been successfully updated to BLOCKED
        self.assertEqual(jobs[0].status, 'BLOCKED')
        self.assertEqual(jobs[0].last_status_change, status_change)
        # Job 2 should not have been updated since it was already BLOCKED
        self.assertEqual(jobs[1].status, 'BLOCKED')
        self.assertEqual(jobs[1].last_status_change, original_status_change)
        # Job 3 should have been successfully updated to BLOCKED
        self.assertEqual(jobs[2].status, 'BLOCKED')
        self.assertEqual(jobs[2].last_status_change, status_change)
        # Job 4 should not have been updated since it has previously been queued
        self.assertEqual(jobs[3].status, 'CANCELED')
        self.assertEqual(jobs[3].last_status_change, original_status_change)
        # Job 5 should not have been updated since it has previously been queued
        self.assertEqual(jobs[4].status, 'QUEUED')
        self.assertEqual(jobs[4].last_status_change, original_status_change)
