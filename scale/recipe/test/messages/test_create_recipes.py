from __future__ import unicode_literals

import django
from django.test import TestCase

from batch.test import utils as batch_test_utils
from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.data.value import FileValue
from data.interface.interface import Interface
from data.interface.parameter import FileParameter
from job.models import Job, JobType, JobTypeRevision
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.diff.forced_nodes import ForcedNodes
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6
from recipe.messages.create_recipes import create_reprocess_messages, create_subrecipes_messages, CreateRecipes, \
    SubRecipe
from recipe.models import Recipe, RecipeNode, RecipeType, RecipeTypeRevision
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

    def test_execute_entire_reprocess(self):
        """Tests performing an entire reprocess by starting with a reprocess create_recipes message and executing all
        resulting messages
        """

        event = trigger_test_utils.create_trigger_event()
        batch = batch_test_utils.create_batch()
        forced_nodes_b = ForcedNodes()
        forced_nodes_b.add_node('job_b_y')
        forced_nodes_a = ForcedNodes()
        forced_nodes_a.add_subrecipe('recipe_b', forced_nodes_b)

        # Set up recipe type E
        job_type_e_x = job_test_utils.create_seed_job_type()
        job_type_e_y = job_test_utils.create_seed_job_type()
        definition_e = RecipeDefinition(Interface())
        definition_e.add_job_node('job_e_x', job_type_e_x.name, job_type_e_x.version, job_type_e_x.revision_num)
        definition_e.add_job_node('job_e_y', job_type_e_y.name, job_type_e_y.version, job_type_e_y.revision_num)
        definition_e.add_dependency('job_e_x', 'job_e_y')
        definition_e_dict = convert_recipe_definition_to_v6_json(definition_e).get_dict()
        recipe_type_e = recipe_test_utils.create_recipe_type(definition=definition_e_dict)

        # Set up recipe type D
        job_type_d_x = job_test_utils.create_seed_job_type()
        job_type_d_y = job_test_utils.create_seed_job_type()
        job_type_d_z = job_test_utils.create_seed_job_type()
        definition_d = RecipeDefinition(Interface())
        definition_d.add_job_node('job_d_x', job_type_d_x.name, job_type_d_x.version, job_type_d_x.revision_num)
        definition_d.add_job_node('job_d_y', job_type_d_y.name, job_type_d_y.version, job_type_d_y.revision_num)
        definition_d.add_job_node('job_d_z', job_type_d_z.name, job_type_d_z.version, job_type_d_z.revision_num)
        definition_d.add_dependency('job_d_x', 'job_d_y')
        definition_d.add_dependency('job_d_x', 'job_d_z')
        definition_d_dict = convert_recipe_definition_to_v6_json(definition_d).get_dict()
        recipe_type_d = recipe_test_utils.create_recipe_type(definition=definition_d_dict)

        # Set up recipe type C (with revision change CC)
        job_type_c_x = job_test_utils.create_seed_job_type()
        job_type_c_y = job_test_utils.create_seed_job_type()
        job_type_c_z = job_test_utils.create_seed_job_type()
        definition_c = RecipeDefinition(Interface())
        definition_c.add_job_node('job_c_x', job_type_c_x.name, job_type_c_x.version, job_type_c_x.revision_num)
        definition_c.add_job_node('job_c_y', job_type_c_y.name, job_type_c_y.version, job_type_c_y.revision_num)
        definition_c.add_job_node('job_c_z', job_type_c_z.name, job_type_c_z.version, job_type_c_z.revision_num)
        definition_c.add_dependency('job_c_x', 'job_c_z')
        definition_c.add_dependency('job_c_y', 'job_c_z')
        definition_c_dict = convert_recipe_definition_to_v6_json(definition_c).get_dict()
        recipe_type_c = recipe_test_utils.create_recipe_type(definition=definition_c_dict)
        job_type_cc_y = JobType.objects.get(id=job_type_c_y.id)
        job_type_cc_y.revision_num += 1
        JobTypeRevision.objects.create_job_type_revision(job_type_cc_y)
        definition_cc = RecipeDefinition(Interface())
        definition_cc.add_job_node('job_c_x', job_type_c_x.name, job_type_c_x.version, job_type_c_x.revision_num)
        definition_cc.add_job_node('job_c_y', job_type_cc_y.name, job_type_cc_y.version, job_type_cc_y.revision_num)
        definition_cc.add_job_node('job_c_z', job_type_c_z.name, job_type_c_z.version, job_type_c_z.revision_num)
        definition_cc.add_dependency('job_c_x', 'job_c_z')
        definition_cc.add_dependency('job_c_y', 'job_c_z')
        definition_cc_dict = convert_recipe_definition_to_v6_json(definition_cc).get_dict()
        recipe_type_cc = RecipeType.objects.get(id=recipe_type_c.id)
        recipe_type_cc.definition = definition_cc_dict
        recipe_type_cc.revision_num += 1
        RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type_cc)

        # Set up recipe type B (with revision change BB)
        job_type_b_x = job_test_utils.create_seed_job_type()
        job_type_b_y = job_test_utils.create_seed_job_type()
        job_type_b_z = job_test_utils.create_seed_job_type()
        definition_b = RecipeDefinition(Interface())
        definition_b.add_job_node('job_b_x', job_type_b_x.name, job_type_b_x.version, job_type_b_x.revision_num)
        definition_b.add_job_node('job_b_y', job_type_b_y.name, job_type_b_y.version, job_type_b_y.revision_num)
        definition_b.add_job_node('job_b_z', job_type_b_z.name, job_type_b_z.version, job_type_b_z.revision_num)
        definition_b.add_recipe_node('recipe_c', recipe_type_c.name, recipe_type_c.revision_num)
        definition_b.add_dependency('job_b_x', 'recipe_c')
        definition_b.add_dependency('job_b_x', 'job_b_y')
        definition_b.add_dependency('recipe_c', 'job_b_z')
        definition_b_dict = convert_recipe_definition_to_v6_json(definition_b).get_dict()
        recipe_type_b = recipe_test_utils.create_recipe_type(definition=definition_b_dict)
        definition_bb = RecipeDefinition(Interface())
        definition_bb.add_job_node('job_b_x', job_type_b_x.name, job_type_b_x.version, job_type_b_x.revision_num)
        definition_bb.add_job_node('job_b_y', job_type_b_y.name, job_type_b_y.version, job_type_b_y.revision_num)
        definition_bb.add_job_node('job_b_z', job_type_b_z.name, job_type_b_z.version, job_type_b_z.revision_num)
        definition_bb.add_recipe_node('recipe_c', recipe_type_cc.name, recipe_type_cc.revision_num)
        definition_bb.add_dependency('job_b_x', 'recipe_c')
        definition_bb.add_dependency('job_b_x', 'job_b_y')
        definition_bb.add_dependency('recipe_c', 'job_b_z')
        definition_bb_dict = convert_recipe_definition_to_v6_json(definition_bb).get_dict()
        recipe_type_bb = RecipeType.objects.get(id=recipe_type_b.id)
        recipe_type_bb.definition = definition_bb_dict
        recipe_type_bb.revision_num += 1
        RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type_bb)

        # Set up recipe type A (with revision change AA)
        job_type_a_x = job_test_utils.create_seed_job_type()
        definition_a = RecipeDefinition(Interface())
        definition_a.add_job_node('job_a_x', job_type_a_x.name, job_type_a_x.version, job_type_a_x.revision_num)
        definition_a.add_recipe_node('recipe_b', recipe_type_b.name, recipe_type_b.revision_num)
        definition_a.add_recipe_node('recipe_d', recipe_type_d.name, recipe_type_d.revision_num)
        definition_a.add_recipe_node('recipe_e', recipe_type_e.name, recipe_type_e.revision_num)
        definition_a.add_dependency('job_a_x', 'recipe_d')
        definition_a.add_dependency('job_a_x', 'recipe_b')
        definition_a.add_dependency('recipe_d', 'recipe_b')
        definition_a.add_dependency('recipe_b', 'recipe_e')
        definition_a_dict = convert_recipe_definition_to_v6_json(definition_a).get_dict()
        recipe_type_a = recipe_test_utils.create_recipe_type(definition=definition_a_dict)
        definition_aa = RecipeDefinition(Interface())
        definition_aa.add_job_node('job_a_x', job_type_a_x.name, job_type_a_x.version, job_type_a_x.revision_num)
        definition_aa.add_recipe_node('recipe_b', recipe_type_bb.name, recipe_type_bb.revision_num)
        definition_aa.add_recipe_node('recipe_d', recipe_type_d.name, recipe_type_d.revision_num)
        definition_aa.add_recipe_node('recipe_e', recipe_type_e.name, recipe_type_e.revision_num)
        definition_aa.add_dependency('job_a_x', 'recipe_d')
        definition_aa.add_dependency('job_a_x', 'recipe_b')
        definition_aa.add_dependency('recipe_d', 'recipe_b')
        definition_aa.add_dependency('recipe_b', 'recipe_e')
        definition_aa_dict = convert_recipe_definition_to_v6_json(definition_aa).get_dict()
        recipe_type_aa = RecipeType.objects.get(id=recipe_type_a.id)
        recipe_type_aa.definition = definition_aa_dict
        recipe_type_aa.revision_num += 1
        RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type_aa)

        # Create two full recipes of type A
        job_a_x_1 = job_test_utils.create_job(job_type=job_type_a_x, save=False)
        job_a_x_2 = job_test_utils.create_job(job_type=job_type_a_x, save=False)
        job_b_x_1 = job_test_utils.create_job(job_type=job_type_b_x, save=False)
        job_b_x_2 = job_test_utils.create_job(job_type=job_type_b_x, save=False)
        job_b_y_1 = job_test_utils.create_job(job_type=job_type_b_y, save=False)
        job_b_y_2 = job_test_utils.create_job(job_type=job_type_b_y, save=False)
        job_b_z_1 = job_test_utils.create_job(job_type=job_type_b_z, save=False)
        job_b_z_2 = job_test_utils.create_job(job_type=job_type_b_z, save=False)
        job_c_x_1 = job_test_utils.create_job(job_type=job_type_c_x, save=False)
        job_c_x_2 = job_test_utils.create_job(job_type=job_type_c_x, save=False)
        job_c_y_1 = job_test_utils.create_job(job_type=job_type_c_y, save=False)
        job_c_y_2 = job_test_utils.create_job(job_type=job_type_c_y, save=False)
        job_c_z_1 = job_test_utils.create_job(job_type=job_type_c_z, save=False)
        job_c_z_2 = job_test_utils.create_job(job_type=job_type_c_z, save=False)
        job_d_x_1 = job_test_utils.create_job(job_type=job_type_d_x, save=False)
        job_d_x_2 = job_test_utils.create_job(job_type=job_type_d_x, save=False)
        job_d_y_1 = job_test_utils.create_job(job_type=job_type_d_y, save=False)
        job_d_y_2 = job_test_utils.create_job(job_type=job_type_d_y, save=False)
        job_d_z_1 = job_test_utils.create_job(job_type=job_type_d_z, save=False)
        job_d_z_2 = job_test_utils.create_job(job_type=job_type_d_z, save=False)
        job_e_x_1 = job_test_utils.create_job(job_type=job_type_e_x, save=False)
        job_e_x_2 = job_test_utils.create_job(job_type=job_type_e_x, save=False)
        job_e_y_1 = job_test_utils.create_job(job_type=job_type_e_y, save=False)
        job_e_y_2 = job_test_utils.create_job(job_type=job_type_e_y, save=False)
        Job.objects.bulk_create([job_a_x_1, job_a_x_2, job_b_x_1, job_b_x_2, job_b_y_1, job_b_y_2, job_b_z_1, job_b_z_2,
                                 job_c_x_1, job_c_x_2, job_c_y_1, job_c_y_2, job_c_z_1, job_c_z_2, job_d_x_1, job_d_x_2,
                                 job_d_y_1, job_d_y_2, job_d_z_1, job_d_z_2, job_e_x_1, job_e_x_2, job_e_y_1,
                                 job_e_y_2])
        recipe_e_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type_e, save=False)
        recipe_e_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type_e, save=False)
        recipe_d_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type_d, save=False)
        recipe_d_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type_d, save=False)
        recipe_c_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type_c, save=False)
        recipe_c_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type_c, save=False)
        recipe_b_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type_b, save=False)
        recipe_b_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type_b, save=False)
        recipe_a_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type_a, save=False)
        recipe_a_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type_a, save=False)
        Recipe.objects.bulk_create([recipe_a_1, recipe_a_2, recipe_b_1, recipe_b_2, recipe_c_1, recipe_c_2, recipe_d_1,
                                    recipe_d_2, recipe_e_1, recipe_e_2])
        node_a_x_1 = recipe_test_utils.create_recipe_node(recipe=recipe_a_1, node_name='job_a_x', job=job_a_x_1)
        node_a_x_2 = recipe_test_utils.create_recipe_node(recipe=recipe_a_2, node_name='job_a_x', job=job_a_x_2)
        node_b_x_1 = recipe_test_utils.create_recipe_node(recipe=recipe_b_1, node_name='job_b_x', job=job_b_x_1)
        node_b_x_2 = recipe_test_utils.create_recipe_node(recipe=recipe_b_2, node_name='job_b_x', job=job_b_x_2)
        node_b_y_1 = recipe_test_utils.create_recipe_node(recipe=recipe_b_1, node_name='job_b_y', job=job_b_y_1)
        node_b_y_2 = recipe_test_utils.create_recipe_node(recipe=recipe_b_2, node_name='job_b_y', job=job_b_y_2)
        node_b_z_1 = recipe_test_utils.create_recipe_node(recipe=recipe_b_1, node_name='job_b_z', job=job_b_z_1)
        node_b_z_2 = recipe_test_utils.create_recipe_node(recipe=recipe_b_2, node_name='job_b_z', job=job_b_z_2)
        node_c_x_1 = recipe_test_utils.create_recipe_node(recipe=recipe_c_1, node_name='job_c_x', job=job_c_x_1)
        node_c_x_2 = recipe_test_utils.create_recipe_node(recipe=recipe_c_2, node_name='job_c_x', job=job_c_x_2)
        node_c_y_1 = recipe_test_utils.create_recipe_node(recipe=recipe_c_1, node_name='job_c_y', job=job_c_y_1)
        node_c_y_2 = recipe_test_utils.create_recipe_node(recipe=recipe_c_2, node_name='job_c_y', job=job_c_y_2)
        node_c_z_1 = recipe_test_utils.create_recipe_node(recipe=recipe_c_1, node_name='job_c_z', job=job_c_z_1)
        node_c_z_2 = recipe_test_utils.create_recipe_node(recipe=recipe_c_2, node_name='job_c_z', job=job_c_z_2)
        node_d_x_1 = recipe_test_utils.create_recipe_node(recipe=recipe_d_1, node_name='job_d_x', job=job_d_x_1)
        node_d_x_2 = recipe_test_utils.create_recipe_node(recipe=recipe_d_2, node_name='job_d_x', job=job_d_x_2)
        node_d_y_1 = recipe_test_utils.create_recipe_node(recipe=recipe_d_1, node_name='job_d_y', job=job_d_y_1)
        node_d_y_2 = recipe_test_utils.create_recipe_node(recipe=recipe_d_2, node_name='job_d_y', job=job_d_y_2)
        node_d_z_1 = recipe_test_utils.create_recipe_node(recipe=recipe_d_1, node_name='job_d_z', job=job_d_z_1)
        node_d_z_2 = recipe_test_utils.create_recipe_node(recipe=recipe_d_2, node_name='job_d_z', job=job_d_z_2)
        node_e_x_1 = recipe_test_utils.create_recipe_node(recipe=recipe_e_1, node_name='job_e_x', job=job_e_x_1)
        node_e_x_2 = recipe_test_utils.create_recipe_node(recipe=recipe_e_2, node_name='job_e_x', job=job_e_x_2)
        node_e_y_1 = recipe_test_utils.create_recipe_node(recipe=recipe_e_1, node_name='job_e_y', job=job_e_y_1)
        node_e_y_2 = recipe_test_utils.create_recipe_node(recipe=recipe_e_2, node_name='job_e_y', job=job_e_y_2)
        node_e_1 = recipe_test_utils.create_recipe_node(recipe=recipe_a_1, node_name='recipe_e', sub_recipe=recipe_e_1)
        node_e_2 = recipe_test_utils.create_recipe_node(recipe=recipe_a_2, node_name='recipe_e', sub_recipe=recipe_e_2)
        node_d_1 = recipe_test_utils.create_recipe_node(recipe=recipe_a_1, node_name='recipe_d', sub_recipe=recipe_d_1)
        node_d_2 = recipe_test_utils.create_recipe_node(recipe=recipe_a_2, node_name='recipe_d', sub_recipe=recipe_d_2)
        node_c_1 = recipe_test_utils.create_recipe_node(recipe=recipe_b_1, node_name='recipe_c', sub_recipe=recipe_c_1)
        node_c_2 = recipe_test_utils.create_recipe_node(recipe=recipe_b_2, node_name='recipe_c', sub_recipe=recipe_c_2)
        node_b_1 = recipe_test_utils.create_recipe_node(recipe=recipe_a_1, node_name='recipe_b', sub_recipe=recipe_b_1)
        node_b_2 = recipe_test_utils.create_recipe_node(recipe=recipe_a_2, node_name='recipe_b', sub_recipe=recipe_b_2)
        RecipeNode.objects.bulk_create([node_a_x_1, node_a_x_2, node_b_x_1, node_b_x_2, node_b_y_1, node_b_y_2,
                                        node_b_z_1, node_b_z_2, node_c_x_1, node_c_x_2, node_c_y_1, node_c_y_2,
                                        node_c_z_1, node_c_z_2, node_d_x_1, node_d_x_2, node_d_y_1, node_d_y_2,
                                        node_d_z_1, node_d_z_2, node_e_x_1, node_e_x_2, node_e_y_1, node_e_y_2,
                                        node_e_1, node_e_2, node_d_1, node_d_2, node_c_1, node_c_2, node_b_1, node_b_2])

        # Create message to reprocess recipe a_1 and a_2
        reprocess_recipe_ids = [recipe_a_1.id, recipe_a_2.id]
        message = create_reprocess_messages(reprocess_recipe_ids, recipe_type_aa.name, recipe_type_aa.revision_num,
                                            event.id, batch_id=batch.id, forced_nodes=forced_nodes_a)[0]

        # Execute entire message chain
        messages = [message]
        while messages:
            msg = messages.pop(0)
            # TODO: remove this once 'process_recipe_input' has been updated to use 'update_recipe' message instead
            if msg.type == 'update_recipes':
                continue
            result = msg.execute()
            self.assertTrue(result)
            messages.extend(msg.new_messages)

        # Check jobs for superseded status
        superseded_job_ids = [job_b_y_1.id, job_b_y_2.id, job_b_z_1.id, job_b_z_2.id, job_c_y_1.id, job_c_y_2.id,
                              job_c_z_1.id, job_c_z_2.id, job_e_x_1.id, job_e_x_2.id, job_e_y_1.id, job_e_y_2.id]
        non_superseded_job_ids = [job_a_x_1.id, job_a_x_2.id, job_b_x_1.id, job_b_x_2.id, job_c_x_1.id, job_c_x_2.id,
                                  job_d_x_1.id, job_d_x_2.id, job_d_y_1.id, job_d_y_2.id, job_d_z_1.id, job_d_z_2.id]
        # TODO: this is temporary until logic is switched to use update_recipe message
        superseded_job_ids = [job_e_x_1.id, job_e_x_2.id, job_e_y_1.id, job_e_y_2.id]
        non_superseded_job_ids = [job_a_x_1.id, job_a_x_2.id, job_b_x_1.id, job_b_x_2.id, job_c_x_1.id, job_c_x_2.id,
                                  job_d_x_1.id, job_d_x_2.id, job_d_y_1.id, job_d_y_2.id, job_d_z_1.id, job_d_z_2.id,
                                  job_b_y_1.id, job_b_y_2.id, job_b_z_1.id, job_b_z_2.id, job_c_y_1.id, job_c_y_2.id,
                                  job_c_z_1.id, job_c_z_2.id,]
        for job in Job.objects.filter(id__in=superseded_job_ids):
            self.assertTrue(job.is_superseded, 'Job %d should be superseded, but is not' % job.id)
        for job in Job.objects.filter(id__in=non_superseded_job_ids):
            self.assertFalse(job.is_superseded, 'Job %d should not be superseded, but is' % job.id)

        # Check recipes for superseded status
        superseded_recipe_ids = [recipe_a_1.id, recipe_a_2.id, recipe_b_1.id, recipe_b_2.id, recipe_c_1.id,
                                 recipe_c_2.id, recipe_e_1.id, recipe_e_2.id]
        non_superseded_recipe_ids = [recipe_d_1.id, recipe_d_2.id]
        # TODO: this is temporary until logic is switched to use update_recipe message
        superseded_recipe_ids = [recipe_a_1.id, recipe_a_2.id, recipe_b_1.id, recipe_b_2.id, recipe_e_1.id,
                                 recipe_e_2.id]
        non_superseded_recipe_ids = [recipe_d_1.id, recipe_d_2.id, recipe_c_1.id, recipe_c_2.id]
        for recipe in Recipe.objects.filter(id__in=superseded_recipe_ids):
            self.assertTrue(recipe.is_superseded, 'Recipe %d should be superseded, but is not' % recipe.id)
        for recipe in Recipe.objects.filter(id__in=non_superseded_recipe_ids):
            self.assertFalse(recipe.is_superseded, 'Recipe %d should not be superseded, but is' % recipe.id)

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
