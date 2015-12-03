#@PydevCodeAnalysisIgnore
import django
from django.test import TestCase

import job.test.utils as job_test_utils
from queue.models import QueueDepthByJobType
from queue.queue_depth_processor import QueueDepthProcessor


# TODO: Remove this once the UI migrates to /load
class TestQueueDepthProcessor(TestCase):

    def setUp(self):
        django.setup()

        self.processor = QueueDepthProcessor()

        job_test_utils.create_job(status=u'QUEUED')

    def test_queue_depth_processor(self):
        '''This method tests the Queue Depth Processor'''
        event = job_test_utils.create_clock_event()
        self.processor.process_event(event)

        queue_depth_values = QueueDepthByJobType.objects.values()
        self.assertEqual(queue_depth_values.count(), 1)
