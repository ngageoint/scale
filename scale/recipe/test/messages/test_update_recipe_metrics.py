from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.test import utils as batch_test_utils
from job.models import Job
from job.test import utils as job_test_utils
from recipe.messages.update_recipe_metrics import UpdateRecipeMetrics
from recipe.models import Recipe, RecipeNode
from recipe.test import utils as recipe_test_utils


class TestUpdateRecipes(TestCase):

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
        recipe_node_1 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_1)
        recipe_node_2 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_2)
        recipe_node_3 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_3)
        recipe_node_4 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_4)
        recipe_node_5 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_5)
        RecipeNode.objects.bulk_create([recipe_node_1, recipe_node_2, recipe_node_3, recipe_node_4, recipe_node_5])

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
        recipe_node_1 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_1)
        recipe_node_2 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_2)
        recipe_node_3 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_3)
        recipe_node_4 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_4)
        recipe_node_5 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_5)
        RecipeNode.objects.bulk_create([recipe_node_1, recipe_node_2, recipe_node_3, recipe_node_4, recipe_node_5])

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
        recipe_node_6 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_6)
        recipe_node_7 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_7)
        recipe_node_8 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_8)
        recipe_node_9 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_9)
        recipe_node_10 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_10)
        recipe_node_11 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_11)
        recipe_node_12 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_12)
        recipe_node_13 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_13)
        recipe_node_14 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_14)
        RecipeNode.objects.bulk_create([recipe_node_6, recipe_node_7, recipe_node_8, recipe_node_9, recipe_node_10,
                                        recipe_node_11, recipe_node_12, recipe_node_13, recipe_node_14])

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

    def test_execute_with_sub_recipes(self):
        """Tests calling UpdateRecipeMetrics.execute() successfully with sub-recipes"""

        recipe_1 = recipe_test_utils.create_recipe()
        batch = batch_test_utils.create_batch()
        recipe_2 = recipe_test_utils.create_recipe(batch=batch)
        # Recipe 1 jobs
        job_1 = job_test_utils.create_job(status='FAILED', save=False)
        job_2 = job_test_utils.create_job(status='CANCELED', save=False)
        job_3 = job_test_utils.create_job(status='BLOCKED', save=False)
        job_4 = job_test_utils.create_job(status='BLOCKED', save=False)
        job_5 = job_test_utils.create_job(status='COMPLETED', save=False)
        # Recipe 2 jobs
        job_6 = job_test_utils.create_job(status='COMPLETED', save=False)
        job_7 = job_test_utils.create_job(status='COMPLETED', save=False)
        job_8 = job_test_utils.create_job(status='RUNNING', save=False)
        job_9 = job_test_utils.create_job(status='QUEUED', save=False)
        job_10 = job_test_utils.create_job(status='PENDING', save=False)
        job_11 = job_test_utils.create_job(status='PENDING', save=False)
        job_12 = job_test_utils.create_job(status='PENDING', save=False)
        job_13 = job_test_utils.create_job(status='CANCELED', save=False)
        job_14 = job_test_utils.create_job(status='BLOCKED', save=False)
        Job.objects.bulk_create([job_1, job_2, job_3, job_4, job_5, job_6, job_7, job_8, job_9, job_10, job_11, job_12,
                                 job_13, job_14])

        # Recipe 1 sub-recipes
        sub_recipe_1 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_1.jobs_total = 26
        sub_recipe_1.jobs_pending = 3
        sub_recipe_1.jobs_blocked = 4
        sub_recipe_1.jobs_queued = 5
        sub_recipe_1.jobs_running = 1
        sub_recipe_1.jobs_failed = 2
        sub_recipe_1.jobs_completed = 3
        sub_recipe_1.jobs_canceled = 8
        sub_recipe_1.is_completed = False
        sub_recipe_2 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_2.jobs_total = 30
        sub_recipe_2.jobs_completed = 30
        sub_recipe_2.is_completed = True
        # Recipe 2 sub-recipes
        sub_recipe_3 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_3.jobs_total = 21
        sub_recipe_3.jobs_pending = 2
        sub_recipe_3.jobs_blocked = 5
        sub_recipe_3.jobs_queued = 0
        sub_recipe_3.jobs_running = 3
        sub_recipe_3.jobs_failed = 2
        sub_recipe_3.jobs_completed = 8
        sub_recipe_3.jobs_canceled = 1
        sub_recipe_3.is_completed = False
        sub_recipe_4 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_4.jobs_total = 7
        sub_recipe_4.jobs_completed = 7
        sub_recipe_4.is_completed = True
        sub_recipe_5 = recipe_test_utils.create_recipe(save=False)
        sub_recipe_5.jobs_total = 12
        sub_recipe_5.jobs_completed = 12
        sub_recipe_5.is_completed = True
        Recipe.objects.bulk_create([sub_recipe_1, sub_recipe_2, sub_recipe_3, sub_recipe_4, sub_recipe_5])
        # Recipe 1 nodes
        recipe_node_1 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_1)
        recipe_node_2 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_2)
        recipe_node_3 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_3)
        recipe_node_4 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_4)
        recipe_node_5 = recipe_test_utils.create_recipe_node(recipe=recipe_1, job=job_5)
        recipe_node_6 = recipe_test_utils.create_recipe_node(recipe=recipe_1, sub_recipe=sub_recipe_1)
        recipe_node_7 = recipe_test_utils.create_recipe_node(recipe=recipe_1, sub_recipe=sub_recipe_2)
        # Recipe 2 nodes
        recipe_node_8 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_6)
        recipe_node_9 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_7)
        recipe_node_10 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_8)
        recipe_node_11 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_9)
        recipe_node_12 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_10)
        recipe_node_13 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_11)
        recipe_node_14 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_12)
        recipe_node_15 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_13)
        recipe_node_16 = recipe_test_utils.create_recipe_node(recipe=recipe_2, job=job_14)
        recipe_node_17 = recipe_test_utils.create_recipe_node(recipe=recipe_2, sub_recipe=sub_recipe_3)
        recipe_node_18 = recipe_test_utils.create_recipe_node(recipe=recipe_2, sub_recipe=sub_recipe_4)
        recipe_node_19 = recipe_test_utils.create_recipe_node(recipe=recipe_2, sub_recipe=sub_recipe_5)
        RecipeNode.objects.bulk_create([recipe_node_1, recipe_node_2, recipe_node_3, recipe_node_4, recipe_node_5,
                                        recipe_node_6, recipe_node_7, recipe_node_8, recipe_node_9, recipe_node_10,
                                        recipe_node_11, recipe_node_12, recipe_node_13, recipe_node_14, recipe_node_15,
                                        recipe_node_16, recipe_node_17, recipe_node_18, recipe_node_19])

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
        self.assertEqual(recipe_1.jobs_total, 61)
        self.assertEqual(recipe_1.jobs_pending, 3)
        self.assertEqual(recipe_1.jobs_blocked, 6)
        self.assertEqual(recipe_1.jobs_queued, 5)
        self.assertEqual(recipe_1.jobs_running, 1)
        self.assertEqual(recipe_1.jobs_failed, 3)
        self.assertEqual(recipe_1.jobs_completed, 34)
        self.assertEqual(recipe_1.jobs_canceled, 9)
        self.assertEqual(recipe_1.sub_recipes_total, 2)
        self.assertEqual(recipe_1.sub_recipes_completed, 1)

        recipe_2 = Recipe.objects.get(id=recipe_2.id)
        self.assertEqual(recipe_2.jobs_total, 49)
        self.assertEqual(recipe_2.jobs_pending, 5)
        self.assertEqual(recipe_2.jobs_blocked, 6)
        self.assertEqual(recipe_2.jobs_queued, 1)
        self.assertEqual(recipe_2.jobs_running, 4)
        self.assertEqual(recipe_2.jobs_failed, 2)
        self.assertEqual(recipe_2.jobs_completed, 29)
        self.assertEqual(recipe_2.jobs_canceled, 2)
        self.assertEqual(recipe_2.sub_recipes_total, 3)
        self.assertEqual(recipe_2.sub_recipes_completed, 2)

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
        self.assertEqual(recipe_1.jobs_total, 61)
        self.assertEqual(recipe_1.jobs_pending, 3)
        self.assertEqual(recipe_1.jobs_blocked, 6)
        self.assertEqual(recipe_1.jobs_queued, 5)
        self.assertEqual(recipe_1.jobs_running, 1)
        self.assertEqual(recipe_1.jobs_failed, 3)
        self.assertEqual(recipe_1.jobs_completed, 34)
        self.assertEqual(recipe_1.jobs_canceled, 9)
        self.assertEqual(recipe_1.sub_recipes_total, 2)
        self.assertEqual(recipe_1.sub_recipes_completed, 1)

        recipe_2 = Recipe.objects.get(id=recipe_2.id)
        self.assertEqual(recipe_2.jobs_total, 49)
        self.assertEqual(recipe_2.jobs_pending, 5)
        self.assertEqual(recipe_2.jobs_blocked, 6)
        self.assertEqual(recipe_2.jobs_queued, 1)
        self.assertEqual(recipe_2.jobs_running, 4)
        self.assertEqual(recipe_2.jobs_failed, 2)
        self.assertEqual(recipe_2.jobs_completed, 29)
        self.assertEqual(recipe_2.jobs_canceled, 2)
        self.assertEqual(recipe_2.sub_recipes_total, 3)
        self.assertEqual(recipe_2.sub_recipes_completed, 2)

        # Make sure message is created to update batch metrics
        self.assertEqual(len(message.new_messages), 1)
        msg = message.new_messages[0]
        self.assertEqual(msg.type, 'update_batch_metrics')
        self.assertListEqual(msg._batch_ids, [batch.id])

    def test_execute_with_top_level_recipe(self):
        """Tests calling UpdateRecipeMetrics.execute() successfully where a message needs to be sent to update a
        top-level recipe
        """

        batch = batch_test_utils.create_batch()
        top_recipe = recipe_test_utils.create_recipe(batch=batch)
        recipe = recipe_test_utils.create_recipe(batch=batch)
        recipe.recipe = top_recipe
        recipe.save()
        recipe_node_1 = recipe_test_utils.create_recipe_node(recipe=top_recipe, sub_recipe=recipe)

        # Recipe jobs
        job_1 = job_test_utils.create_job(status='FAILED', save=False)
        job_2 = job_test_utils.create_job(status='CANCELED', save=False)
        job_3 = job_test_utils.create_job(status='BLOCKED', save=False)
        job_4 = job_test_utils.create_job(status='BLOCKED', save=False)
        job_5 = job_test_utils.create_job(status='COMPLETED', save=False)
        Job.objects.bulk_create([job_1, job_2, job_3, job_4, job_5])

        # Recipe nodes
        recipe_node_2 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_1)
        recipe_node_3 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_2)
        recipe_node_4 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_3)
        recipe_node_5 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_4)
        recipe_node_6 = recipe_test_utils.create_recipe_node(recipe=recipe, job=job_5)
        RecipeNode.objects.bulk_create([recipe_node_1, recipe_node_2, recipe_node_3, recipe_node_4, recipe_node_5,
                                        recipe_node_6])

        # Add recipes to message
        message = UpdateRecipeMetrics()
        if message.can_fit_more():
            message.add_recipe(recipe.id)

        # Execute message
        result = message.execute()
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
        self.assertEqual(recipe.sub_recipes_total, 0)
        self.assertEqual(recipe.sub_recipes_completed, 0)

        # Make sure message is created to update top-level recipe metrics
        # There should be no message to update batch metrics since we did not update a top-level recipe
        self.assertEqual(len(message.new_messages), 1)
        msg = message.new_messages[0]
        self.assertEqual(msg.type, 'update_recipe_metrics')
        self.assertListEqual(msg._recipe_ids, [top_recipe.id])

        # Test executing message again
        message_json_dict = message.to_json()
        message = UpdateRecipeMetrics.from_json(message_json_dict)
        result = message.execute()
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
        self.assertEqual(recipe.sub_recipes_total, 0)
        self.assertEqual(recipe.sub_recipes_completed, 0)

        # Make sure message is created to update top-level recipe metrics
        # There should be no message to update batch metrics since we did not update a top-level recipe
        self.assertEqual(len(message.new_messages), 1)
        msg = message.new_messages[0]
        self.assertEqual(msg.type, 'update_recipe_metrics')
        self.assertListEqual(msg._recipe_ids, [top_recipe.id])
