from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from recipe.messages.process_recipe_input import ProcessRecipeInput
from recipe.models import Recipe, RecipeInputFile
from recipe.test import utils as recipe_test_utils
from storage.test import utils as storage_test_utils


class TestProcessRecipeInput(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a ProcessRecipeInput message to and from JSON"""

        recipe_1 = recipe_test_utils.create_recipe()
        recipe_2 = recipe_test_utils.create_recipe()
        recipe_ids = [recipe_1.id, recipe_2.id]

        # Add recipes to message
        message = ProcessRecipeInput()
        if message.can_fit_more():
            message.add_recipe(recipe_1.id)
        if message.can_fit_more():
            message.add_recipe(recipe_2.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = ProcessRecipeInput.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        recipes = Recipe.objects.filter(id__in=recipe_ids).order_by('id')
        self.assertEqual(len(new_message.new_messages), 1)
        self.assertEqual(new_message.new_messages[0].type, 'update_recipes')
        # Recipes should have input_file_size set to 0 (no input files)
        self.assertEqual(recipes[0].input_file_size, 0.0)
        self.assertEqual(recipes[1].input_file_size, 0.0)

    def test_execute(self):
        """Tests calling ProcessRecipeInput.execute() successfully"""

        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=10485760.0)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0)
        file_3 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0)
        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }, {
                'name': 'Input 2',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': []
        }
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition)

        input_1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_1.id
            }, {
                'name': 'Input 2',
                'file_id': file_2.id
            }],
            'workspace_id': workspace.id
        }
        input_2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_2.id
            }, {
                'name': 'Input 2',
                'file_id': file_3.id
            }],
            'workspace_id': workspace.id
        }

        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=input_1)
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=input_2)
        recipe_ids = [recipe_1.id, recipe_2.id]

        # Add jobs to message
        message = ProcessRecipeInput()
        if message.can_fit_more():
            message.add_recipe(recipe_1.id)
        if message.can_fit_more():
            message.add_recipe(recipe_2.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        recipes = Recipe.objects.filter(id__in=recipe_ids).order_by('id')
        # Check for update_recipes message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipes')

        # Check recipes for expected input_file_size
        self.assertEqual(recipes[0].input_file_size, 110.0)
        self.assertEqual(recipes[1].input_file_size, 1042.0)

        # Make sure recipe input file models are created
        recipe_input_files = RecipeInputFile.objects.filter(recipe_id=recipe_1.id)
        self.assertEqual(len(recipe_input_files), 2)
        for recipe_input_file in recipe_input_files:
            if recipe_input_file.recipe_input == 'Input 1':
                self.assertEqual(recipe_input_file.scale_file_id, file_1.id)
            elif recipe_input_file.recipe_input == 'Input 2':
                self.assertEqual(recipe_input_file.scale_file_id, file_2.id)
            else:
                self.fail('Invalid input name: %s' % recipe_input_file.recipe_input)
        recipe_input_files = RecipeInputFile.objects.filter(recipe_id=recipe_2.id)
        self.assertEqual(len(recipe_input_files), 2)
        for recipe_input_file in recipe_input_files:
            if recipe_input_file.recipe_input == 'Input 1':
                self.assertEqual(recipe_input_file.scale_file_id, file_2.id)
            elif recipe_input_file.recipe_input == 'Input 2':
                self.assertEqual(recipe_input_file.scale_file_id, file_3.id)
            else:
                self.fail('Invalid input name: %s' % recipe_input_file.recipe_input)

        # Test executing message again
        message_json_dict = message.to_json()
        message = ProcessRecipeInput.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Still should have update_recipes message
        self.assertEqual(len(message.new_messages), 1)
        self.assertEqual(message.new_messages[0].type, 'update_recipes')

        # Make sure recipe input file models are unchanged
        recipe_input_files = RecipeInputFile.objects.filter(recipe_id=recipe_1.id)
        self.assertEqual(len(recipe_input_files), 2)
        recipe_input_files = RecipeInputFile.objects.filter(recipe_id=recipe_2.id)
        self.assertEqual(len(recipe_input_files), 2)
