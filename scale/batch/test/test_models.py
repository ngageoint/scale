from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

import recipe.test.utils as recipe_test_utils
from batch.configuration.definition.batch_definition import BatchDefinition
from batch.models import Batch
from job.models import Job


class TestBatchManager(TransactionTestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

        self.recipe = recipe_test_utils.create_recipe()

    def test_successful(self):
        """Tests calling BatchManager.create_batch() successfully"""

        batch = Batch.objects.create_batch(self.recipe.recipe_type, BatchDefinition({}), 'Test', 'test')

        batch = Batch.objects.get(pk=batch.id)

        self.assertEqual(batch.title, 'Test')
        self.assertEqual(batch.description, 'test')
        self.assertEqual(batch.status, 'PENDING')
        self.assertEqual(batch.recipe_type, self.recipe.recipe_type)

        self.assertEqual(len(Job.objects.filter(job_type__name='scale-batch')), 1)
