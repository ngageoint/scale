from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from job.messages.publish_job import PublishJob
from job.test import utils as job_test_utils
from product.test import utils as product_test_utils
from storage.models import ScaleFile


class TestPublishJob(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a PublishJob message to and from JSON"""

        job_exe = job_test_utils.create_job_exe(status='COMPLETED')
        job = job_exe.job

        product_1 = product_test_utils.create_product(job_exe=job_exe)
        product_2 = product_test_utils.create_product(job_exe=job_exe)

        # Add job to message
        message = PublishJob()
        message.job_id = job.id

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = PublishJob.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        for scale_file in ScaleFile.objects.filter(id__in=[product_1.id, product_2.id]):
            self.assertTrue(scale_file.is_published)

    def test_execute(self):
        """Tests calling PublishJob.execute() successfully"""

        job_exe = job_test_utils.create_job_exe(status='COMPLETED')
        job = job_exe.job

        product_1 = product_test_utils.create_product(job_exe=job_exe)
        product_2 = product_test_utils.create_product(job_exe=job_exe)

        # Add job to message
        message = PublishJob()
        message.job_id = job.id

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check that products are published
        for scale_file in ScaleFile.objects.filter(id__in=[product_1.id, product_2.id]):
            self.assertTrue(scale_file.is_published)
