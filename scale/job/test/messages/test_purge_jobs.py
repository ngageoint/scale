from __future__ import unicode_literals

from datetime import datetime as dt
import django
from django.test import TransactionTestCase

from job.messages.purge_jobs import PurgeJobs
from job.models import Job, JobExecution
from job.test import utils as job_test_utils


class TestPurgeJobs(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a PurgeJobs message to and from JSON"""

        job_exe = job_test_utils.create_job_exe(status='COMPLETED')
        job = job_exe.job

        # Add job to message
        message = PurgeJobs()
        message.job_id = job.id
        message.status_change = dt.utcnow()

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = PurgeJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        self.assertFalse(Job.objects.filter(id=job.id))

    def test_execute(self):
        """Tests calling PurgeJobs.execute() successfully"""

        job_exe = job_test_utils.create_job_exe(status='COMPLETED')
        job = job_exe.job

        # Add job to message
        message = PurgeJobs()
        message.job_id = job.id
        message.status_change = dt.utcnow()

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check that job is deleted
        self.assertFalse(Job.objects.filter(id=job.id))
