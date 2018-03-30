from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.definition.definition import BatchDefinition
from batch.messages.create_batch_recipes import create_batch_recipes_message, CreateBatchRecipes
from batch.test import utils as batch_test_utils
from recipe.test import utils as recipe_test_utils


class TestCreateBatchRecipes(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a CreateBatchRecipes message to and from JSON"""

        # Previous batch with three recipes
        prev_batch = batch_test_utils.create_batch()
        recipe_1 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_2 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_3 = recipe_test_utils.create_recipe(batch=prev_batch)

        definition = BatchDefinition()
        definition.prev_batch_id = prev_batch.id
        batch = batch_test_utils.create_batch(definition=definition)

        # Create message
        message = create_batch_recipes_message(batch.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateBatchRecipes.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        # Should be one reprocess_recipes message for the three recipes
        self.assertEqual(len(new_message.new_messages), 1)
        message = new_message.new_messages[0]
        self.assertEqual(message.type, 'reprocess_recipes')
        self.assertSetEqual(set(message._root_recipe_ids), {recipe_1.id, recipe_2.id, recipe_3.id})

    def test_execute(self):
        """Tests calling CreateBatchRecipes.execute() successfully"""

        # Importing module here to patch the max recipe num
        import batch.messages.create_batch_recipes
        batch.messages.create_batch_recipes.MAX_RECIPE_NUM = 5

        # Previous batch with six recipes
        prev_batch = batch_test_utils.create_batch()
        recipe_1 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_2 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_3 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_4 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_5 = recipe_test_utils.create_recipe(batch=prev_batch)
        recipe_6 = recipe_test_utils.create_recipe(batch=prev_batch)

        definition = BatchDefinition()
        definition.prev_batch_id = prev_batch.id
        new_batch = batch_test_utils.create_batch(definition=definition)

        # Create message
        message = batch.messages.create_batch_recipes.CreateBatchRecipes()
        message.batch_id = new_batch.id

        # Copy JSON for running same message again later
        message_json = message.to_json()

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Should be two messages, one for next create_batch_recipes and one for re-processing recipes
        self.assertEqual(len(message.new_messages), 2)
        batch_recipes_message = message.new_messages[0]
        reprocess_message = message.new_messages[1]
        self.assertEqual(batch_recipes_message.type, 'create_batch_recipes')
        self.assertEqual(batch_recipes_message.batch_id, new_batch.id)
        self.assertFalse(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(batch_recipes_message.current_recipe_id, recipe_2.id)
        self.assertEqual(reprocess_message.type, 'reprocess_recipes')
        self.assertSetEqual(set(reprocess_message._root_recipe_ids), {recipe_2.id, recipe_3.id, recipe_4.id,
                                                                      recipe_5.id, recipe_6.id})

        # Test executing message again
        message = batch.messages.create_batch_recipes.CreateBatchRecipes.from_json(message_json)
        result = message.execute()
        self.assertTrue(result)

        # Should have same messages returned
        self.assertEqual(len(message.new_messages), 2)
        batch_recipes_message = message.new_messages[0]
        reprocess_message = message.new_messages[1]
        self.assertEqual(batch_recipes_message.type, 'create_batch_recipes')
        self.assertEqual(batch_recipes_message.batch_id, new_batch.id)
        self.assertFalse(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(batch_recipes_message.current_recipe_id, recipe_2.id)
        self.assertEqual(reprocess_message.type, 'reprocess_recipes')
        self.assertSetEqual(set(reprocess_message._root_recipe_ids), {recipe_2.id, recipe_3.id, recipe_4.id,
                                                                      recipe_5.id, recipe_6.id})

        # Execute next create_batch_recipes messages
        result = batch_recipes_message.execute()
        self.assertTrue(result)

        # Should only have one last reprocess message
        self.assertEqual(len(batch_recipes_message.new_messages), 1)
        reprocess_message = batch_recipes_message.new_messages[0]
        self.assertTrue(batch_recipes_message.is_prev_batch_done)
        self.assertEqual(reprocess_message.type, 'reprocess_recipes')
        self.assertSetEqual(set(reprocess_message._root_recipe_ids), {recipe_1.id})
