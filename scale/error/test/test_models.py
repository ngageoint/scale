import django
from django.test import TestCase

from error.models import get_job_error, Error


class Test_get_job_error(TestCase):

    def setUp(self):
        django.setup()

    def test_get_job_error(self):
        """Tests successfully calling get_job_error()"""

        job_type_name = 'job_type_1'
        error_model = Error()
        error_model.name = 'error_1'
        error_model.job_type_name = job_type_name
        error_model.title = 'Error 1'
        error_model.description = 'This is a description'
        error_model.category = 'ALGORITHM'
        Error.objects.save_job_error_models(job_type_name, [error_model])

        # Test retrieving error model, which will load it into the cache
        error_model = get_job_error(job_type_name, 'error_1')
        self.assertEqual(error_model.name, 'error_1')


class TestErrorManager(TestCase):

    def setUp(self):
        django.setup()

    def test_save_job_error_models(self):
        """Tests successfully calling save_job_error_models()"""

        job_type_name = 'job_type_1_for_error_test'
        error_model_1 = Error()
        error_model_1.name = 'error_1'
        error_model_1.job_type_name = job_type_name
        error_model_1.title = 'Error 1'
        error_model_1.description = 'This is a description'
        error_model_1.category = 'ALGORITHM'
        error_model_2 = Error()
        error_model_2.name = 'error_2'
        error_model_2.job_type_name = job_type_name

        # Test saving models for the first time
        Error.objects.save_job_error_models(job_type_name, [error_model_1, error_model_2])
        self.assertEqual(Error.objects.filter(job_type_name=job_type_name).count(), 2)

        # Make some changes
        error_model_1.description = 'New description'
        error_model_2.category = 'DATA'

        # Test updating models
        Error.objects.save_job_error_models(job_type_name, [error_model_1, error_model_2])
        self.assertEqual(Error.objects.get(name='error_1').description, 'New description')
        self.assertEqual(Error.objects.get(name='error_2').category, 'DATA')
