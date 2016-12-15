from __future__ import unicode_literals

import django
from django.test import TestCase

import job.test.utils as job_test_utils
from queue.models import JobLoad
from queue.job_load import JobLoadProcessor


class TestJobLoadProcessor(TestCase):

    def setUp(self):
        django.setup()

        self.processor = JobLoadProcessor()

        job_test_utils.create_job(status='QUEUED')

    def test_process_event(self):
        """This method tests the Job Load Processor"""
        event = job_test_utils.create_clock_event()
        self.processor.process_event(event)

        job_loads = JobLoad.objects.values()
        self.assertEqual(job_loads.count(), 1)
