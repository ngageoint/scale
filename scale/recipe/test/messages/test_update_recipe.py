from __future__ import unicode_literals

import django
from django.test import TestCase

from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.interface.interface import Interface
from job.messages.create_jobs import RECIPE_TYPE, RecipeJob
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.diff.forced_nodes import ForcedNodes
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6
from recipe.messages.create_recipes import SUB_RECIPE_TYPE, SubRecipe
from recipe.messages.update_recipe import create_update_recipe_message, UpdateRecipe
from recipe.models import RecipeNode
from recipe.test import utils as recipe_test_utils


class TestUpdateRecipe(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests converting an UpdateRecipe message to and from JSON"""

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        job_failed = job_test_utils.create_job(status='FAILED', input=data_dict)
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
        job_completed = job_test_utils.create_job(status='COMPLETED', input=data_dict, output=data_dict)
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

    def test_execute(self):
        """Tests calling UpdateRecipe.execute() successfully"""

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        job_a = job_test_utils.create_job(status='COMPLETED', input=data_dict, output=data_dict)
        recipe_b = recipe_test_utils.create_recipe()
        job_c = job_test_utils.create_job(status='PENDING')
        job_d = job_test_utils.create_job(status='BLOCKED')
        recipe_type_e = recipe_test_utils.create_recipe_type()
        job_type_f = job_test_utils.create_seed_job_type()
        job_g = job_test_utils.create_job(status='FAILED', input=data_dict)
        job_h = job_test_utils.create_job(status='PENDING')
        definition = RecipeDefinition(Interface())
        definition.add_job_node('node_a', job_a.job_type.name, job_a.job_type.version, job_a.job_type_rev.revision_num)
        definition.add_recipe_node('node_b', recipe_b.recipe_type.name, recipe_b.recipe_type.revision_num)
        definition.add_job_node('node_c', job_c.job_type.name, job_c.job_type.version, job_c.job_type_rev.revision_num)
        definition.add_job_node('node_d', job_d.job_type.name, job_d.job_type.version, job_d.job_type_rev.revision_num)
        definition.add_recipe_node('node_e', recipe_type_e.name, recipe_type_e.revision_num)
        definition.add_job_node('node_f', job_type_f.name, job_type_f.version, job_type_f.revision_num)
        definition.add_job_node('node_g', job_g.job_type.name, job_g.job_type.version, job_g.job_type_rev.revision_num)
        definition.add_job_node('node_h', job_h.job_type.name, job_h.job_type.version, job_h.job_type_rev.revision_num)
        definition.add_dependency('node_a', 'node_c')
        definition.add_dependency('node_a', 'node_e')
        definition.add_dependency('node_a', 'node_g')
        definition.add_dependency('node_c', 'node_d')
        definition.add_dependency('node_e', 'node_f')
        definition.add_dependency('node_g', 'node_h')
        definition_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_dict)
        node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_a', job=job_a, save=False)
        node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_b', sub_recipe=recipe_b,
                                                      save=False)
        node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_c', job=job_c, save=False)
        node_d = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_d', job=job_d, save=False)
        node_g = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_g', job=job_g, save=False)
        node_h = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='node_h', job=job_h, save=False)
        RecipeNode.objects.bulk_create([node_a, node_b, node_c, node_d, node_g, node_h])
        forced_nodes = ForcedNodes()
        forced_nodes_e = ForcedNodes()
        forced_nodes_e.set_all_nodes()
        forced_nodes.add_subrecipe('node_e', forced_nodes_e)

        # Create and execute message
        message = create_update_recipe_message(recipe.id, forced_nodes=forced_nodes)
        result = message.execute()
        self.assertTrue(result)

        self.assertEqual(len(message.new_messages), 6)
        # Check messages
        blocked_jobs_msg = None
        pending_jobs_msg = None
        create_jobs_msg = None
        create_recipes_msg = None
        process_job_input_msg = None
        process_recipe_input_msg = None
        for msg in message.new_messages:
            if msg.type == 'blocked_jobs':
                blocked_jobs_msg = msg
            elif msg.type == 'pending_jobs':
                pending_jobs_msg = msg
            elif msg.type == 'create_jobs':
                create_jobs_msg = msg
            elif msg.type == 'create_recipes':
                create_recipes_msg = msg
            elif msg.type == 'process_job_input':
                process_job_input_msg = msg
            elif msg.type == 'process_recipe_input':
                process_recipe_input_msg = msg
        self.assertIsNotNone(blocked_jobs_msg)
        self.assertIsNotNone(pending_jobs_msg)
        self.assertIsNotNone(create_jobs_msg)
        self.assertIsNotNone(create_recipes_msg)
        self.assertIsNotNone(process_job_input_msg)
        self.assertIsNotNone(process_recipe_input_msg)
        # Check message to change jobs to BLOCKED
        self.assertListEqual(blocked_jobs_msg._blocked_job_ids, [job_h.id])
        # Check message to change jobs to PENDING
        self.assertListEqual(pending_jobs_msg._pending_job_ids, [job_d.id])
        # Check message to create jobs
        self.assertEqual(create_jobs_msg.event_id, recipe.event_id)
        self.assertEqual(create_jobs_msg.create_jobs_type, RECIPE_TYPE)
        self.assertEqual(create_jobs_msg.recipe_id, recipe.id)
        self.assertEqual(create_jobs_msg.root_recipe_id, recipe.root_superseded_recipe_id)
        self.assertIsNone(create_jobs_msg.superseded_recipe_id)
        recipe_job = RecipeJob(job_type_f.name, job_type_f.version, job_type_f.revision_num, 'node_f', False)
        self.assertListEqual(create_jobs_msg.recipe_jobs, [recipe_job])
        # Check message to create sub-recipes
        self.assertEqual(create_recipes_msg.event_id, recipe.event_id)
        msg_forced_nodes_dict = convert_forced_nodes_to_v6(create_recipes_msg.forced_nodes).get_dict()
        expected_forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()
        self.assertDictEqual(msg_forced_nodes_dict, expected_forced_nodes_dict)
        self.assertEqual(create_recipes_msg.create_recipes_type, SUB_RECIPE_TYPE)
        self.assertEqual(create_recipes_msg.recipe_id, recipe.id)
        self.assertEqual(create_recipes_msg.root_recipe_id, recipe.root_superseded_recipe_id)
        self.assertIsNone(create_recipes_msg.superseded_recipe_id)
        sub = SubRecipe(recipe_type_e.name, recipe_type_e.revision_num, 'node_e', True)
        self.assertListEqual(create_recipes_msg.sub_recipes, [sub])
        # Check message to process job input
        self.assertEqual(process_job_input_msg.job_id, job_c.id)
        # Check message to process recipe input
        self.assertEqual(process_recipe_input_msg.recipe_id, recipe_b.id)

        # Test executing message again
        message_json_dict = message.to_json()
        message = UpdateRecipe.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Make sure the same messages are returned
        blocked_jobs_msg = None
        pending_jobs_msg = None
        create_jobs_msg = None
        create_recipes_msg = None
        process_job_input_msg = None
        process_recipe_input_msg = None
        for msg in message.new_messages:
            if msg.type == 'blocked_jobs':
                blocked_jobs_msg = msg
            elif msg.type == 'pending_jobs':
                pending_jobs_msg = msg
            elif msg.type == 'create_jobs':
                create_jobs_msg = msg
            elif msg.type == 'create_recipes':
                create_recipes_msg = msg
            elif msg.type == 'process_job_input':
                process_job_input_msg = msg
            elif msg.type == 'process_recipe_input':
                process_recipe_input_msg = msg
        self.assertIsNotNone(blocked_jobs_msg)
        self.assertIsNotNone(pending_jobs_msg)
        self.assertIsNotNone(create_jobs_msg)
        self.assertIsNotNone(create_recipes_msg)
        self.assertIsNotNone(process_job_input_msg)
        self.assertIsNotNone(process_recipe_input_msg)
        # Check message to change jobs to BLOCKED
        self.assertListEqual(blocked_jobs_msg._blocked_job_ids, [job_h.id])
        # Check message to change jobs to PENDING
        self.assertListEqual(pending_jobs_msg._pending_job_ids, [job_d.id])
        # Check message to create jobs
        self.assertEqual(create_jobs_msg.event_id, recipe.event_id)
        self.assertEqual(create_jobs_msg.create_jobs_type, RECIPE_TYPE)
        self.assertEqual(create_jobs_msg.recipe_id, recipe.id)
        self.assertEqual(create_jobs_msg.root_recipe_id, recipe.root_superseded_recipe_id)
        self.assertIsNone(create_jobs_msg.superseded_recipe_id)
        recipe_job = RecipeJob(job_type_f.name, job_type_f.version, job_type_f.revision_num, 'node_f', False)
        self.assertListEqual(create_jobs_msg.recipe_jobs, [recipe_job])
        # Check message to create sub-recipes
        self.assertEqual(create_recipes_msg.event_id, recipe.event_id)
        msg_forced_nodes_dict = convert_forced_nodes_to_v6(create_recipes_msg.forced_nodes).get_dict()
        expected_forced_nodes_dict = convert_forced_nodes_to_v6(forced_nodes).get_dict()
        self.assertDictEqual(msg_forced_nodes_dict, expected_forced_nodes_dict)
        self.assertEqual(create_recipes_msg.create_recipes_type, SUB_RECIPE_TYPE)
        self.assertEqual(create_recipes_msg.recipe_id, recipe.id)
        self.assertEqual(create_recipes_msg.root_recipe_id, recipe.root_superseded_recipe_id)
        self.assertIsNone(create_recipes_msg.superseded_recipe_id)
        sub = SubRecipe(recipe_type_e.name, recipe_type_e.revision_num, 'node_e', True)
        self.assertListEqual(create_recipes_msg.sub_recipes, [sub])
        # Check message to process job input
        self.assertEqual(process_job_input_msg.job_id, job_c.id)
        # Check message to process recipe input
        self.assertEqual(process_recipe_input_msg.recipe_id, recipe_b.id)
