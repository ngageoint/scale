from __future__ import unicode_literals

import django
from django.test import TestCase

from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.interface.interface import Interface
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.diff.forced_nodes import ForcedNodes
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6
from recipe.messages.create_recipes import SUB_RECIPE_TYPE, SubRecipe
from recipe.messages.update_recipe import create_update_recipe_message, UpdateRecipe
from recipe.test import utils as recipe_test_utils


class TestUpdateRecipe(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests converting an UpdateRecipe message to and from JSON"""

        job_failed = job_test_utils.create_job(status='FAILED')
        job_pending = job_test_utils.create_job(status='PENDING')
        definition = RecipeDefinition(Interface())
        definition.add_job_node('job_failed', job_failed.job_type.name, job_failed.job_type.version,
                                job_failed.job_type_rev.revision_num)
        definition.add_job_node('job_pending', job_pending.job_type.name, job_pending.job_type.version,
                                job_pending.job_type_rev.revision_num)
        definition.add_dependency('job_failed', 'job_pending')
        definition_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_test_utils.create_recipe_job(recipe=recipe, job_name='job_failed', job=job_failed)
        recipe_test_utils.create_recipe_job(recipe=recipe, job_name='job_pending', job=job_pending)

        # Create message
        message = create_update_recipe_message(recipe.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = UpdateRecipe.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # Check for message to set job_pending to BLOCKED
        self.assertEqual(len(new_message.new_messages), 1)
        msg = new_message.new_messages[0]
        self.assertEqual(msg.type, 'blocked_jobs')
        self.assertListEqual(msg._blocked_job_ids, [job_pending.id])

    def test_json_forced_nodes(self):
        """Tests converting an UpdateRecipe message to and from JSON when forced nodes are provided"""

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        job_completed = job_test_utils.create_job(status='COMPLETED', output=data_dict)
        sub_recipe_type = recipe_test_utils.create_recipe_type()
        definition = RecipeDefinition(Interface())
        definition.add_job_node('job_completed', job_completed.job_type.name, job_completed.job_type.version,
                                job_completed.job_type_rev.revision_num)
        definition.add_recipe_node('the_sub_recipe', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_dependency('job_completed', 'the_sub_recipe')
        definition_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_dict)
        recipe_test_utils.create_recipe_job(recipe=recipe, job_name='job_completed', job=job_completed)
        forced_nodes = ForcedNodes()
        sub_forced_nodes = ForcedNodes()
        sub_forced_nodes.set_all_nodes()
        forced_nodes.add_subrecipe('the_sub_recipe', sub_forced_nodes)

        # Create message
        message = create_update_recipe_message(recipe.id, forced_nodes=forced_nodes)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = UpdateRecipe.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # Check for message to create sub-recipe
        self.assertEqual(len(new_message.new_messages), 1)
        msg = new_message.new_messages[0]
        self.assertEqual(msg.type, 'create_recipes')
        self.assertEqual(msg.event_id, recipe.event_id)
        msg_forced_nodes_dict = convert_forced_nodes_to_v6(msg.forced_nodes).get_dict()
        expected_forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()
        self.assertDictEqual(msg_forced_nodes_dict, expected_forced_nodes_dict)
        self.assertEqual(msg.create_recipes_type, SUB_RECIPE_TYPE)
        self.assertEqual(msg.recipe_id, recipe.id)
        self.assertEqual(msg.root_recipe_id, recipe.root_superseded_recipe_id)
        self.assertIsNone(msg.superseded_recipe_id)
        sub = SubRecipe(sub_recipe_type.name, sub_recipe_type.revision_num, 'the_sub_recipe', True)
        self.assertListEqual(msg.sub_recipes, [sub])

    # def test_execute(self):
    #     """Tests calling UpdateRecipe.execute() successfully"""

    #     # Create recipes for testing the setting of jobs to BLOCKED/PENDING
    #     self.job_1_failed = job_test_utils.create_job(status='FAILED')
    #     self.job_1_pending = job_test_utils.create_job(status='PENDING')
    #     definition_1 = {
    #         'version': '1.0',
    #         'input_data': [],
    #         'jobs': [{
    #             'name': 'job_failed',
    #             'job_type': {
    #                 'name': self.job_1_failed.job_type.name,
    #                 'version': self.job_1_failed.job_type.version,
    #             },
    #         }, {
    #             'name': 'job_pending',
    #             'job_type': {
    #                 'name': self.job_1_pending.job_type.name,
    #                 'version': self.job_1_pending.job_type.version,
    #             },
    #             'dependencies': [{
    #                 'name': 'job_failed',
    #             }],
    #         }],
    #     }
    #     self.recipe_type_1 = recipe_test_utils.create_recipe_type(definition=definition_1)
    #     self.recipe_1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_1)
    #     recipe_test_utils.create_recipe_job(recipe=self.recipe_1, job_name='job_failed', job=self.job_1_failed)
    #     recipe_test_utils.create_recipe_job(recipe=self.recipe_1, job_name='job_pending', job=self.job_1_pending)

    #     self.job_2_running = job_test_utils.create_job(status='RUNNING')
    #     self.job_2_blocked = job_test_utils.create_job(status='BLOCKED')
    #     definition_2 = {
    #         'version': '1.0',
    #         'input_data': [],
    #         'jobs': [{
    #             'name': 'job_running',
    #             'job_type': {
    #                 'name': self.job_2_running.job_type.name,
    #                 'version': self.job_2_running.job_type.version,
    #             },
    #         }, {
    #             'name': 'job_blocked',
    #             'job_type': {
    #                 'name': self.job_2_blocked.job_type.name,
    #                 'version': self.job_2_blocked.job_type.version,
    #             },
    #             'dependencies': [{
    #                 'name': 'job_running',
    #             }],
    #         }],
    #     }
    #     self.recipe_type_2 = recipe_test_utils.create_recipe_type(definition=definition_2)
    #     self.recipe_2 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_2)
    #     recipe_test_utils.create_recipe_job(recipe=self.recipe_2, job_name='job_running', job=self.job_2_running)
    #     recipe_test_utils.create_recipe_job(recipe=self.recipe_2, job_name='job_blocked', job=self.job_2_blocked)

    #     # Create recipe for testing the setting of input for a starting job in a recipe (no parents)
    #     input_name_1 = 'Test Input 1'
    #     output_name_1 = 'Test Output 1'
    #     interface_1 = {
    #         'version': '1.0',
    #         'command': 'my_cmd',
    #         'command_arguments': 'args',
    #         'input_data': [{
    #             'name': input_name_1,
    #             'type': 'file',
    #             'media_types': ['text/plain'],
    #         }],
    #         'output_data': [{
    #             'name': output_name_1,
    #             'type': 'files',
    #             'media_type': 'image/png',
    #         }],
    #     }
    #     job_type_3 = job_test_utils.create_job_type(interface=interface_1)
    #     job_3 = job_test_utils.create_job(job_type=job_type_3, status='PENDING', num_exes=0)

    #     input_name_2 = 'Test Input 2'
    #     output_name_2 = 'Test Output 2'
    #     interface_2 = {
    #         'version': '1.0',
    #         'command': 'my_cmd',
    #         'command_arguments': 'args',
    #         'input_data': [{
    #             'name': input_name_2,
    #             'type': 'files',
    #             'media_types': ['image/png', 'image/tiff'],
    #         }],
    #         'output_data': [{
    #             'name': output_name_2,
    #             'type': 'file',
    #         }],
    #     }
    #     job_type_4 = job_test_utils.create_job_type(interface=interface_2)
    #     job_4 = job_test_utils.create_job(job_type=job_type_4, status='PENDING', num_exes=0)
    #     workspace = storage_test_utils.create_workspace()
    #     file_1 = storage_test_utils.create_file(workspace=workspace, media_type='text/plain')

    #     definition = {
    #         'version': '1.0',
    #         'input_data': [{
    #             'name': 'Recipe Input',
    #             'type': 'file',
    #             'media_types': ['text/plain'],
    #         }],
    #         'jobs': [{
    #             'name': 'Job 1',
    #             'job_type': {
    #                 'name': job_type_3.name,
    #                 'version': job_type_3.version,
    #             },
    #             'recipe_inputs': [{
    #                 'recipe_input': 'Recipe Input',
    #                 'job_input': input_name_1,
    #             }]
    #         }, {
    #             'name': 'Job 2',
    #             'job_type': {
    #                 'name': job_type_4.name,
    #                 'version': job_type_4.version,
    #             },
    #             'dependencies': [{
    #                 'name': 'Job 1',
    #                 'connections': [{
    #                     'output': output_name_1,
    #                     'input': input_name_2,
    #                 }],
    #             }],
    #         }],
    #     }
    #     data = {
    #         'version': '1.0',
    #         'input_data': [{
    #             'name': 'Recipe Input',
    #             'file_id': file_1.id,
    #         }],
    #         'workspace_id': workspace.id,
    #     }
    #     self.recipe_type_3 = recipe_test_utils.create_recipe_type(definition=definition)
    #     self.recipe_3 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_3, input=data)
    #     recipe_test_utils.create_recipe_job(recipe=self.recipe_3, job_name='Job 1', job=job_3)
    #     recipe_test_utils.create_recipe_job(recipe=self.recipe_3, job_name='Job 2', job=job_4)

    #     # Create recipe for testing the setting of input for a child job
    #     job_5 = job_test_utils.create_job(job_type=job_type_3, status='COMPLETED')
    #     file_2 = storage_test_utils.create_file(workspace=workspace, media_type='text/plain')
    #     job_5_output_dict = {
    #         'version': '1.0',
    #         'output_data': [{
    #             'name': output_name_1,
    #             'file_ids': [file_2.id]
    #         }]
    #     }
    #     job_test_utils.create_job_exe(job=job_5, output=JobResults(job_5_output_dict))
    #     # Complete job 5 and set its output so that update recipe message can give go ahead for child job 6
    #     Job.objects.process_job_output([job_5.id], now())
    #     job_6 = job_test_utils.create_job(job_type=job_type_4, status='PENDING', num_exes=0)
    #     self.recipe_4 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type_3, input=data)
    #     recipe_test_utils.create_recipe_job(recipe=self.recipe_4, job_name='Job 1', job=job_5)
    #     recipe_test_utils.create_recipe_job(recipe=self.recipe_4, job_name='Job 2', job=job_6)

    #     # Add recipes to message
    #     message = UpdateRecipes()
    #     if message.can_fit_more():
    #         message.add_recipe(self.recipe_1.id)
    #     if message.can_fit_more():
    #         message.add_recipe(self.recipe_2.id)
    #     if message.can_fit_more():
    #         message.add_recipe(self.recipe_3.id)
    #     if message.can_fit_more():
    #         message.add_recipe(self.recipe_4.id)

    #     # Execute message
    #     result = message.execute()
    #     self.assertTrue(result)

    #     self.assertEqual(len(message.new_messages), 4)
    #     # Check message types
    #     blocked_jobs_msg = False
    #     pending_jobs_msg = False
    #     process_job_input_msg_job_3 = False
    #     process_job_input_msg_job_6 = False
    #     for new_msg in message.new_messages:
    #         if new_msg.type == 'blocked_jobs':
    #             blocked_jobs_msg = True
    #         elif new_msg.type == 'pending_jobs':
    #             pending_jobs_msg = True
    #         elif new_msg.type == 'process_job_input':
    #             if new_msg.job_id == job_3.id:
    #                 process_job_input_msg_job_3 = True
    #             elif new_msg.job_id == job_6.id:
    #                 process_job_input_msg_job_6 = True
    #     self.assertTrue(blocked_jobs_msg)
    #     self.assertTrue(pending_jobs_msg)
    #     self.assertTrue(process_job_input_msg_job_3)
    #     self.assertTrue(process_job_input_msg_job_6)
    #     # Make sure Job 3 has its input populated
    #     job = Job.objects.get(id=job_3.id)
    #     self.assertDictEqual(job.input, {
    #         'version': '1.0',
    #         'input_data': [{
    #             'name': input_name_1,
    #             'file_id': file_1.id,
    #         }],
    #         'output_data': [{
    #             'name': output_name_1,
    #             'workspace_id': workspace.id,
    #         }],
    #     })
    #     # Make sure Job 6 has its input populated
    #     job = Job.objects.get(id=job_6.id)
    #     self.assertDictEqual(job.input, {
    #         'version': '1.0',
    #         'input_data': [{
    #             'name': input_name_2,
    #             'file_ids': [file_2.id],
    #         }],
    #         'output_data': [{
    #             'name': output_name_2,
    #             'workspace_id': workspace.id,
    #         }],
    #     })

    #     # Test executing message again
    #     message_json_dict = message.to_json()
    #     message = UpdateRecipes.from_json(message_json_dict)
    #     result = message.execute()
    #     self.assertTrue(result)

    #     # Make sure the same three messages are returned
    #     self.assertEqual(len(message.new_messages), 4)
    #     # Check message types
    #     blocked_jobs_msg = False
    #     pending_jobs_msg = False
    #     process_job_input_msg_job_3 = False
    #     process_job_input_msg_job_6 = False
    #     for new_msg in message.new_messages:
    #         if new_msg.type == 'blocked_jobs':
    #             blocked_jobs_msg = True
    #         elif new_msg.type == 'pending_jobs':
    #             pending_jobs_msg = True
    #         elif new_msg.type == 'process_job_input':
    #             if new_msg.job_id == job_3.id:
    #                 process_job_input_msg_job_3 = True
    #             elif new_msg.job_id == job_6.id:
    #                 process_job_input_msg_job_6 = True
    #     self.assertTrue(blocked_jobs_msg)
    #     self.assertTrue(pending_jobs_msg)
    #     self.assertTrue(process_job_input_msg_job_3)
    #     self.assertTrue(process_job_input_msg_job_6)

    # def test_execute_create_jobs(self):
    #     """Tests calling UpdateRecipe.execute() successfully where recipe jobs need to be created"""

    #     configuration = BatchConfiguration()
    #     configuration.priority = 999
    #     batch = batch_test_utils.create_batch(configuration=configuration)

    #     # Create recipes
    #     job_type_1 = job_test_utils.create_job_type()
    #     job_type_2 = job_test_utils.create_job_type()
    #     definition_1 = {
    #         'version': '1.0',
    #         'input_data': [],
    #         'jobs': [{
    #             'name': 'job_1',
    #             'job_type': {
    #                 'name': job_type_1.name,
    #                 'version': job_type_1.version,
    #             },
    #         }, {
    #             'name': 'job_2',
    #             'job_type': {
    #                 'name': job_type_2.name,
    #                 'version': job_type_2.version,
    #             },
    #             'dependencies': [{
    #                 'name': 'job_1',
    #             }],
    #         }]
    #     }
    #     recipe_type_1 = recipe_test_utils.create_recipe_type(definition=definition_1)
    #     recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type_1)

    #     job_type_3 = job_test_utils.create_job_type()
    #     job_type_4 = job_test_utils.create_job_type()
    #     definition_2 = {
    #         'version': '1.0',
    #         'input_data': [],
    #         'jobs': [{
    #             'name': 'job_a',
    #             'job_type': {
    #                 'name': job_type_3.name,
    #                 'version': job_type_3.version,
    #             },
    #         }, {
    #             'name': 'job_b',
    #             'job_type': {
    #                 'name': job_type_4.name,
    #                 'version': job_type_4.version,
    #             },
    #             'dependencies': [{
    #                 'name': 'job_a',
    #             }],
    #         }]
    #     }
    #     superseded_recipe = recipe_test_utils.create_recipe(is_superseded=True)
    #     superseded_job_a = job_test_utils.create_job(is_superseded=True)
    #     superseded_job_b = job_test_utils.create_job(is_superseded=True)
    #     recipe_test_utils.create_recipe_job(recipe=superseded_recipe, job_name='job_a', job=superseded_job_a)
    #     recipe_test_utils.create_recipe_job(recipe=superseded_recipe, job_name='job_b', job=superseded_job_b)
    #     recipe_type_2 = recipe_test_utils.create_recipe_type(definition=definition_2)
    #     recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type_2, batch=batch,
    #                                               superseded_recipe=superseded_recipe)

    #     # Add recipes to message
    #     message = UpdateRecipes()
    #     if message.can_fit_more():
    #         message.add_recipe(recipe_1.id)
    #     if message.can_fit_more():
    #         message.add_recipe(recipe_2.id)

    #     # Execute message
    #     result = message.execute()
    #     self.assertTrue(result)

    #     # Make sure jobs get created and that "top" recipe jobs (job_1 and job_a) have input populated
    #     # Recipe 2 jobs (job_a and job_b) should have priority set to 999 from batch
    #     # Recipe 2 jobs (job_a and job_b) should supersede old jobs
    #     rj_qry = RecipeNode.objects.select_related('job').filter(recipe_id__in=[recipe_1.id, recipe_2.id])
    #     recipe_jobs = rj_qry.order_by('recipe_id', 'node_name')
    #     self.assertEqual(len(recipe_jobs), 4)
    #     self.assertEqual(recipe_jobs[0].recipe_id, recipe_1.id)
    #     self.assertEqual(recipe_jobs[0].node_name, 'job_1')
    #     self.assertEqual(recipe_jobs[0].job.job_type_id, job_type_1.id)
    #     self.assertTrue(recipe_jobs[0].is_original)
    #     self.assertTrue(recipe_jobs[0].job.has_input())
    #     self.assertEqual(recipe_jobs[1].recipe_id, recipe_1.id)
    #     self.assertEqual(recipe_jobs[1].node_name, 'job_2')
    #     self.assertEqual(recipe_jobs[1].job.job_type_id, job_type_2.id)
    #     self.assertTrue(recipe_jobs[1].is_original)
    #     self.assertFalse(recipe_jobs[1].job.has_input())
    #     self.assertEqual(recipe_jobs[2].recipe_id, recipe_2.id)
    #     self.assertEqual(recipe_jobs[2].node_name, 'job_a')
    #     self.assertEqual(recipe_jobs[2].job.job_type_id, job_type_3.id)
    #     self.assertTrue(recipe_jobs[2].is_original)
    #     self.assertTrue(recipe_jobs[2].job.has_input())
    #     self.assertEqual(recipe_jobs[2].job.priority, 999)
    #     self.assertEqual(recipe_jobs[2].job.superseded_job_id, superseded_job_a.id)
    #     self.assertEqual(recipe_jobs[3].recipe_id, recipe_2.id)
    #     self.assertEqual(recipe_jobs[3].node_name, 'job_b')
    #     self.assertEqual(recipe_jobs[3].job.job_type_id, job_type_4.id)
    #     self.assertTrue(recipe_jobs[3].is_original)
    #     self.assertFalse(recipe_jobs[3].job.has_input())
    #     self.assertEqual(recipe_jobs[3].job.priority, 999)
    #     self.assertEqual(recipe_jobs[3].job.superseded_job_id, superseded_job_b.id)

    #     jobs = Job.objects.filter(recipe_id__in=[recipe_1.id, recipe_2.id])
    #     self.assertEqual(len(jobs), 4)

    #     # Should have two messages for processing inputs for job_1 and job_a
    #     self.assertEqual(len(message.new_messages), 2)
    #     self.assertEqual(message.new_messages[0].type, 'process_job_input')
    #     self.assertEqual(message.new_messages[1].type, 'process_job_input')
    #     self.assertSetEqual({message.new_messages[0].job_id, message.new_messages[1].job_id},
    #                         {recipe_jobs[0].job_id, recipe_jobs[2].job_id})

    #     # Test executing message again
    #     message_json_dict = message.to_json()
    #     message = UpdateRecipes.from_json(message_json_dict)
    #     result = message.execute()
    #     self.assertTrue(result)

    #     # Make sure no additional jobs are created
    #     rj_qry = RecipeNode.objects.select_related('job').filter(recipe_id__in=[recipe_1.id, recipe_2.id])
    #     recipe_jobs = rj_qry.order_by('recipe_id', 'node_name')
    #     self.assertEqual(len(recipe_jobs), 4)

    #     # Make sure the same messages are returned
    #     self.assertEqual(len(message.new_messages), 2)
    #     self.assertEqual(message.new_messages[0].type, 'process_job_input')
    #     self.assertEqual(message.new_messages[1].type, 'process_job_input')
    #     self.assertSetEqual({message.new_messages[0].job_id, message.new_messages[1].job_id},
    #                         {recipe_jobs[0].job_id, recipe_jobs[2].job_id})
