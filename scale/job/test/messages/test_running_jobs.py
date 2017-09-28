from __future__ import unicode_literals

import django
from django.utils.timezone import now
from django.test import TransactionTestCase

from job.messages.running_jobs import RunningJobs
from job.models import Job
from job.test import utils as job_test_utils
from node.test import utils as node_test_utils


class TestRunningJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a RunningJobs message to and from JSON"""

        node_1 = node_test_utils.create_node()
        node_2 = node_test_utils.create_node()
        job_1 = job_test_utils.create_job(num_exes=1, status='QUEUED')
        job_2 = job_test_utils.create_job(num_exes=2, status='QUEUED')
        job_3 = job_test_utils.create_job(num_exes=10, status='QUEUED')
        job_4 = job_test_utils.create_job(num_exes=2, status='QUEUED')
        job_5 = job_test_utils.create_job(num_exes=1, status='QUEUED')
        job_ids = [job_1.id, job_2.id, job_3.id, job_4.id, job_5.id]

        # Add jobs to message
        started = now()
        message = RunningJobs(started)
        if message.can_fit_more():
            message.add_running_job(job_1.id, job_1.num_exes, node_1.id)
        if message.can_fit_more():
            message.add_running_job(job_2.id, job_2.num_exes, node_1.id)
        if message.can_fit_more():
            message.add_running_job(job_3.id, job_3.num_exes, node_2.id)
        if message.can_fit_more():
            message.add_running_job(job_4.id, job_4.num_exes, node_2.id)
        if message.can_fit_more():
            message.add_running_job(job_5.id, job_5.num_exes, node_2.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = RunningJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        self.assertEqual(jobs[0].status, 'RUNNING')
        self.assertEqual(jobs[0].started, started)
        self.assertEqual(jobs[0].node_id, node_1.id)
        self.assertEqual(jobs[1].status, 'RUNNING')
        self.assertEqual(jobs[1].started, started)
        self.assertEqual(jobs[1].node_id, node_1.id)
        self.assertEqual(jobs[2].status, 'RUNNING')
        self.assertEqual(jobs[2].started, started)
        self.assertEqual(jobs[2].node_id, node_2.id)
        self.assertEqual(jobs[3].status, 'RUNNING')
        self.assertEqual(jobs[3].started, started)
        self.assertEqual(jobs[3].node_id, node_2.id)
        self.assertEqual(jobs[4].status, 'RUNNING')
        self.assertEqual(jobs[4].started, started)
        self.assertEqual(jobs[4].node_id, node_2.id)

    def test_execute(self):
        """Tests calling RunningJobs.execute() successfully"""

        node_1 = node_test_utils.create_node()
        node_2 = node_test_utils.create_node()
        job_1 = job_test_utils.create_job(num_exes=1, status='QUEUED')
        job_2 = job_test_utils.create_job(num_exes=2, status='QUEUED')
        job_3 = job_test_utils.create_job(num_exes=1, status='COMPLETED')
        job_4 = job_test_utils.create_job(num_exes=1, status='FAILED')
        job_5 = job_test_utils.create_job(num_exes=1, status='CANCELED')
        job_ids = [job_1.id, job_2.id, job_3.id, job_4.id, job_5.id]

        # Add jobs to message
        started = now()
        message = RunningJobs(started)
        if message.can_fit_more():
            message.add_running_job(job_1.id, job_1.num_exes, node_1.id)
        if message.can_fit_more():
            message.add_running_job(job_2.id, 1, node_1.id)  # This message is for the first execution number
        if message.can_fit_more():
            message.add_running_job(job_3.id, job_3.num_exes, node_2.id)
        if message.can_fit_more():
            message.add_running_job(job_4.id, job_4.num_exes, node_2.id)
        if message.can_fit_more():
            message.add_running_job(job_5.id, job_5.num_exes, node_2.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        jobs = Job.objects.filter(id__in=job_ids).order_by('id')
        # Job 1 should have been successfully updated to RUNNING
        self.assertEqual(jobs[0].status, 'RUNNING')
        self.assertEqual(jobs[0].started, started)
        self.assertEqual(jobs[0].node_id, node_1.id)
        # Job 2 should not be updated since it has already moved on to exe_num 2
        self.assertEqual(jobs[1].status, 'QUEUED')
        self.assertIsNone(jobs[1].started)
        self.assertIsNone(jobs[1].node_id)
        # Job 3 should update its node, but not status since it is already COMPLETED
        self.assertEqual(jobs[2].status, 'COMPLETED')
        self.assertEqual(jobs[2].started, started)
        self.assertEqual(jobs[2].node_id, node_2.id)
        # Job 4 should update its node, but not status since it is already FAILED
        self.assertEqual(jobs[3].status, 'FAILED')
        self.assertEqual(jobs[3].started, started)
        self.assertEqual(jobs[3].node_id, node_2.id)
        # Job 5 should update its node, but not status since it is already CANCELED
        self.assertEqual(jobs[4].status, 'CANCELED')
        self.assertEqual(jobs[4].started, started)
        self.assertEqual(jobs[4].node_id, node_2.id)
