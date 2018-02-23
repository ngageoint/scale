from __future__ import unicode_literals

import datetime

import django
from django.utils.timezone import now
from django.test import TestCase

from job.messages.unpublish_jobs import UnpublishJobs
from job.models import Job
from job.test import utils as job_test_utils
from product.models import ProductFile
from product.test import utils as product_test_utils


class TestUnpublishJobs(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting an UnpublishJobs message to and from JSON"""

        when = now()
        job_exe_1 = job_test_utils.create_job_exe(status='COMPLETED')
        job_exe_2 = job_test_utils.create_job_exe(status='COMPLETED')
        product_1 = product_test_utils.create_product(job_exe=job_exe_1, is_published=True)
        product_2 = product_test_utils.create_product(job_exe=job_exe_2, is_published=True)

        # Add jobs to message
        message = UnpublishJobs()
        message.when = when
        if message.can_fit_more():
            message.add_job(job_exe_1.job_id)
        if message.can_fit_more():
            message.add_job(job_exe_2.job_id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = UnpublishJobs.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        products = ProductFile.objects.filter(id__in=[product_1.id, product_2.id])
        self.assertEqual(len(products), 2)
        self.assertFalse(products[0].is_published)
        self.assertEqual(products[0].unpublished, when)
        self.assertFalse(products[1].is_published)
        self.assertEqual(products[1].unpublished, when)

    def test_execute(self):
        """Tests calling UnpublishJobs.execute() successfully"""

        when = now()
        job_exe_1 = job_test_utils.create_job_exe(status='COMPLETED')
        job_exe_2 = job_test_utils.create_job_exe(status='COMPLETED')
        product_1 = product_test_utils.create_product(job_exe=job_exe_1, is_published=True)
        product_2 = product_test_utils.create_product(job_exe=job_exe_2, is_published=True)

        # Add jobs to message
        message = UnpublishJobs()
        message.when = when
        if message.can_fit_more():
            message.add_job(job_exe_1.job_id)
        if message.can_fit_more():
            message.add_job(job_exe_2.job_id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check that products are unpublished
        products = ProductFile.objects.filter(id__in=[product_1.id, product_2.id])
        self.assertEqual(len(products), 2)
        self.assertFalse(products[0].is_published)
        self.assertEqual(products[0].unpublished, when)
        self.assertFalse(products[1].is_published)
        self.assertEqual(products[1].unpublished, when)
