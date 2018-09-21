from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from batch.test import utils as batch_test_utils
from job.models import Job
from job.test import utils as job_test_utils
from recipe.messages.purge_recipe import create_purge_recipe_message, PurgeRecipe
from recipe.models import Recipe, RecipeNode
from recipe.test import utils as recipe_test_utils
from storage.test import utils as storage_test_utils
from trigger.test import utils as trigger_test_utils


class TestPurgeRecipe(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.trigger = trigger_test_utils.create_trigger_event()
        
        self.workspace = storage_test_utils.create_workspace()
        self.file_1 = storage_test_utils.create_file()
        self.file_2 = storage_test_utils.create_file()

        interface_1 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.job_type_1 = job_test_utils.create_job_type(interface=interface_1)

        interface_2 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 2',
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': 'Test Output 2',
                'type': 'file',
            }]}
        self.job_type_2 = job_test_utils.create_job_type(interface=interface_2)

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Test Input 1',
                }]
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type_2.name,
                    'version': self.job_type_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Test Output 1',
                        'input': 'Test Input 2',
                    }]
                }]
            }]
        }
        self.recipe_type = recipe_test_utils.create_recipe_type(definition=definition)

        self.input_1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file_1.id,
            }],
            'workspace_id': self.workspace.id,
        }
        self.recipe_1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type)
        self.job_1_1 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=self.recipe_1, job_name='Job 1', job=self.job_1_1)
        self.job_1_2 = job_test_utils.create_job(job_type=self.job_type_2, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=self.recipe_1, job_name='Job 2', job=self.job_1_2)

        self.input_2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file_2.id,
            }],
            'workspace_id': self.workspace.id,
        }
        self.recipe_2 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type, input=self.input_2)
        self.job_2_1 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=self.recipe_2, job_name='Job 1', job=self.job_2_1)
        self.job_2_2 = job_test_utils.create_job(job_type=self.job_type_2, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=self.recipe_2, job_name='Job 2', job=self.job_2_2)

        self.old_recipe_ids = [self.recipe_1.id, self.recipe_2.id]
        self.old_job_ids = [self.job_1_1.id, self.job_1_2.id, self.job_2_1.id, self.job_2_2.id]
        self.old_job_1_ids = [self.job_1_1.id, self.job_2_1.id]
        self.old_job_2_ids = [self.job_1_2.id, self.job_2_2.id]

    def test_json(self):
        """Tests coverting a ReprocessRecipes message to and from JSON"""

        # Create message
        message = create_purge_recipe_message(recipe_id=self.recipe_1.id, trigger_id=self.trigger.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = PurgeRecipe.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)

# Create 2 jobs, assert 2 new_messages wth msg.type == 'create_spawn_delete_files_job'
# TODO: Assert msg.type == 'create_purge_recipe_message' for node recipe.id
# TODO: Assert msg.type == 'create_purge_recipe_message' for parent recipe.id
# TODO: Assert msg.type == 'create_purge_recipe_message' for superseded recipe.id
# TODO: BatchRecipe, RecipeNode, RecipeInputFile, Recipe models have been deleted 

    def test_execute_with_jobs(self):
        """Tests calling PurgeRecipe.execute() successfully"""

        # Create message
        message = create_purge_recipe_message(recipe_id=self.recipe_1.id, trigger_id=self.trigger.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Test to see that the two jobs in this recipe were called to be purged
        self.assertEqual(len(message.new_messages), 2)
        for msg in message.new_messages:
            self.assertIn(msg.job_id, [self.job_1_1.id, self.job_1_2.id])
            self.assertEqual(msg.type, 'spawn_delete_files_job')

    def test_execute_with_parent_recipe(self):
        """Tests calling PurgeRecipe.execute() successfully"""

        # Create recipes
        job_type_1 = job_test_utils.create_job_type()
        job_type_2 = job_test_utils.create_job_type()
        definition_1 = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'job_1',
                'job_type': {
                    'name': job_type_1.name,
                    'version': job_type_1.version,
                },
            }, {
                'name': 'job_2',
                'job_type': {
                    'name': job_type_2.name,
                    'version': job_type_2.version,
                },
                'dependencies': [{
                    'name': 'job_1',
                }],
            }]
        }
        recipe_type_1 = recipe_test_utils.create_recipe_type(definition=definition_1)
        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type_1)

        job_type_3 = job_test_utils.create_job_type()
        job_type_4 = job_test_utils.create_job_type()
        definition_2 = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'job_a',
                'job_type': {
                    'name': job_type_3.name,
                    'version': job_type_3.version,
                },
            }, {
                'name': 'job_b',
                'job_type': {
                    'name': job_type_4.name,
                    'version': job_type_4.version,
                },
                'dependencies': [{
                    'name': 'job_a',
                }],
            }]
        }
        superseded_recipe = recipe_test_utils.create_recipe(is_superseded=True)
        superseded_job_a = job_test_utils.create_job(is_superseded=True)
        superseded_job_b = job_test_utils.create_job(is_superseded=True)
        recipe_test_utils.create_recipe_job(recipe=superseded_recipe, job_name='job_a', job=superseded_job_a)
        recipe_test_utils.create_recipe_job(recipe=superseded_recipe, job_name='job_b', job=superseded_job_b)
        recipe_type_2 = recipe_test_utils.create_recipe_type(definition=definition_2)
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type_2, superseded_recipe=superseded_recipe)
        
        # Create message
        message = create_purge_recipe_message(recipe_id=recipe_2.id, trigger_id=self.trigger.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # 
        # self.assertEqual(len(message.new_messages), 2)
        for msg in message.new_messages:
            # self.assertIn(msg.job_id, [self.job_1_1.id, self.job_1_2.id])
            print msg.type
