from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from batch.test import utils as batch_test_utils
from job.models import Job
from job.test import utils as job_test_utils
from recipe.messages.reprocess_recipes import create_reprocess_recipes_messages, ReprocessRecipes
from recipe.models import Recipe, RecipeJob
from recipe.test import utils as recipe_test_utils
from storage.test import utils as storage_test_utils
from trigger.test import utils as trigger_test_utils


class TestReprocessRecipes(TransactionTestCase):

    def setUp(self):
        django.setup()

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
        self.recipe_1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type, input=self.input_1)
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

        batch = batch_test_utils.create_batch()
        event = trigger_test_utils.create_trigger_event()

        # Create message
        message = create_reprocess_recipes_messages(self.old_recipe_ids, self.recipe_1.recipe_type_rev_id, event.id,
                                                    all_jobs=True, job_names=['Job 1', 'Job 2'], batch_id=batch.id)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = ReprocessRecipes.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        # Make sure new recipes supersede the old ones
        for recipe in Recipe.objects.filter(id__in=self.old_recipe_ids):
            self.assertTrue(recipe.is_superseded)
        new_recipe_1 = Recipe.objects.get(superseded_recipe_id=self.recipe_1.id)
        self.assertEqual(new_recipe_1.batch_id, batch.id)
        self.assertEqual(new_recipe_1.event_id, event.id)
        self.assertDictEqual(new_recipe_1.input, self.recipe_1.input)
        new_recipe_2 = Recipe.objects.get(superseded_recipe_id=self.recipe_2.id)
        self.assertEqual(new_recipe_2.batch_id, batch.id)
        self.assertEqual(new_recipe_2.event_id, event.id)
        self.assertDictEqual(new_recipe_2.input, self.recipe_2.input)
        # Make sure old jobs are superseded
        for job in Job.objects.filter(id__in=self.old_job_ids):
            self.assertTrue(job.is_superseded)
        # Should be two messages, one for processing new recipe input and one for canceling superseded jobs
        self.assertEqual(len(new_message.new_messages), 2)
        found_process_recipe_input = False
        found_cancel_jobs = False
        for msg in new_message.new_messages:
            if msg.type == 'process_recipe_input':
                found_process_recipe_input = True
            elif msg.type == 'cancel_jobs':
                found_cancel_jobs = True
        self.assertTrue(found_process_recipe_input)
        self.assertTrue(found_cancel_jobs)

    def test_execute(self):
        """Tests calling ReprocessRecipes.execute() successfully"""

        batch = batch_test_utils.create_batch()
        event = trigger_test_utils.create_trigger_event()

        # Create message
        message = create_reprocess_recipes_messages(self.old_recipe_ids, self.recipe_1.recipe_type_rev_id, event.id,
                                                    all_jobs=False, job_names=['Job 2'], batch_id=batch.id)[0]

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Make sure new recipes supersede the old ones
        for recipe in Recipe.objects.filter(id__in=self.old_recipe_ids):
            self.assertTrue(recipe.is_superseded)
        new_recipe_1 = Recipe.objects.get(superseded_recipe_id=self.recipe_1.id)
        self.assertEqual(new_recipe_1.batch_id, batch.id)
        self.assertEqual(new_recipe_1.event_id, event.id)
        self.assertEqual(new_recipe_1.root_superseded_recipe_id, self.recipe_1.id)
        self.assertDictEqual(new_recipe_1.input, self.recipe_1.input)
        new_recipe_2 = Recipe.objects.get(superseded_recipe_id=self.recipe_2.id)
        self.assertEqual(new_recipe_2.batch_id, batch.id)
        self.assertEqual(new_recipe_2.event_id, event.id)
        self.assertEqual(new_recipe_2.root_superseded_recipe_id, self.recipe_2.id)
        self.assertDictEqual(new_recipe_2.input, self.recipe_2.input)
        # Make sure identical jobs (Job 1) are NOT superseded
        for job in Job.objects.filter(id__in=self.old_job_1_ids):
            self.assertFalse(job.is_superseded)
        # Make sure old jobs (Job 2) are superseded
        for job in Job.objects.filter(id__in=self.old_job_2_ids):
            self.assertTrue(job.is_superseded)
        # Make sure identical jobs (Job 1) were copied to new recipes
        recipe_job_1 = RecipeJob.objects.get(recipe=new_recipe_1.id)
        self.assertEqual(recipe_job_1.job_name, 'Job 1')
        self.assertEqual(recipe_job_1.job_id, self.job_1_1.id)
        recipe_job_2 = RecipeJob.objects.get(recipe=new_recipe_2.id)
        self.assertEqual(recipe_job_2.job_name, 'Job 1')
        self.assertEqual(recipe_job_2.job_id, self.job_2_1.id)
        # Should be two messages, one for processing new recipe input and one for canceling superseded jobs
        self.assertEqual(len(message.new_messages), 2)
        found_process_recipe_input = False
        found_cancel_jobs = False
        for msg in message.new_messages:
            if msg.type == 'process_recipe_input':
                found_process_recipe_input = True
                self.assertSetEqual(set(msg._recipe_ids), {new_recipe_1.id, new_recipe_2.id})
            elif msg.type == 'cancel_jobs':
                found_cancel_jobs = True
                self.assertSetEqual(set(msg._job_ids), set(self.old_job_2_ids))
        self.assertTrue(found_process_recipe_input)
        self.assertTrue(found_cancel_jobs)

        # Test executing message again
        message_json_dict = message.to_json()
        message = ReprocessRecipes.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Make sure we don't reprocess twice
        for new_recipe in Recipe.objects.filter(id__in=[new_recipe_1.id, new_recipe_2.id]):
            self.assertFalse(new_recipe.is_superseded)
        # Should get same messages
        self.assertEqual(len(message.new_messages), 2)
        found_process_recipe_input = False
        found_cancel_jobs = False
        for msg in message.new_messages:
            if msg.type == 'process_recipe_input':
                found_process_recipe_input = True
                self.assertSetEqual(set(msg._recipe_ids), {new_recipe_1.id, new_recipe_2.id})
            elif msg.type == 'cancel_jobs':
                found_cancel_jobs = True
                self.assertSetEqual(set(msg._job_ids), set(self.old_job_2_ids))
        self.assertTrue(found_process_recipe_input)
        self.assertTrue(found_cancel_jobs)
