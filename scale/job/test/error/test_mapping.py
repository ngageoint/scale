from __future__ import unicode_literals
from __future__ import absolute_import

import django
from django.test import TestCase

from error.models import Error
from job.error.error import JobError
from job.error.mapping import JobErrorMapping


class TestJobErrorMapping(TestCase):
    """Tests the JobErrorMapping class"""

    def setUp(self):
        django.setup()

    def test_save_models(self):
        """Tests calling JobErrorMapping.save_models() successfully"""

        job_type_name = 'test-job'
        mapping = JobErrorMapping(job_type_name)

        error_1 = JobError(job_type_name, 'mapped_error_1', title='Title', description='Description',
                           category='ALGORITHM')
        error_2 = JobError(job_type_name, 'mapped_error_2', category='DATA')
        mapping.add_mapping(1, error_1)
        mapping.add_mapping(2, error_2)

        # Make sure error models are created successfully
        mapping.save_models()
        self.assertEqual(Error.objects.filter(job_type_name=job_type_name).count(), 2)

        # Make some changes
        error_1.description = 'New description'
        error_2.category = 'ALGORITHM'

        # Make sure error models are updated successfully
        mapping.save_models()
        self.assertEqual(Error.objects.get(name='mapped_error_1').description, 'New description')
        self.assertEqual(Error.objects.get(name='mapped_error_2').category, 'ALGORITHM')
