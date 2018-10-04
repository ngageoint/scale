from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.test import utils as batch_test_utils
from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.data.value import FileValue
from data.interface.interface import Interface
from data.interface.parameter import FileParameter
from job.models import Job
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.diff.forced_nodes import ForcedNodes
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6
from recipe.messages.create_recipes import create_reprocess_messages, create_subrecipes_messages, CreateRecipes, \
    SubRecipe
from recipe.models import Recipe, RecipeNode
from recipe.test import utils as recipe_test_utils
from storage.test import utils as storage_test_utils
from trigger.test import utils as trigger_test_utils


class TestCreateRecipes(TestCase):

    def setUp(self):
        django.setup()

    def test_json_reprocess(self):
        """Tests converting a CreateRecipes message to and from JSON when re-processing"""

        file_1 = storage_test_utils.create_file()
        file_2 = storage_test_utils.create_file()

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
        job_type_1 = job_test_utils.create_job_type(interface=interface_1)

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
        job_type_2 = job_test_utils.create_job_type(interface=interface_2)

        recipe_interface = Interface()
        recipe_interface.add_parameter(FileParameter('Recipe Input', ['text/plain']))
        definition = RecipeDefinition(recipe_interface)
        definition.add_job_node('Job 1', job_type_1.name, job_type_1.version, job_type_1.revision_num)
        definition.add_recipe_input_connection('Job 1', 'Test Input 1', 'Recipe Input')
        definition.add_job_node('Job 2', job_type_2.name, job_type_2.version, job_type_2.revision_num)
        definition.add_dependency('Job 1', 'Job 2')
        definition.add_dependency_input_connection('Job 2', 'Test Input 2', 'Job 1', 'Test Output 1')
        definition_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_dict)

        input_1 = Data()
        input_1.add_value(FileValue('Recipe Input', [file_1.id]))
        input_1_dict = convert_data_to_v6_json(input_1).get_dict()
        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=input_1_dict)
        job_1_1 = job_test_utils.create_job(job_type=job_type_1, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job_name='Job 1', job=job_1_1)
        job_1_2 = job_test_utils.create_job(job_type=job_type_2, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job_name='Job 2', job=job_1_2)

        input_2 = Data()
        input_2.add_value(FileValue('Recipe Input', [file_2.id]))
        input_2_dict = convert_data_to_v6_json(input_2).get_dict()
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=input_2_dict)
        job_2_1 = job_test_utils.create_job(job_type=job_type_1, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job_name='Job 1', job=job_2_1)
        job_2_2 = job_test_utils.create_job(job_type=job_type_2, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job_name='Job 2', job=job_2_2)

        event = trigger_test_utils.create_trigger_event()

        # Create message to reprocess recipe 1 and 2
        reprocess_recipe_ids = [recipe_1.id, recipe_2.id]
        reprocess_job_ids = [job_1_1.id, job_1_2.id, job_2_1.id, job_2_2.id]
        message = create_reprocess_messages(reprocess_recipe_ids, recipe_1.recipe_type.name,
                                            recipe_1.recipe_type.revision_num, event.id)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateRecipes.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # Make sure new recipes supersede the old ones
        for recipe in Recipe.objects.filter(id__in=reprocess_recipe_ids):
            self.assertTrue(recipe.is_superseded)
        new_recipe_1 = Recipe.objects.get(superseded_recipe_id=recipe_1.id)
        self.assertEqual(new_recipe_1.event_id, event.id)
        self.assertDictEqual(new_recipe_1.input, recipe_1.input)
        new_recipe_2 = Recipe.objects.get(superseded_recipe_id=recipe_2.id)
        self.assertEqual(new_recipe_2.event_id, event.id)
        self.assertDictEqual(new_recipe_2.input, recipe_2.input)
        # Nothing changed in recipe type revision, so reprocessed jobs should all be copied to new recipes
        for job in Job.objects.filter(id__in=reprocess_job_ids):
            self.assertFalse(job.is_superseded)
        recipe_nodes = RecipeNode.objects.filter(recipe_id__in=[new_recipe_1.id, new_recipe_2.id])
        self.assertEqual(len(recipe_nodes), 4)
        for recipe_node in recipe_nodes:
            if recipe_node.recipe_id == new_recipe_1.id:
                self.assertTrue(recipe_node.job_id in [job_1_1.id, job_1_2.id])
            elif recipe_node.recipe_id == new_recipe_2.id:
                self.assertTrue(recipe_node.job_id in [job_2_1.id, job_2_2.id])
            self.assertFalse(recipe_node.is_original)

        # Should be two messages for processing the input for the new recipes
        self.assertEqual(len(new_message.new_messages), 2)
        for msg in new_message.new_messages:
            self.assertEqual(msg.type, 'process_recipe_input')
            self.assertTrue(msg.recipe_id in [new_recipe_1.id, new_recipe_2.id])
            self.assertIsNone(msg.forced_nodes)

    def test_json_reprocess_forced_nodes(self):
        """Tests converting a CreateRecipes message to and from JSON when re-processing with forced nodes"""

        file_1 = storage_test_utils.create_file()
        file_2 = storage_test_utils.create_file()

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
        job_type_1 = job_test_utils.create_job_type(interface=interface_1)

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
        job_type_2 = job_test_utils.create_job_type(interface=interface_2)

        recipe_interface = Interface()
        recipe_interface.add_parameter(FileParameter('Recipe Input', ['text/plain']))
        definition = RecipeDefinition(recipe_interface)
        definition.add_job_node('Job 1', job_type_1.name, job_type_1.version, job_type_1.revision_num)
        definition.add_recipe_input_connection('Job 1', 'Test Input 1', 'Recipe Input')
        definition.add_job_node('Job 2', job_type_2.name, job_type_2.version, job_type_2.revision_num)
        definition.add_dependency('Job 1', 'Job 2')
        definition.add_dependency_input_connection('Job 2', 'Test Input 2', 'Job 1', 'Test Output 1')
        definition_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_dict)

        input_1 = Data()
        input_1.add_value(FileValue('Recipe Input', [file_1.id]))
        input_1_dict = convert_data_to_v6_json(input_1).get_dict()
        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=input_1_dict)
        job_1_1 = job_test_utils.create_job(job_type=job_type_1, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job_name='Job 1', job=job_1_1)
        job_1_2 = job_test_utils.create_job(job_type=job_type_2, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job_name='Job 2', job=job_1_2)

        input_2 = Data()
        input_2.add_value(FileValue('Recipe Input', [file_2.id]))
        input_2_dict = convert_data_to_v6_json(input_2).get_dict()
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=input_2_dict)
        job_2_1 = job_test_utils.create_job(job_type=job_type_1, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job_name='Job 1', job=job_2_1)
        job_2_2 = job_test_utils.create_job(job_type=job_type_2, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job_name='Job 2', job=job_2_2)

        event = trigger_test_utils.create_trigger_event()
        batch = batch_test_utils.create_batch()
        forced_nodes = ForcedNodes()
        forced_nodes.set_all_nodes()

        # Create message to reprocess recipe 1 and 2
        reprocess_recipe_ids = [recipe_1.id, recipe_2.id]
        reprocess_job_ids = [job_1_1.id, job_1_2.id, job_2_1.id, job_2_2.id]
        message = create_reprocess_messages(reprocess_recipe_ids, recipe_1.recipe_type.name,
                                            recipe_1.recipe_type.revision_num, event.id, batch_id=batch.id,
                                            forced_nodes=forced_nodes)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateRecipes.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # Make sure new recipes supersede the old ones
        for recipe in Recipe.objects.filter(id__in=reprocess_recipe_ids):
            self.assertTrue(recipe.is_superseded)
        new_recipe_1 = Recipe.objects.get(superseded_recipe_id=recipe_1.id)
        self.assertEqual(new_recipe_1.batch_id, batch.id)
        self.assertEqual(new_recipe_1.event_id, event.id)
        self.assertDictEqual(new_recipe_1.input, recipe_1.input)
        new_recipe_2 = Recipe.objects.get(superseded_recipe_id=recipe_2.id)
        self.assertEqual(new_recipe_2.batch_id, batch.id)
        self.assertEqual(new_recipe_2.event_id, event.id)
        self.assertDictEqual(new_recipe_2.input, recipe_2.input)
        # All nodes were forced to reprocess, new recipes should have no copied jobs
        self.assertEqual(RecipeNode.objects.filter(recipe_id__in=[new_recipe_1.id, new_recipe_2.id]).count(), 0)
        for job in Job.objects.filter(id__in=reprocess_job_ids):
            self.assertFalse(job.is_superseded)

        # Should be three messages, one for superseding recipe nodes and two for processing recipe input
        self.assertEqual(len(new_message.new_messages), 3)
        supersede_recipe_msg = None
        process_recipe_input_1_msg = None
        process_recipe_input_2_msg = None
        for msg in new_message.new_messages:
            if msg.type == 'supersede_recipe_nodes':
                supersede_recipe_msg = msg
            elif msg.type == 'process_recipe_input':
                if msg.recipe_id == new_recipe_1.id:
                    process_recipe_input_1_msg = msg
                if msg.recipe_id == new_recipe_2.id:
                    process_recipe_input_2_msg = msg
        self.assertIsNotNone(supersede_recipe_msg)
        self.assertIsNotNone(process_recipe_input_1_msg)
        self.assertIsNotNone(process_recipe_input_2_msg)
        # Check message for superseding recipes 1 and 2
        self.assertListEqual(supersede_recipe_msg._recipe_ids, reprocess_recipe_ids)
        self.assertFalse(supersede_recipe_msg.supersede_all)
        self.assertSetEqual(supersede_recipe_msg.supersede_jobs, {'Job 1', 'Job 2'})
        self.assertSetEqual(supersede_recipe_msg.supersede_subrecipes, set())
        self.assertFalse(supersede_recipe_msg.unpublish_all)
        self.assertSetEqual(supersede_recipe_msg.unpublish_jobs, set())
        self.assertFalse(supersede_recipe_msg.supersede_recursive_all)
        self.assertSetEqual(supersede_recipe_msg.supersede_recursive, set())
        self.assertFalse(supersede_recipe_msg.unpublish_recursive_all)
        self.assertSetEqual(supersede_recipe_msg.unpublish_recursive, set())
        # Check message to process recipe input for new recipe 1
        self.assertEqual(process_recipe_input_1_msg.recipe_id, new_recipe_1.id)
        msg_forced_nodes = convert_forced_nodes_to_v6(process_recipe_input_1_msg.forced_nodes).get_dict()
        forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_dict)
        # Check message to process recipe input for new recipe 2
        self.assertEqual(process_recipe_input_2_msg.recipe_id, new_recipe_2.id)
        msg_forced_nodes = convert_forced_nodes_to_v6(process_recipe_input_2_msg.forced_nodes).get_dict()
        forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_dict)

    def test_json_subrecipes(self):
        """Tests converting a CreateRecipes message to and from JSON when creating sub-recipes"""

        # Creates definitions for sub-recipe A and sub-recipe B
        event = trigger_test_utils.create_trigger_event()
        top_recipe_type = recipe_test_utils.create_recipe_type()
        job_type_a_1 = job_test_utils.create_seed_job_type()
        job_type_a_2 = job_test_utils.create_seed_job_type()
        sub_definition_a = RecipeDefinition(Interface())
        sub_definition_a.add_job_node('node_1', job_type_a_1.name, job_type_a_1.version, job_type_a_1.revision_num)
        sub_definition_a.add_job_node('node_2', job_type_a_2.name, job_type_a_2.version, job_type_a_2.revision_num)
        sub_definition_a.add_dependency('node_1', 'node_2')
        sub_definition_a_dict = convert_recipe_definition_to_v6_json(sub_definition_a).get_dict()
        recipe_type_a = recipe_test_utils.create_recipe_type(definition=sub_definition_a_dict)
        job_type_b_x = job_test_utils.create_seed_job_type()
        recipe_type_b_y = recipe_test_utils.create_recipe_type()
        sub_definition_b = RecipeDefinition(Interface())
        sub_definition_b.add_job_node('node_x', job_type_b_x.name, job_type_b_x.version, job_type_b_x.revision_num)
        sub_definition_b.add_recipe_node('node_y', recipe_type_b_y.name, recipe_type_b_y.revision_num)
        sub_definition_b.add_dependency('node_x', 'node_y')
        sub_definition_b_dict = convert_recipe_definition_to_v6_json(sub_definition_b).get_dict()
        recipe_type_b = recipe_test_utils.create_recipe_type(definition=sub_definition_b_dict)
        top_recipe = recipe_test_utils.create_recipe(recipe_type=top_recipe_type, event=event, save=True)

        # Create message to create sub-recipes A and B for top_recipe
        sub_recipes = [SubRecipe(recipe_type_a.name, recipe_type_a.revision_num, 'node_a', True),
                       SubRecipe(recipe_type_b.name, recipe_type_b.revision_num, 'node_b', False)]
        message = create_subrecipes_messages(top_recipe, sub_recipes)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateRecipes.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # Check for new sub-recipes
        qry = RecipeNode.objects.select_related('sub_recipe')
        recipe_nodes = qry.filter(recipe_id=top_recipe.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_a')
        self.assertEqual(recipe_nodes[1].node_name, 'node_b')
        sub_recipe_a = recipe_nodes[0].sub_recipe
        sub_recipe_b = recipe_nodes[1].sub_recipe
        self.assertEqual(sub_recipe_a.recipe_type_id, recipe_type_a.id)
        self.assertIsNone(sub_recipe_a.superseded_recipe_id)
        self.assertEqual(sub_recipe_b.recipe_type_id, recipe_type_b.id)
        self.assertIsNone(sub_recipe_b.superseded_recipe_id)

        # Should be three messages, one for processing recipe input, one for updating a sub-recipe, and one for updating
        # metrics for the recipe containing the new sub-recipes
        self.assertEqual(len(new_message.new_messages), 3)
        process_recipe_input_msg = None
        update_metrics_msg = None
        update_recipe_msg = None
        for msg in new_message.new_messages:
            if msg.type == 'process_recipe_input':
                process_recipe_input_msg = msg
            elif msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(process_recipe_input_msg)
        self.assertIsNotNone(update_recipe_msg)
        self.assertIsNotNone(update_metrics_msg)
        # Check message to process recipe input for new sub-recipe A
        self.assertEqual(process_recipe_input_msg.recipe_id, sub_recipe_a.id)
        self.assertIsNone(process_recipe_input_msg.forced_nodes)
        # Check message to update new sub-recipe B
        self.assertEqual(update_recipe_msg.root_recipe_id, sub_recipe_b.id)
        self.assertIsNone(update_recipe_msg.forced_nodes)
        # Check message to update recipe metrics for the recipe containing the new sub-recipes
        self.assertListEqual(update_metrics_msg._recipe_ids, [top_recipe.id])

    def test_json_subrecipes_superseded(self):
        """Tests converting a CreateRecipes message to and from JSON when creating sub-recipes that supersede other
        sub-recipes
        """

        # Creates definitions for sub-recipe A and sub-recipe B
        batch = batch_test_utils.create_batch()
        event = trigger_test_utils.create_trigger_event()
        top_recipe_type = recipe_test_utils.create_recipe_type()
        job_type_a_1 = job_test_utils.create_seed_job_type()
        job_type_a_2 = job_test_utils.create_seed_job_type()
        sub_definition_a = RecipeDefinition(Interface())
        sub_definition_a.add_job_node('node_1', job_type_a_1.name, job_type_a_1.version, job_type_a_1.revision_num)
        sub_definition_a.add_job_node('node_2', job_type_a_2.name, job_type_a_2.version, job_type_a_2.revision_num)
        sub_definition_a.add_dependency('node_1', 'node_2')
        sub_definition_a_dict = convert_recipe_definition_to_v6_json(sub_definition_a).get_dict()
        recipe_type_a = recipe_test_utils.create_recipe_type(definition=sub_definition_a_dict)
        job_type_b_x = job_test_utils.create_seed_job_type()
        recipe_type_b_y = recipe_test_utils.create_recipe_type()
        sub_definition_b = RecipeDefinition(Interface())
        sub_definition_b.add_job_node('node_x', job_type_b_x.name, job_type_b_x.version, job_type_b_x.revision_num)
        sub_definition_b.add_recipe_node('node_y', recipe_type_b_y.name, recipe_type_b_y.revision_num)
        sub_definition_b.add_dependency('node_x', 'node_y')
        sub_definition_b_dict = convert_recipe_definition_to_v6_json(sub_definition_b).get_dict()
        recipe_type_b = recipe_test_utils.create_recipe_type(definition=sub_definition_b_dict)

        # Create previous recipe containing sub-recipe A and B in order to be superseded
        prev_recipe_a = recipe_test_utils.create_recipe(recipe_type=recipe_type_a, save=False)
        prev_job_a_1 = job_test_utils.create_job(job_type=job_type_a_1, save=False)
        prev_job_a_2 = job_test_utils.create_job(job_type=job_type_a_2, save=False)
        prev_recipe_b = recipe_test_utils.create_recipe(recipe_type=recipe_type_b, save=False)
        prev_job_b_x = job_test_utils.create_job(job_type=job_type_b_x, save=False)
        prev_recipe_b_y = recipe_test_utils.create_recipe(recipe_type=recipe_type_b_y, save=False)
        prev_top_recipe = recipe_test_utils.create_recipe(recipe_type=top_recipe_type, save=False)
        Job.objects.bulk_create([prev_job_a_1, prev_job_a_2, prev_job_b_x])
        Recipe.objects.bulk_create([prev_recipe_a, prev_recipe_b, prev_recipe_b_y, prev_top_recipe])
        new_top_recipe = recipe_test_utils.create_recipe(recipe_type=top_recipe_type, superseded_recipe=prev_top_recipe,
                                                         event=event, batch=batch, save=True)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=prev_top_recipe, sub_recipe=prev_recipe_a,
                                                             node_name='node_a', save=False)
        recipe_node_a_1 = recipe_test_utils.create_recipe_node(recipe=prev_recipe_a, job=prev_job_a_1,
                                                               node_name='node_1', save=False)
        recipe_node_a_2 = recipe_test_utils.create_recipe_node(recipe=prev_recipe_a, job=prev_job_a_2,
                                                               node_name='node_2', save=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=prev_top_recipe, sub_recipe=prev_recipe_b,
                                                             node_name='node_b', save=False)
        recipe_node_b_x = recipe_test_utils.create_recipe_node(recipe=prev_recipe_b, job=prev_job_b_x,
                                                               node_name='node_x', save=False)
        recipe_node_b_y = recipe_test_utils.create_recipe_node(recipe=prev_recipe_b, sub_recipe=prev_recipe_b_y,
                                                               node_name='node_y', save=False)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_a_1, recipe_node_a_2, recipe_node_b, recipe_node_b_x,
                                        recipe_node_b_y])

        # Create message to create sub-recipes A and B for new_top_recipe which supersedes prev_top_recipe
        sub_recipes = [SubRecipe(recipe_type_a.name, recipe_type_a.revision_num, 'node_a', True),
                       SubRecipe(recipe_type_b.name, recipe_type_b.revision_num, 'node_b', False)]
        forced_nodes = ForcedNodes()
        sub_forced_nodes_a = ForcedNodes()
        sub_forced_nodes_a.set_all_nodes()
        sub_forced_nodes_b = ForcedNodes()
        sub_forced_nodes_y = ForcedNodes()
        sub_forced_nodes_y.set_all_nodes()
        sub_forced_nodes_b.add_subrecipe('node_y', sub_forced_nodes_y)
        forced_nodes.add_subrecipe('node_a', sub_forced_nodes_a)
        forced_nodes.add_subrecipe('node_b', sub_forced_nodes_b)
        message = create_subrecipes_messages(new_top_recipe, sub_recipes, forced_nodes=forced_nodes)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = CreateRecipes.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # Check for new sub-recipes
        qry = RecipeNode.objects.select_related('sub_recipe')
        recipe_nodes = qry.filter(recipe_id=new_top_recipe.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_a')
        self.assertEqual(recipe_nodes[1].node_name, 'node_b')
        sub_recipe_a = recipe_nodes[0].sub_recipe
        sub_recipe_b = recipe_nodes[1].sub_recipe
        self.assertEqual(sub_recipe_a.recipe_type_id, recipe_type_a.id)
        self.assertEqual(sub_recipe_a.superseded_recipe_id, prev_recipe_a.id)
        self.assertEqual(sub_recipe_a.root_superseded_recipe_id, prev_recipe_a.id)
        self.assertEqual(sub_recipe_b.recipe_type_id, recipe_type_b.id)
        self.assertEqual(sub_recipe_b.superseded_recipe_id, prev_recipe_b.id)
        self.assertEqual(sub_recipe_b.root_superseded_recipe_id, prev_recipe_b.id)
        # Check for sub-recipes to contain correct copied nodes
        self.assertEqual(RecipeNode.objects.filter(recipe_id=sub_recipe_a.id).count(), 0)  # No copied nodes for A
        # Node X in sub-recipe B should be copied
        recipe_nodes = RecipeNode.objects.select_related('sub_recipe').filter(recipe_id=sub_recipe_b.id)
        self.assertEqual(len(recipe_nodes), 1)
        self.assertEqual(recipe_nodes[0].node_name, 'node_x')
        self.assertFalse(recipe_nodes[0].is_original)

        # Should be five messages, two for superseding recipe nodes, one for processing recipe input, one for updating
        # the other sub-recipe, and one for updating metrics for the recipe containing the new sub-recipes
        self.assertEqual(len(new_message.new_messages), 5)
        supersede_recipe_a_msg = None
        supersede_recipe_b_msg = None
        process_recipe_input_msg = None
        update_metrics_msg = None
        update_recipe_msg = None
        for msg in new_message.new_messages:
            if msg.type == 'supersede_recipe_nodes':
                if msg._recipe_ids[0] == prev_recipe_a.id:
                    supersede_recipe_a_msg = msg
                if msg._recipe_ids[0] == prev_recipe_b.id:
                    supersede_recipe_b_msg = msg
            elif msg.type == 'process_recipe_input':
                process_recipe_input_msg = msg
            elif msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(supersede_recipe_a_msg)
        self.assertIsNotNone(supersede_recipe_b_msg)
        self.assertIsNotNone(process_recipe_input_msg)
        self.assertIsNotNone(update_metrics_msg)
        self.assertIsNotNone(update_recipe_msg)
        # Check message for superseding previous sub-recipe A
        self.assertFalse(supersede_recipe_a_msg.supersede_all)
        self.assertSetEqual(supersede_recipe_a_msg.supersede_jobs, {'node_1', 'node_2'})
        self.assertSetEqual(supersede_recipe_a_msg.supersede_subrecipes, set())
        self.assertFalse(supersede_recipe_a_msg.unpublish_all)
        self.assertSetEqual(supersede_recipe_a_msg.unpublish_jobs, set())
        self.assertFalse(supersede_recipe_a_msg.supersede_recursive_all)
        self.assertSetEqual(supersede_recipe_a_msg.supersede_recursive, set())
        self.assertFalse(supersede_recipe_a_msg.unpublish_recursive_all)
        self.assertSetEqual(supersede_recipe_a_msg.unpublish_recursive, set())
        # Check message for superseding previous sub-recipe B
        self.assertFalse(supersede_recipe_b_msg.supersede_all)
        self.assertSetEqual(supersede_recipe_b_msg.supersede_jobs, set())
        self.assertSetEqual(supersede_recipe_b_msg.supersede_subrecipes, {'node_y'})
        self.assertFalse(supersede_recipe_b_msg.unpublish_all)
        self.assertSetEqual(supersede_recipe_b_msg.unpublish_jobs, set())
        self.assertFalse(supersede_recipe_b_msg.supersede_recursive_all)
        self.assertSetEqual(supersede_recipe_b_msg.supersede_recursive, set())
        self.assertFalse(supersede_recipe_b_msg.unpublish_recursive_all)
        self.assertSetEqual(supersede_recipe_b_msg.unpublish_recursive, set())
        # Check message to process recipe input for new sub-recipe A
        self.assertEqual(process_recipe_input_msg.recipe_id, sub_recipe_a.id)
        msg_forced_nodes = convert_forced_nodes_to_v6(process_recipe_input_msg.forced_nodes).get_dict()
        forced_nodes_a_dict = convert_forced_nodes_to_v6(sub_forced_nodes_a).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_a_dict)
        # Check message to update new sub-recipe B
        self.assertEqual(update_recipe_msg.root_recipe_id, sub_recipe_b.root_superseded_recipe_id)
        msg_forced_nodes = convert_forced_nodes_to_v6(update_recipe_msg.forced_nodes).get_dict()
        forced_nodes_b_dict = convert_forced_nodes_to_v6(sub_forced_nodes_b).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_b_dict)
        # Check message to update recipe metrics for the recipe containing the new sub-recipes
        self.assertListEqual(update_metrics_msg._recipe_ids, [new_top_recipe.id])

    def test_execute_reprocess(self):
        """Tests calling CreateRecipes.execute() successfully when reprocessing recipes"""

        file_1 = storage_test_utils.create_file()
        file_2 = storage_test_utils.create_file()

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
        job_type_1 = job_test_utils.create_job_type(interface=interface_1)

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
        job_type_2 = job_test_utils.create_job_type(interface=interface_2)

        recipe_interface = Interface()
        recipe_interface.add_parameter(FileParameter('Recipe Input', ['text/plain']))
        definition = RecipeDefinition(recipe_interface)
        definition.add_job_node('Job 1', job_type_1.name, job_type_1.version, job_type_1.revision_num)
        definition.add_recipe_input_connection('Job 1', 'Test Input 1', 'Recipe Input')
        definition.add_job_node('Job 2', job_type_2.name, job_type_2.version, job_type_2.revision_num)
        definition.add_dependency('Job 1', 'Job 2')
        definition.add_dependency_input_connection('Job 2', 'Test Input 2', 'Job 1', 'Test Output 1')
        definition_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_dict)

        input_1 = Data()
        input_1.add_value(FileValue('Recipe Input', [file_1.id]))
        input_1_dict = convert_data_to_v6_json(input_1).get_dict()
        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=input_1_dict)
        job_1_1 = job_test_utils.create_job(job_type=job_type_1, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job_name='Job 1', job=job_1_1)
        job_1_2 = job_test_utils.create_job(job_type=job_type_2, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_1, job_name='Job 2', job=job_1_2)

        input_2 = Data()
        input_2.add_value(FileValue('Recipe Input', [file_2.id]))
        input_2_dict = convert_data_to_v6_json(input_2).get_dict()
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=input_2_dict)
        job_2_1 = job_test_utils.create_job(job_type=job_type_1, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job_name='Job 1', job=job_2_1)
        job_2_2 = job_test_utils.create_job(job_type=job_type_2, status='COMPLETED')
        recipe_test_utils.create_recipe_job(recipe=recipe_2, job_name='Job 2', job=job_2_2)

        event = trigger_test_utils.create_trigger_event()
        batch = batch_test_utils.create_batch()
        forced_nodes = ForcedNodes()
        forced_nodes.add_node('Job 2')

        # Create and execute message to reprocess recipe 1 and 2
        reprocess_recipe_ids = [recipe_1.id, recipe_2.id]
        copied_job_ids = [job_1_1.id, job_2_1.id]
        message = create_reprocess_messages(reprocess_recipe_ids, recipe_1.recipe_type.name,
                                            recipe_1.recipe_type.revision_num, event.id, batch_id=batch.id,
                                            forced_nodes=forced_nodes)[0]
        result = message.execute()
        self.assertTrue(result)

        # Make sure new recipes supersede the old ones
        for recipe in Recipe.objects.filter(id__in=reprocess_recipe_ids):
            self.assertTrue(recipe.is_superseded)
        new_recipe_1 = Recipe.objects.get(superseded_recipe_id=recipe_1.id)
        self.assertEqual(new_recipe_1.batch_id, batch.id)
        self.assertEqual(new_recipe_1.event_id, event.id)
        self.assertDictEqual(new_recipe_1.input, recipe_1.input)
        new_recipe_2 = Recipe.objects.get(superseded_recipe_id=recipe_2.id)
        self.assertEqual(new_recipe_2.batch_id, batch.id)
        self.assertEqual(new_recipe_2.event_id, event.id)
        self.assertDictEqual(new_recipe_2.input, recipe_2.input)
        # Job 1 was not force reprocessed so it should be copied to the new recipes
        for job in Job.objects.filter(id__in=copied_job_ids):
            self.assertFalse(job.is_superseded)
        recipe_nodes = RecipeNode.objects.filter(recipe_id__in=[new_recipe_1.id, new_recipe_2.id])
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            if recipe_node.recipe_id == new_recipe_1.id:
                self.assertEqual(recipe_node.job_id, job_1_1.id)
            elif recipe_node.recipe_id == new_recipe_2.id:
                self.assertEqual(recipe_node.job_id, job_2_1.id)
            self.assertFalse(recipe_node.is_original)

        # Should be three messages, one for superseding recipe nodes and two for processing recipe input
        self.assertEqual(len(message.new_messages), 3)
        supersede_recipe_msg = None
        process_recipe_input_1_msg = None
        process_recipe_input_2_msg = None
        for msg in message.new_messages:
            if msg.type == 'supersede_recipe_nodes':
                supersede_recipe_msg = msg
            elif msg.type == 'process_recipe_input':
                if msg.recipe_id == new_recipe_1.id:
                    process_recipe_input_1_msg = msg
                if msg.recipe_id == new_recipe_2.id:
                    process_recipe_input_2_msg = msg
        self.assertIsNotNone(supersede_recipe_msg)
        self.assertIsNotNone(process_recipe_input_1_msg)
        self.assertIsNotNone(process_recipe_input_2_msg)
        # Check message for superseding recipes 1 and 2
        self.assertListEqual(supersede_recipe_msg._recipe_ids, reprocess_recipe_ids)
        self.assertFalse(supersede_recipe_msg.supersede_all)
        self.assertSetEqual(supersede_recipe_msg.supersede_jobs, {'Job 2'})
        self.assertSetEqual(supersede_recipe_msg.supersede_subrecipes, set())
        self.assertFalse(supersede_recipe_msg.unpublish_all)
        self.assertSetEqual(supersede_recipe_msg.unpublish_jobs, set())
        self.assertFalse(supersede_recipe_msg.supersede_recursive_all)
        self.assertSetEqual(supersede_recipe_msg.supersede_recursive, set())
        self.assertFalse(supersede_recipe_msg.unpublish_recursive_all)
        self.assertSetEqual(supersede_recipe_msg.unpublish_recursive, set())
        # Check message to process recipe input for new recipe 1
        self.assertEqual(process_recipe_input_1_msg.recipe_id, new_recipe_1.id)
        msg_forced_nodes = convert_forced_nodes_to_v6(process_recipe_input_1_msg.forced_nodes).get_dict()
        forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_dict)
        # Check message to process recipe input for new recipe 2
        self.assertEqual(process_recipe_input_2_msg.recipe_id, new_recipe_2.id)
        msg_forced_nodes = convert_forced_nodes_to_v6(process_recipe_input_2_msg.forced_nodes).get_dict()
        forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_dict)

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateRecipes.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Make sure new recipes supersede the old ones
        for recipe in Recipe.objects.filter(id__in=reprocess_recipe_ids):
            self.assertTrue(recipe.is_superseded)
        new_recipe_1 = Recipe.objects.get(superseded_recipe_id=recipe_1.id)
        self.assertEqual(new_recipe_1.batch_id, batch.id)
        self.assertEqual(new_recipe_1.event_id, event.id)
        self.assertDictEqual(new_recipe_1.input, recipe_1.input)
        new_recipe_2 = Recipe.objects.get(superseded_recipe_id=recipe_2.id)
        self.assertEqual(new_recipe_2.batch_id, batch.id)
        self.assertEqual(new_recipe_2.event_id, event.id)
        self.assertDictEqual(new_recipe_2.input, recipe_2.input)
        # Job 1 was not force reprocessed so it should be copied to the new recipes
        for job in Job.objects.filter(id__in=copied_job_ids):
            self.assertFalse(job.is_superseded)
        recipe_nodes = RecipeNode.objects.filter(recipe_id__in=[new_recipe_1.id, new_recipe_2.id])
        self.assertEqual(len(recipe_nodes), 2)
        for recipe_node in recipe_nodes:
            if recipe_node.recipe_id == new_recipe_1.id:
                self.assertEqual(recipe_node.job_id, job_1_1.id)
            elif recipe_node.recipe_id == new_recipe_2.id:
                self.assertEqual(recipe_node.job_id, job_2_1.id)
            self.assertFalse(recipe_node.is_original)

        # Check messages again
        # Should be three messages, one for superseding recipe nodes and two for processing recipe input
        self.assertEqual(len(message.new_messages), 3)
        supersede_recipe_msg = None
        process_recipe_input_1_msg = None
        process_recipe_input_2_msg = None
        for msg in message.new_messages:
            if msg.type == 'supersede_recipe_nodes':
                supersede_recipe_msg = msg
            elif msg.type == 'process_recipe_input':
                if msg.recipe_id == new_recipe_1.id:
                    process_recipe_input_1_msg = msg
                if msg.recipe_id == new_recipe_2.id:
                    process_recipe_input_2_msg = msg
        self.assertIsNotNone(supersede_recipe_msg)
        self.assertIsNotNone(process_recipe_input_1_msg)
        self.assertIsNotNone(process_recipe_input_2_msg)
        # Check message for superseding recipes 1 and 2
        self.assertListEqual(supersede_recipe_msg._recipe_ids, reprocess_recipe_ids)
        self.assertFalse(supersede_recipe_msg.supersede_all)
        self.assertSetEqual(supersede_recipe_msg.supersede_jobs, {'Job 2'})
        self.assertSetEqual(supersede_recipe_msg.supersede_subrecipes, set())
        self.assertFalse(supersede_recipe_msg.unpublish_all)
        self.assertSetEqual(supersede_recipe_msg.unpublish_jobs, set())
        self.assertFalse(supersede_recipe_msg.supersede_recursive_all)
        self.assertSetEqual(supersede_recipe_msg.supersede_recursive, set())
        self.assertFalse(supersede_recipe_msg.unpublish_recursive_all)
        self.assertSetEqual(supersede_recipe_msg.unpublish_recursive, set())
        # Check message to process recipe input for new recipe 1
        self.assertEqual(process_recipe_input_1_msg.recipe_id, new_recipe_1.id)
        msg_forced_nodes = convert_forced_nodes_to_v6(process_recipe_input_1_msg.forced_nodes).get_dict()
        forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_dict)
        # Check message to process recipe input for new recipe 2
        self.assertEqual(process_recipe_input_2_msg.recipe_id, new_recipe_2.id)
        msg_forced_nodes = convert_forced_nodes_to_v6(process_recipe_input_2_msg.forced_nodes).get_dict()
        forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_dict)

    def test_execute_subrecipes(self):
        """Tests calling CreateRecipes.execute() successfully when creating sub-recipes"""

        # Creates definitions for sub-recipe A and sub-recipe B
        top_recipe_type = recipe_test_utils.create_recipe_type()
        job_type_a_1 = job_test_utils.create_seed_job_type()
        job_type_a_2 = job_test_utils.create_seed_job_type()
        sub_definition_a = RecipeDefinition(Interface())
        sub_definition_a.add_job_node('node_1', job_type_a_1.name, job_type_a_1.version, job_type_a_1.revision_num)
        sub_definition_a.add_job_node('node_2', job_type_a_2.name, job_type_a_2.version, job_type_a_2.revision_num)
        sub_definition_a.add_dependency('node_1', 'node_2')
        sub_definition_a_dict = convert_recipe_definition_to_v6_json(sub_definition_a).get_dict()
        recipe_type_a = recipe_test_utils.create_recipe_type(definition=sub_definition_a_dict)
        job_type_b_x = job_test_utils.create_seed_job_type()
        job_type_b_y = job_test_utils.create_seed_job_type()
        recipe_type_b_z = recipe_test_utils.create_recipe_type()
        sub_definition_b = RecipeDefinition(Interface())
        sub_definition_b.add_job_node('node_x', job_type_b_x.name, job_type_b_x.version, job_type_b_x.revision_num)
        sub_definition_b.add_job_node('node_y', job_type_b_y.name, job_type_b_y.version, job_type_b_y.revision_num)
        sub_definition_b.add_recipe_node('node_z', recipe_type_b_z.name, recipe_type_b_z.revision_num)
        sub_definition_b.add_dependency('node_x', 'node_z')
        sub_definition_b.add_dependency('node_y', 'node_z')
        sub_definition_b_dict = convert_recipe_definition_to_v6_json(sub_definition_b).get_dict()
        recipe_type_b = recipe_test_utils.create_recipe_type(definition=sub_definition_b_dict)
        top_recipe = recipe_test_utils.create_recipe(recipe_type=top_recipe_type, save=True)

        # Create message to create sub-recipes A and B for top_recipe which supersedes prev_top_recipe
        sub_recipes = [SubRecipe(recipe_type_a.name, recipe_type_a.revision_num, 'node_a', True),
                       SubRecipe(recipe_type_b.name, recipe_type_b.revision_num, 'node_b', False)]
        message = create_subrecipes_messages(top_recipe, sub_recipes)[0]

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check for new sub-recipes
        qry = RecipeNode.objects.select_related('sub_recipe')
        recipe_nodes = qry.filter(recipe_id=top_recipe.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_a')
        self.assertEqual(recipe_nodes[1].node_name, 'node_b')
        sub_recipe_a = recipe_nodes[0].sub_recipe
        sub_recipe_b = recipe_nodes[1].sub_recipe
        self.assertEqual(sub_recipe_a.recipe_type_id, recipe_type_a.id)
        self.assertIsNone(sub_recipe_a.superseded_recipe_id)
        self.assertEqual(sub_recipe_b.recipe_type_id, recipe_type_b.id)
        self.assertIsNone(sub_recipe_b.superseded_recipe_id)

        # Should be three messages, one for processing recipe input, one for updating a sub-recipe, and one for updating
        # metrics for the recipe containing the new sub-recipes
        self.assertEqual(len(message.new_messages), 3)
        process_recipe_input_msg = None
        update_metrics_msg = None
        update_recipe_msg = None
        for msg in message.new_messages:
            if msg.type == 'process_recipe_input':
                process_recipe_input_msg = msg
            elif msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(process_recipe_input_msg)
        self.assertIsNotNone(update_recipe_msg)
        self.assertIsNotNone(update_metrics_msg)
        # Check message to process recipe input for new sub-recipe A
        self.assertEqual(process_recipe_input_msg.recipe_id, sub_recipe_a.id)
        self.assertIsNone(process_recipe_input_msg.forced_nodes)
        # Check message to update new sub-recipe B
        self.assertEqual(update_recipe_msg.root_recipe_id, sub_recipe_b.id)
        self.assertIsNone(update_recipe_msg.forced_nodes)
        # Check message to update recipe metrics for the recipe containing the new sub-recipes
        self.assertListEqual(update_metrics_msg._recipe_ids, [top_recipe.id])

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateRecipes.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Check sub-recipes to make sure we didn't create them again a second time
        qry = RecipeNode.objects.select_related('sub_recipe')
        recipe_nodes = qry.filter(recipe_id=top_recipe.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_a')
        self.assertEqual(recipe_nodes[1].node_name, 'node_b')
        sub_recipe_a = recipe_nodes[0].sub_recipe
        sub_recipe_b = recipe_nodes[1].sub_recipe
        self.assertEqual(sub_recipe_a.recipe_type_id, recipe_type_a.id)
        self.assertIsNone(sub_recipe_a.superseded_recipe_id)
        self.assertEqual(sub_recipe_b.recipe_type_id, recipe_type_b.id)
        self.assertIsNone(sub_recipe_b.superseded_recipe_id)

        # Check messages again
        # Should be three messages, one for processing recipe input, one for updating a sub-recipe, and one for updating
        # metrics for the recipe containing the new sub-recipes
        self.assertEqual(len(message.new_messages), 3)
        process_recipe_input_msg = None
        update_metrics_msg = None
        update_recipe_msg = None
        for msg in message.new_messages:
            if msg.type == 'process_recipe_input':
                process_recipe_input_msg = msg
            elif msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(process_recipe_input_msg)
        self.assertIsNotNone(update_recipe_msg)
        self.assertIsNotNone(update_metrics_msg)
        # Check message to process recipe input for new sub-recipe A
        self.assertEqual(process_recipe_input_msg.recipe_id, sub_recipe_a.id)
        self.assertIsNone(process_recipe_input_msg.forced_nodes)
        # Check message to update new sub-recipe B
        self.assertEqual(update_recipe_msg.root_recipe_id, sub_recipe_b.id)
        self.assertIsNone(update_recipe_msg.forced_nodes)
        # Check message to update recipe metrics for the recipe containing the new sub-recipes
        self.assertListEqual(update_metrics_msg._recipe_ids, [top_recipe.id])

    def test_execute_subrecipes_superseded(self):
        """Tests calling CreateRecipes.execute() successfully when creating sub-recipes that supersede other sub-recipes
        """

        # Creates definitions for sub-recipe A and sub-recipe B
        batch = batch_test_utils.create_batch()
        event = trigger_test_utils.create_trigger_event()
        top_recipe_type = recipe_test_utils.create_recipe_type()
        job_type_a_1 = job_test_utils.create_seed_job_type()
        job_type_a_2 = job_test_utils.create_seed_job_type()
        sub_definition_a = RecipeDefinition(Interface())
        sub_definition_a.add_job_node('node_1', job_type_a_1.name, job_type_a_1.version, job_type_a_1.revision_num)
        sub_definition_a.add_job_node('node_2', job_type_a_2.name, job_type_a_2.version, job_type_a_2.revision_num)
        sub_definition_a.add_dependency('node_1', 'node_2')
        sub_definition_a_dict = convert_recipe_definition_to_v6_json(sub_definition_a).get_dict()
        recipe_type_a = recipe_test_utils.create_recipe_type(definition=sub_definition_a_dict)
        job_type_b_x = job_test_utils.create_seed_job_type()
        job_type_b_y = job_test_utils.create_seed_job_type()
        recipe_type_b_z = recipe_test_utils.create_recipe_type()
        sub_definition_b = RecipeDefinition(Interface())
        sub_definition_b.add_job_node('node_x', job_type_b_x.name, job_type_b_x.version, job_type_b_x.revision_num)
        sub_definition_b.add_job_node('node_y', job_type_b_y.name, job_type_b_y.version, job_type_b_y.revision_num)
        sub_definition_b.add_recipe_node('node_z', recipe_type_b_z.name, recipe_type_b_z.revision_num)
        sub_definition_b.add_dependency('node_x', 'node_z')
        sub_definition_b.add_dependency('node_y', 'node_z')
        sub_definition_b_dict = convert_recipe_definition_to_v6_json(sub_definition_b).get_dict()
        recipe_type_b = recipe_test_utils.create_recipe_type(definition=sub_definition_b_dict)

        # Create previous recipe containing sub-recipe A and B in order to be superseded
        prev_recipe_a = recipe_test_utils.create_recipe(recipe_type=recipe_type_a, save=False)
        prev_job_a_1 = job_test_utils.create_job(job_type=job_type_a_1, save=False)
        prev_job_a_2 = job_test_utils.create_job(job_type=job_type_a_2, save=False)
        prev_recipe_b = recipe_test_utils.create_recipe(recipe_type=recipe_type_b, save=False)
        prev_job_b_x = job_test_utils.create_job(job_type=job_type_b_x, save=False)
        prev_job_b_y = job_test_utils.create_job(job_type=job_type_b_y, save=False)
        prev_recipe_b_z = recipe_test_utils.create_recipe(recipe_type=recipe_type_b_z, save=False)
        prev_top_recipe = recipe_test_utils.create_recipe(recipe_type=top_recipe_type, save=False)
        Job.objects.bulk_create([prev_job_a_1, prev_job_a_2, prev_job_b_x, prev_job_b_y])
        Recipe.objects.bulk_create([prev_recipe_a, prev_recipe_b, prev_recipe_b_z, prev_top_recipe])
        new_top_recipe = recipe_test_utils.create_recipe(recipe_type=top_recipe_type, superseded_recipe=prev_top_recipe,
                                                         event=event, batch=batch, save=True)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=prev_top_recipe, sub_recipe=prev_recipe_a,
                                                             node_name='node_a', save=False)
        recipe_node_a_1 = recipe_test_utils.create_recipe_node(recipe=prev_recipe_a, job=prev_job_a_1,
                                                               node_name='node_1', save=False)
        recipe_node_a_2 = recipe_test_utils.create_recipe_node(recipe=prev_recipe_a, job=prev_job_a_2,
                                                               node_name='node_2', save=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=prev_top_recipe, sub_recipe=prev_recipe_b,
                                                             node_name='node_b', save=False)
        recipe_node_b_x = recipe_test_utils.create_recipe_node(recipe=prev_recipe_b, job=prev_job_b_x,
                                                               node_name='node_x', save=False)
        recipe_node_b_y = recipe_test_utils.create_recipe_node(recipe=prev_recipe_b, job=prev_job_b_y,
                                                               node_name='node_y', save=False)
        recipe_node_b_z = recipe_test_utils.create_recipe_node(recipe=prev_recipe_b, sub_recipe=prev_recipe_b_z,
                                                               node_name='node_z', save=False)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_a_1, recipe_node_a_2, recipe_node_b, recipe_node_b_x,
                                        recipe_node_b_y, recipe_node_b_z])

        # Create message to create sub-recipes A and B for new_top_recipe which supersedes prev_top_recipe
        sub_recipes = [SubRecipe(recipe_type_a.name, recipe_type_a.revision_num, 'node_a', True),
                       SubRecipe(recipe_type_b.name, recipe_type_b.revision_num, 'node_b', False)]
        forced_nodes = ForcedNodes()
        sub_forced_nodes_b = ForcedNodes()
        sub_forced_nodes_y = ForcedNodes()
        sub_forced_nodes_b.add_subrecipe('node_y', sub_forced_nodes_y)
        forced_nodes.add_subrecipe('node_b', sub_forced_nodes_b)
        message = create_subrecipes_messages(new_top_recipe, sub_recipes, forced_nodes=forced_nodes)[0]

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Check for new sub-recipes
        qry = RecipeNode.objects.select_related('sub_recipe')
        recipe_nodes = qry.filter(recipe_id=new_top_recipe.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_a')
        self.assertEqual(recipe_nodes[1].node_name, 'node_b')
        sub_recipe_a = recipe_nodes[0].sub_recipe
        sub_recipe_b = recipe_nodes[1].sub_recipe
        self.assertEqual(sub_recipe_a.recipe_type_id, recipe_type_a.id)
        self.assertEqual(sub_recipe_a.superseded_recipe_id, prev_recipe_a.id)
        self.assertEqual(sub_recipe_a.root_superseded_recipe_id, prev_recipe_a.id)
        self.assertEqual(sub_recipe_b.recipe_type_id, recipe_type_b.id)
        self.assertEqual(sub_recipe_b.superseded_recipe_id, prev_recipe_b.id)
        self.assertEqual(sub_recipe_b.root_superseded_recipe_id, prev_recipe_b.id)
        # Check for sub-recipes to contain correct copied nodes
        # Nodes 1 and 2 in sub-recipe A should be copied
        recipe_nodes = RecipeNode.objects.select_related('job').filter(recipe_id=sub_recipe_a.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_1')
        self.assertFalse(recipe_nodes[0].is_original)
        self.assertEqual(recipe_nodes[0].job_id, prev_job_a_1.id)
        self.assertEqual(recipe_nodes[1].node_name, 'node_2')
        self.assertFalse(recipe_nodes[1].is_original)
        self.assertEqual(recipe_nodes[1].job_id, prev_job_a_2.id)
        # Node X in sub-recipe B should be copied
        recipe_nodes = RecipeNode.objects.select_related('sub_recipe').filter(recipe_id=sub_recipe_b.id)
        self.assertEqual(len(recipe_nodes), 1)
        self.assertEqual(recipe_nodes[0].node_name, 'node_x')
        self.assertFalse(recipe_nodes[0].is_original)

        # Should be four messages, one for superseding recipe B nodes, one for processing recipe input, one for updating
        # the other sub-recipe, and one for updating metrics for the recipe containing the new sub-recipes
        self.assertEqual(len(message.new_messages), 4)
        supersede_recipe_b_msg = None
        process_recipe_input_msg = None
        update_metrics_msg = None
        update_recipe_msg = None
        for msg in message.new_messages:
            if msg.type == 'supersede_recipe_nodes':
                if msg._recipe_ids[0] == prev_recipe_b.id:
                    supersede_recipe_b_msg = msg
            elif msg.type == 'process_recipe_input':
                process_recipe_input_msg = msg
            elif msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(supersede_recipe_b_msg)
        self.assertIsNotNone(process_recipe_input_msg)
        self.assertIsNotNone(update_metrics_msg)
        self.assertIsNotNone(update_recipe_msg)
        # Check message for superseding previous sub-recipe B
        self.assertFalse(supersede_recipe_b_msg.supersede_all)
        self.assertSetEqual(supersede_recipe_b_msg.supersede_jobs, {'node_y'})
        self.assertSetEqual(supersede_recipe_b_msg.supersede_subrecipes, {'node_z'})
        self.assertFalse(supersede_recipe_b_msg.unpublish_all)
        self.assertSetEqual(supersede_recipe_b_msg.unpublish_jobs, set())
        self.assertFalse(supersede_recipe_b_msg.supersede_recursive_all)
        self.assertSetEqual(supersede_recipe_b_msg.supersede_recursive, {'node_z'})
        self.assertFalse(supersede_recipe_b_msg.unpublish_recursive_all)
        self.assertSetEqual(supersede_recipe_b_msg.unpublish_recursive, set())
        # Check message to process recipe input for new sub-recipe A
        self.assertEqual(process_recipe_input_msg.recipe_id, sub_recipe_a.id)
        self.assertIsNone(process_recipe_input_msg.forced_nodes)
        # Check message to update new sub-recipe B
        self.assertEqual(update_recipe_msg.root_recipe_id, sub_recipe_b.root_superseded_recipe_id)
        msg_forced_nodes = convert_forced_nodes_to_v6(update_recipe_msg.forced_nodes).get_dict()
        forced_nodes_b_dict = convert_forced_nodes_to_v6(sub_forced_nodes_b).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_b_dict)
        # Check message to update recipe metrics for the recipe containing the new sub-recipes
        self.assertListEqual(update_metrics_msg._recipe_ids, [new_top_recipe.id])

        # Test executing message again
        message_json_dict = message.to_json()
        message = CreateRecipes.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Check sub-recipes to make sure we didn't create them again a second time
        qry = RecipeNode.objects.select_related('sub_recipe')
        recipe_nodes = qry.filter(recipe_id=new_top_recipe.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_a')
        self.assertEqual(recipe_nodes[1].node_name, 'node_b')
        sub_recipe_a = recipe_nodes[0].sub_recipe
        sub_recipe_b = recipe_nodes[1].sub_recipe
        self.assertEqual(sub_recipe_a.recipe_type_id, recipe_type_a.id)
        self.assertEqual(sub_recipe_a.superseded_recipe_id, prev_recipe_a.id)
        self.assertEqual(sub_recipe_a.root_superseded_recipe_id, prev_recipe_a.id)
        self.assertEqual(sub_recipe_b.recipe_type_id, recipe_type_b.id)
        self.assertEqual(sub_recipe_b.superseded_recipe_id, prev_recipe_b.id)
        self.assertEqual(sub_recipe_b.root_superseded_recipe_id, prev_recipe_b.id)
        # Check for sub-recipes to contain correct copied nodes
        # Nodes 1 and 2 in sub-recipe A should be copied
        recipe_nodes = RecipeNode.objects.select_related('job').filter(recipe_id=sub_recipe_a.id).order_by('node_name')
        self.assertEqual(len(recipe_nodes), 2)
        self.assertEqual(recipe_nodes[0].node_name, 'node_1')
        self.assertFalse(recipe_nodes[0].is_original)
        self.assertEqual(recipe_nodes[0].job_id, prev_job_a_1.id)
        self.assertEqual(recipe_nodes[1].node_name, 'node_2')
        self.assertFalse(recipe_nodes[1].is_original)
        self.assertEqual(recipe_nodes[1].job_id, prev_job_a_2.id)
        # Node X in sub-recipe B should be copied
        recipe_nodes = RecipeNode.objects.select_related('sub_recipe').filter(recipe_id=sub_recipe_b.id)
        self.assertEqual(len(recipe_nodes), 1)
        self.assertEqual(recipe_nodes[0].node_name, 'node_x')
        self.assertFalse(recipe_nodes[0].is_original)

        # Check messages again
        # Should be four messages, one for superseding recipe B nodes, one for processing recipe input, one for updating
        # the other sub-recipe, and one for updating metrics for the recipe containing the new sub-recipes
        self.assertEqual(len(message.new_messages), 4)
        supersede_recipe_b_msg = None
        process_recipe_input_msg = None
        update_metrics_msg = None
        update_recipe_msg = None
        for msg in message.new_messages:
            if msg.type == 'supersede_recipe_nodes':
                if msg._recipe_ids[0] == prev_recipe_b.id:
                    supersede_recipe_b_msg = msg
            elif msg.type == 'process_recipe_input':
                process_recipe_input_msg = msg
            elif msg.type == 'update_recipe':
                update_recipe_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(supersede_recipe_b_msg)
        self.assertIsNotNone(process_recipe_input_msg)
        self.assertIsNotNone(update_metrics_msg)
        self.assertIsNotNone(update_recipe_msg)
        # Check message for superseding previous sub-recipe B
        self.assertFalse(supersede_recipe_b_msg.supersede_all)
        self.assertSetEqual(supersede_recipe_b_msg.supersede_jobs, {'node_y'})
        self.assertSetEqual(supersede_recipe_b_msg.supersede_subrecipes, {'node_z'})
        self.assertFalse(supersede_recipe_b_msg.unpublish_all)
        self.assertSetEqual(supersede_recipe_b_msg.unpublish_jobs, set())
        self.assertFalse(supersede_recipe_b_msg.supersede_recursive_all)
        self.assertSetEqual(supersede_recipe_b_msg.supersede_recursive, {'node_z'})
        self.assertFalse(supersede_recipe_b_msg.unpublish_recursive_all)
        self.assertSetEqual(supersede_recipe_b_msg.unpublish_recursive, set())
        # Check message to process recipe input for new sub-recipe A
        self.assertEqual(process_recipe_input_msg.recipe_id, sub_recipe_a.id)
        self.assertIsNone(process_recipe_input_msg.forced_nodes)
        # Check message to update new sub-recipe B
        self.assertEqual(update_recipe_msg.root_recipe_id, sub_recipe_b.root_superseded_recipe_id)
        msg_forced_nodes = convert_forced_nodes_to_v6(update_recipe_msg.forced_nodes).get_dict()
        forced_nodes_b_dict = convert_forced_nodes_to_v6(sub_forced_nodes_b).get_dict()
        self.assertDictEqual(msg_forced_nodes, forced_nodes_b_dict)
        # Check message to update recipe metrics for the recipe containing the new sub-recipes
        self.assertListEqual(update_metrics_msg._recipe_ids, [new_top_recipe.id])
