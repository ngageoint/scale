from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from job.error.error import JobError


class TestErrorModel(TransactionTestCase):
    """Tests functions in the job error module."""

    def setUp(self):
        django.setup()
        
    def test_create_error_model(self):
        """Validate that a complete Error model is created using JobError
        """
        job_type_name = 'test-job'
        name = 'bad-data'
        title = 'Bad Data'
        description = 'Error received when bad data is detected'
        category = 'DATA'
        
        error = JobError(job_type_name, name, title, description, category)
        model = error.create_model()
        self.assertEqual(model.name, name)
        self.assertEqual(model.title, title)
        self.assertEqual(model.description, description)
        self.assertEqual(model.category, category)
        self.assertEqual(model.job_type_name, job_type_name)
