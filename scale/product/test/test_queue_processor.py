from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch

import job.test.utils as job_test_utils
from product.models import FileAncestryLink
from product.queue_processor import ProductProcessor


class TestProductProcessor(TestCase):
    """Tests handling queue events when job executions change state."""

    def setUp(self):
        django.setup()

        self.processor = ProductProcessor()

        data = {
            'input_data': [{
                'name': 'Param1',
                'file_id': 1,
            }, {
                'name': 'Param2',
                'file_id': 2,
            }]
        }
        self.job = job_test_utils.create_job(data=data)
        self.job_exe = job_test_utils.create_job_exe(job=self.job)

    def test_queued_initial(self):
        """Tests file ancestry links are created for input files when a job is first queued."""
        self.processor.process_queued(self.job_exe, True)

        results = FileAncestryLink.objects.all()
        self.assertEqual(len(results), 2)
        self.assertIsNone(results[0].descendant)
        self.assertIsNone(results[1].descendant)

    def test_queued_repeat(self):
        """Tests nothing is done when a job is queued more than once."""
        self.processor.process_queued(self.job_exe, False)

        self.assertEqual(len(FileAncestryLink.objects.all()), 0)

    @patch('product.queue_processor.ProductFile')
    def test_completed(self, mock_ProductFile):
        """Tests products are published when a job is completed."""
        self.processor.process_completed(self.job_exe)

        self.assertTrue(mock_ProductFile.objects.publish_products.called)
