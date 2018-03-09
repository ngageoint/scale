from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.test import utils as batch_test_utils
from job.test import utils as job_test_utils
from recipe.messages.update_recipe_metrics import UpdateRecipeMetrics
from recipe.models import Recipe
from recipe.test import utils as recipe_test_utils


class TestUpdateRecipes(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a UpdateRecipeMetrics message to and from JSON"""

        recipe = recipe_test_utils.create_recipe()
        job_1 = job_test_utils.create_job(status='FAILED')
        job_2 = job_test_utils.create_job(status='CANCELED')
        job_3 = job_test_utils.create_job(status='BLOCKED')
        job_4 = job_test_utils.create_job(status='BLOCKED')
        job_5 = job_test_utils.create_job(status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe, job=job_1)
        recipe_test_utils.create_recipe_job(recipe=recipe, job=job_2)
        recipe_test_utils.create_recipe_job(recipe=recipe, job=job_3)
        recipe_test_utils.create_recipe_job(recipe=recipe, job=job_4)
        recipe_test_utils.create_recipe_job(recipe=recipe, job=job_5)

        # Add recipe to message
        message = UpdateRecipeMetrics()
        if message.can_fit_more():
            message.add_recipe(recipe.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = UpdateRecipeMetrics.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        recipe = Recipe.objects.get(id=recipe.id)
        self.assertEqual(recipe.jobs_total, 5)
        self.assertEqual(recipe.jobs_pending, 0)
        self.assertEqual(recipe.jobs_blocked, 2)
        self.assertEqual(recipe.jobs_queued, 0)
        self.assertEqual(recipe.jobs_running, 0)
        self.assertEqual(recipe.jobs_failed, 1)
        self.assertEqual(recipe.jobs_completed, 1)
        self.assertEqual(recipe.jobs_canceled, 1)

    def test_execute(self):
        """Tests calling UpdateRecipeMetrics.execute() successfully"""

        recipe_1 = recipe_test_utils.create_recipe()
        job_1 = job_test_utils.create_job(status='FAILED')
        job_2 = job_test_utils.create_job(status='CANCELED')
        job_3 = job_test_utils.create_job(status='BLOCKED')
        job_4 = job_test_utils.create_job(status='BLOCKED')
        job_5 = job_test_utils.create_job(status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_1)
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_2)
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_3)
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_4)
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job=job_5)

        batch = batch_test_utils.create_batch()
        recipe_2 = recipe_test_utils.create_recipe(batch=batch)
        job_6 = job_test_utils.create_job(status='COMPLETED')
        job_7 = job_test_utils.create_job(status='COMPLETED')
        job_8 = job_test_utils.create_job(status='RUNNING')
        job_9 = job_test_utils.create_job(status='QUEUED')
        job_10 = job_test_utils.create_job(status='PENDING')
        job_11 = job_test_utils.create_job(status='PENDING')
        job_12 = job_test_utils.create_job(status='PENDING')
        job_13 = job_test_utils.create_job(status='CANCELED')
        job_14 = job_test_utils.create_job(status='BLOCKED')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_6)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_7)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_8)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_9)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_10)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_11)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_12)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_13)
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job=job_14)

        # Add recipes to message
        message = UpdateRecipeMetrics()
        if message.can_fit_more():
            message.add_recipe(recipe_1.id)
        if message.can_fit_more():
            message.add_recipe(recipe_2.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        recipe_1 = Recipe.objects.get(id=recipe_1.id)
        self.assertEqual(recipe_1.jobs_total, 5)
        self.assertEqual(recipe_1.jobs_pending, 0)
        self.assertEqual(recipe_1.jobs_blocked, 2)
        self.assertEqual(recipe_1.jobs_queued, 0)
        self.assertEqual(recipe_1.jobs_running, 0)
        self.assertEqual(recipe_1.jobs_failed, 1)
        self.assertEqual(recipe_1.jobs_completed, 1)
        self.assertEqual(recipe_1.jobs_canceled, 1)

        recipe_2 = Recipe.objects.get(id=recipe_2.id)
        self.assertEqual(recipe_2.jobs_total, 9)
        self.assertEqual(recipe_2.jobs_pending, 3)
        self.assertEqual(recipe_2.jobs_blocked, 1)
        self.assertEqual(recipe_2.jobs_queued, 1)
        self.assertEqual(recipe_2.jobs_running, 1)
        self.assertEqual(recipe_2.jobs_failed, 0)
        self.assertEqual(recipe_2.jobs_completed, 2)
        self.assertEqual(recipe_2.jobs_canceled, 1)

        # Make sure message is created to update batch metrics
        self.assertEqual(len(message.new_messages), 1)
        msg = message.new_messages[0]
        self.assertEqual(msg.type, 'update_batch_metrics')
        self.assertListEqual(msg._batch_ids, [batch.id])

        # Test executing message again
        message_json_dict = message.to_json()
        message = UpdateRecipeMetrics.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        recipe_1 = Recipe.objects.get(id=recipe_1.id)
        self.assertEqual(recipe_1.jobs_total, 5)
        self.assertEqual(recipe_1.jobs_pending, 0)
        self.assertEqual(recipe_1.jobs_blocked, 2)
        self.assertEqual(recipe_1.jobs_queued, 0)
        self.assertEqual(recipe_1.jobs_running, 0)
        self.assertEqual(recipe_1.jobs_failed, 1)
        self.assertEqual(recipe_1.jobs_completed, 1)
        self.assertEqual(recipe_1.jobs_canceled, 1)

        recipe_2 = Recipe.objects.get(id=recipe_2.id)
        self.assertEqual(recipe_2.jobs_total, 9)
        self.assertEqual(recipe_2.jobs_pending, 3)
        self.assertEqual(recipe_2.jobs_blocked, 1)
        self.assertEqual(recipe_2.jobs_queued, 1)
        self.assertEqual(recipe_2.jobs_running, 1)
        self.assertEqual(recipe_2.jobs_failed, 0)
        self.assertEqual(recipe_2.jobs_completed, 2)
        self.assertEqual(recipe_2.jobs_canceled, 1)

        # Make sure message is created to update batch metrics
        self.assertEqual(len(message.new_messages), 1)
        msg = message.new_messages[0]
        self.assertEqual(msg.type, 'update_batch_metrics')
        self.assertListEqual(msg._batch_ids, [batch.id])
