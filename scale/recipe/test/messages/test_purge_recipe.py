from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
import mock

from data.filter.filter import DataFilter
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from job.test import utils as job_test_utils
from job.models import Job
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.instance.recipe import RecipeInstance
from recipe.messages.purge_recipe import create_purge_recipe_message, PurgeRecipe
from recipe.models import Recipe, RecipeNode
from recipe.test import utils as recipe_test_utils
from storage.models import PurgeResults
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
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Test Input 1',
                }]
            }]
        }
        self.recipe_type = recipe_test_utils.create_recipe_type_v6(definition=definition)

        self.input_1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file_1.id,
            }],
            'workspace_id': self.workspace.id,
        }
        self.recipe_1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type)
        recipe_test_utils.create_input_file(recipe=self.recipe_1)
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

        PurgeResults.objects.create(source_file_id=self.file_1.id, trigger_event=self.trigger)

    def test_json(self):
        """Tests coverting a PurgeRecipe message to and from JSON"""

        # Create message
        message = create_purge_recipe_message(recipe_id=self.recipe_1.id, trigger_id=self.trigger.id,
                                              source_file_id=self.file_1.id)

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = PurgeRecipe.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)

    def test_execute_with_jobs(self):
        """Tests calling PurgeRecipe.execute() successfully"""

        # Create message
        message = create_purge_recipe_message(recipe_id=self.recipe_1.id, trigger_id=self.trigger.id,
                                              source_file_id=self.file_1.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Test to see that the two jobs in this recipe were called to be purged
        msgs = [msg for msg in message.new_messages if msg.type == 'spawn_delete_files_job']
        self.assertEqual(len(msgs), 2)
        for msg in msgs:
            self.assertIn(msg.job_id, [self.job_1_1.id, self.job_1_2.id])

    def test_execute_with_superseded_recipe(self):
        """Tests calling PurgeRecipe.execute() successfully"""

        # Create recipes
        superseded_recipe = recipe_test_utils.create_recipe(is_superseded=True)
        recipe = recipe_test_utils.create_recipe(superseded_recipe=superseded_recipe)
        recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', save=True)

        # Create message
        message = create_purge_recipe_message(recipe_id=recipe.id, trigger_id=self.trigger.id,
                                              source_file_id=self.file_1.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Test to see that a message to purge the superseded recipe was sent
        msgs = [msg for msg in message.new_messages if msg.type == 'purge_recipe']
        self.assertEqual(len(msgs), 1)
        for msg in msgs:
            self.assertEqual(msg.recipe_id, superseded_recipe.id)

        # Assert models were deleted
        self.assertEqual(Recipe.objects.filter(id=recipe.id).count(), 0)
        self.assertEqual(RecipeNode.objects.filter(recipe=recipe).count(), 0)

    def test_execute_with_parent_recipe(self):
        """Tests calling PurgeRecipe.execute() successfully"""

        # Create recipes
        recipe = recipe_test_utils.create_recipe()
        parent_recipe = recipe_test_utils.create_recipe()
        recipe_test_utils.create_recipe_node(recipe=parent_recipe, node_name='A', sub_recipe=recipe, save=True)

        # Create message
        message = create_purge_recipe_message(recipe_id=recipe.id, trigger_id=self.trigger.id,
                                              source_file_id=self.file_1.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Test to see that a message to purge the parent recipe was sent
        msgs = [msg for msg in message.new_messages if msg.type == 'purge_recipe']
        self.assertEqual(len(msgs), 1)
        for msg in msgs:
            self.assertEqual(msg.recipe_id, parent_recipe.id)

        # Assert models were deleted
        self.assertEqual(Recipe.objects.filter(id=recipe.id).count(), 0)
        self.assertEqual(RecipeNode.objects.filter(recipe=recipe).count(), 0)

    def test_execute_with_sub_recipe(self):
        """Tests calling PurgeRecipe.execute() successfully"""

        # Create recipes
        sub_recipe_type = recipe_test_utils.create_recipe_type_v6()

        definition = RecipeDefinition(Interface())
        definition.add_recipe_node('A', sub_recipe_type.name, sub_recipe_type.revision_num)

        recipe_a = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type, save=False)
        recipe_a.jobs_completed = 3
        recipe_a.jobs_running = 2
        recipe_a.jobs_total = 5
        Recipe.objects.bulk_create([recipe_a])

        definition_json_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type_v6(definition=definition_json_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)

        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', sub_recipe=recipe_a,
                                                             save=False)
        RecipeNode.objects.bulk_create([recipe_node_a])

        # Create message
        message = create_purge_recipe_message(recipe_id=recipe.id, trigger_id=self.trigger.id,
                                              source_file_id=self.file_1.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Test to see that a message to purge the parent recipe was sent
        msgs = [msg for msg in message.new_messages if msg.type == 'purge_recipe']
        self.assertEqual(len(msgs), 1)
        for msg in msgs:
            self.assertEqual(msg.recipe_id, recipe_node_a.sub_recipe.id)

    def test_execute_no_leaf_nodes(self):
        """Tests calling PurgeRecipe.execute() successfully"""

        # Create recipes
        recipe_type = recipe_test_utils.create_recipe_type_v6()
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)

        # Create message
        message = create_purge_recipe_message(recipe_id=recipe.id, trigger_id=self.trigger.id,
                                              source_file_id=self.file_1.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Assert models were deleted
        self.assertEqual(Recipe.objects.filter(id=recipe.id).count(), 0)
        self.assertEqual(RecipeNode.objects.filter(recipe=recipe).count(), 0)

    def test_execute_check_results(self):
        """Tests calling PurgeRecipe.execute() successfully"""

        # Create PurgeResults entry
        trigger_2 = trigger_test_utils.create_trigger_event()
        file_2 = storage_test_utils.create_file()
        PurgeResults.objects.create(source_file_id=file_2.id, trigger_event=trigger_2)
        self.assertEqual(PurgeResults.objects.values_list('num_recipes_deleted', flat=True).get(
            source_file_id=file_2.id), 0)

        # Create recipes
        recipe_type = recipe_test_utils.create_recipe_type_v6()
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)

        # Create message
        message = create_purge_recipe_message(recipe_id=recipe.id, trigger_id=self.trigger.id,
                                              source_file_id=self.file_1.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check results are accurate
        self.assertEqual(PurgeResults.objects.values_list('num_recipes_deleted', flat=True).get(
            source_file_id=self.file_1.id), 1)

    def test_execute_force_stop(self):
        """Tests calling PurgeRecipe.execute() successfully"""

        # Create PurgeResults entry
        file_2 = storage_test_utils.create_file(file_type='SOURCE')
        trigger = trigger_test_utils.create_trigger_event()
        PurgeResults.objects.create(source_file_id=file_2.id, trigger_event=trigger, force_stop_purge=True)
        self.assertEqual(PurgeResults.objects.values_list('num_recipes_deleted', flat=True).get(
            trigger_event=trigger.id), 0)

        # Create recipes
        recipe_type = recipe_test_utils.create_recipe_type_v6()
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)

        # Create message
        message = create_purge_recipe_message(recipe_id=recipe.id, trigger_id=trigger.id,
                                              source_file_id=file_2.id)

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check results are accurate
        self.assertEqual(PurgeResults.objects.values_list('num_recipes_deleted', flat=True).get(
            source_file_id=file_2.id), 0)

    def test_execute_dummy_recipe(self):
        """Tests calling PurgeRecipe.execute() with dummy nodes"""

        file_2 = storage_test_utils.create_file(file_type='SOURCE')
        trigger = trigger_test_utils.create_trigger_event()
        PurgeResults.objects.create(source_file_id=file_2.id, trigger_event=trigger, force_stop_purge=True)
        self.assertEqual(PurgeResults.objects.values_list('num_recipes_deleted', flat=True).get(
            trigger_event=trigger.id), 0)

        job_type_1 = job_test_utils.create_job_type()
        job_type_2 = job_test_utils.create_job_type()
        job_type_3 = job_test_utils.create_job_type()
        job_type_4 = job_test_utils.create_job_type()
        recipe_type_1 = recipe_test_utils.create_recipe_type_v5()

        interface = Interface()
        interface.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface.add_parameter(JsonParameter('json_param_1', 'object'))

        definition = RecipeDefinition(interface)
        definition.add_job_node('A', job_type_1.name, job_type_1.version, job_type_1.revision_num)
        definition.add_job_node('B', job_type_2.name, job_type_2.version, job_type_2.revision_num)
        definition.add_job_node('C', job_type_3.name, job_type_3.version, job_type_3.revision_num)
        definition.add_recipe_node('D', recipe_type_1.name, recipe_type_1.revision_num)
        definition.add_job_node('E', job_type_4.name, job_type_4.version, job_type_4.revision_num)
        definition.add_condition_node('F', Interface(), DataFilter())
        definition.add_job_node('G', job_type_4.name, job_type_4.version, job_type_4.revision_num)
        definition.add_dependency('A', 'B')
        definition.add_dependency('A', 'C')
        definition.add_dependency('B', 'E')
        definition.add_dependency('C', 'D')
        definition.add_dependency('A', 'F')
        definition.add_dependency('F', 'G')
        definition.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')

        recipe = recipe_test_utils.create_recipe()
        job_a = job_test_utils.create_job(job_type=job_type_1, status='COMPLETED', save=False)
        job_b = job_test_utils.create_job(job_type=job_type_2, status='RUNNING', save=False)
        job_c = job_test_utils.create_job(job_type=job_type_3, status='COMPLETED', save=False)
        job_e = job_test_utils.create_job(job_type=job_type_4, status='PENDING', num_exes=0, save=False)
        Job.objects.bulk_create([job_a, job_b, job_c, job_e])
        condition_f = recipe_test_utils.create_recipe_condition(is_processed=True, is_accepted=False, save=True)
        recipe_d = recipe_test_utils.create_recipe(recipe_type=recipe_type_1)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', job=job_a, save=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='B', job=job_b, save=False)
        recipe_node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='C', job=job_c, save=False)
        recipe_node_d = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='D', sub_recipe=recipe_d,
                                                             save=False)
        recipe_node_e = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='E', job=job_e, save=False)
        recipe_node_f = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='F', condition=condition_f,
                                                             save=False)
        recipe_nodes = [recipe_node_a, recipe_node_b, recipe_node_c, recipe_node_d, recipe_node_e, recipe_node_f]

        # Create message
        message = create_purge_recipe_message(recipe_id=recipe.id, trigger_id=trigger.id,
                                              source_file_id=file_2.id)

        # Execute message
        with mock.patch('recipe.models.RecipeManager.get_recipe_instance', 
                        return_value=RecipeInstance(definition, recipe, recipe_nodes)) as recipe_instance_mock:
            result = message.execute()
            self.assertTrue(result)