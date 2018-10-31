from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from batch.test import utils as batch_test_utils
from recipe.messages.create_conditions import create_conditions_messages, CreateConditions, Condition
from recipe.models import RecipeCondition, RecipeNode
from recipe.test import utils as recipe_test_utils


class TestCreateConditions(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests converting a CreateConditions message to and from JSON"""

        batch = batch_test_utils.create_batch()
        recipe = recipe_test_utils.create_recipe(batch=batch)
        conditions = [Condition('node_1', False), Condition('node_2', True)]

        # Create message
        message = create_conditions_messages(recipe, conditions)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateConditions.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        self.assertEqual(RecipeCondition.objects.filter(recipe_id=recipe.id).count(), 2)
        recipe_nodes = RecipeNode.objects.select_related('condition').filter(recipe_id=recipe.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_1')
        self.assertEqual(recipe_nodes[1].node_name, 'node_2')
        condition_2 = recipe_nodes[1].condition

        # Should be one message for processing condition for node 2
        self.assertEqual(len(new_message.new_messages), 1)
        process_condition_msg = new_message.new_messages[0]
        self.assertEqual(process_condition_msg.type, 'process_condition')
        self.assertEqual(process_condition_msg.condition_id, condition_2.id)

    def test_execute(self):
        """Tests calling CreateConditions.execute() successfully"""

        batch = batch_test_utils.create_batch()
        recipe = recipe_test_utils.create_recipe(batch=batch)
        conditions = [Condition('node_1', False), Condition('node_2', True)]

        # Create and execute message
        message = create_conditions_messages(recipe, conditions)[0]
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(RecipeCondition.objects.filter(recipe_id=recipe.id).count(), 2)
        recipe_nodes = RecipeNode.objects.select_related('condition').filter(recipe_id=recipe.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_1')
        self.assertEqual(recipe_nodes[1].node_name, 'node_2')
        condition_2 = recipe_nodes[1].condition

        # Should be one message for processing condition for node 2
        self.assertEqual(len(message.new_messages), 1)
        process_condition_msg = message.new_messages[0]
        self.assertEqual(process_condition_msg.type, 'process_condition')
        self.assertEqual(process_condition_msg.condition_id, condition_2.id)

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateConditions.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(RecipeCondition.objects.filter(recipe_id=recipe.id).count(), 2)
        recipe_nodes = RecipeNode.objects.select_related('condition').filter(recipe_id=recipe.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_1')
        self.assertEqual(recipe_nodes[1].node_name, 'node_2')
        condition_2.id = recipe_nodes[1].condition_id

        # Should be one message for processing condition for node 2
        self.assertEqual(len(message.new_messages), 1)
        process_condition_msg = message.new_messages[0]
        self.assertEqual(process_condition_msg.type, 'process_condition')
        self.assertEqual(process_condition_msg.condition_id, condition_2.id)
