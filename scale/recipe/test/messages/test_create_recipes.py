from __future__ import unicode_literals

import django
from django.test import TransactionTestCase

from batch.test import utils as batch_test_utils
from data.interface.interface import Interface
from job.models import Job
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.diff.forced_nodes import ForcedNodes
from recipe.messages.create_recipes import create_subrecipes_messages, CreateRecipes, SubRecipe
from recipe.models import Recipe, RecipeNode
from recipe.test import utils as recipe_test_utils
from trigger.test import utils as trigger_test_utils


class TestCreateRecipes(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_json_subrecipes(self):
        """Tests converting a CreateRecipes message to and from JSON when creating sub-recipes"""

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
        new_top_recipe = recipe_test_utils.create_recipe(recipe_type=top_recipe_type, save=False)
        Job.objects.bulk_create([prev_job_a_1, prev_job_a_2, prev_job_b_x])
        Recipe.objects.bulk_create([prev_recipe_a, prev_recipe_b, prev_recipe_b_y, prev_top_recipe, new_top_recipe])
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
        message = create_subrecipes_messages(new_top_recipe.id, new_top_recipe.root_superseded_recipe_id, sub_recipes,
                                             event.id, superseded_recipe_id=prev_top_recipe.id,
                                             forced_nodes=forced_nodes, batch_id=batch.id)[0]

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
        self.assertEqual(sub_recipe_b.recipe_type_id, recipe_type_b.id)
        # Check for sub-recipes to contain correct copied nodes
        self.assertEqual(RecipeNode.objects.filter(recipe_id=sub_recipe_a.id).count(), 0)  # No copied nodes for A
        # Node X in sub-recipe B should be copied
        recipe_nodes = RecipeNode.objects.select_related('sub_recipe').filter(recipe_id=sub_recipe_b.id)
        self.assertEqual(len(recipe_nodes), 1)
        self.assertEqual(recipe_nodes[0].node_name, 'node_x')
        self.assertFalse(recipe_nodes[0].is_original)

        # Should be four messages, two for superseding recipe nodes, one for processing recipe input, and one for
        # updating metrics for the recipe containing the new sub-recipes
        self.assertEqual(len(new_message.new_messages), 4)
        supersede_recipe_a_msg = None
        supersede_recipe_b_msg = None
        process_recipe_input_msg = None
        update_metrics_msg = None
        for msg in new_message.new_messages:
            if msg.type == 'supersede_recipe_nodes':
                if msg._recipe_ids[0] == prev_recipe_a.id:
                    supersede_recipe_a_msg = msg
                if msg._recipe_ids[0] == prev_recipe_b.id:
                    supersede_recipe_b_msg = msg
            elif msg.type == 'process_recipe_input':
                process_recipe_input_msg = msg
            elif msg.type == 'update_recipe_metrics':
                update_metrics_msg = msg
        self.assertIsNotNone(supersede_recipe_a_msg)
        self.assertIsNotNone(supersede_recipe_b_msg)
        self.assertIsNotNone(process_recipe_input_msg)
        self.assertIsNotNone(update_metrics_msg)
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
        # Check message to update recipe metrics for the recipe containing the new sub-recipes
        self.assertListEqual(update_metrics_msg._recipe_ids, [new_top_recipe.id])

    def test_execute(self):
        """Tests calling ReprocessRecipes.execute() successfully"""

        # TODO: code snippet for copying recipe nodes, keep until we know it works
        # INSERT INTO recipe_node (node_name, is_original, recipe_id, job_id, sub_recipe_id)
        # SELECT node_name, false, %new_recipe_id%, job_id, sub_recipe_id FROM recipe_node
        #   WHERE recipe_id = %old_recipe_id% AND node_name IN ('%node_name')
        # UNION ALL SELECT node_name, false, %new_recipe_id%, job_id, sub_recipe_id FROM recipe_node
        #   WHERE recipe_id = %old_recipe_id% AND node_name IN ('%node_name')

        batch = batch_test_utils.create_batch()
        # event = trigger_test_utils.create_trigger_event()

        # # Create message
        # message = create_reprocess_recipes_messages(self.old_recipe_ids, self.recipe_1.recipe_type_rev_id, event.id,
        #                                             all_jobs=False, job_names=['Job 2'], batch_id=batch.id)[0]

        # # Execute message
        # result = message.execute()
        # self.assertTrue(result)

        # # Make sure new recipes supersede the old ones
        # for recipe in Recipe.objects.filter(id__in=self.old_recipe_ids):
        #     self.assertTrue(recipe.is_superseded)
        # new_recipe_1 = Recipe.objects.get(superseded_recipe_id=self.recipe_1.id)
        # self.assertEqual(new_recipe_1.batch_id, batch.id)
        # self.assertEqual(new_recipe_1.event_id, event.id)
        # self.assertEqual(new_recipe_1.root_superseded_recipe_id, self.recipe_1.id)
        # self.assertDictEqual(new_recipe_1.input, self.recipe_1.input)
        # new_recipe_2 = Recipe.objects.get(superseded_recipe_id=self.recipe_2.id)
        # self.assertEqual(new_recipe_2.batch_id, batch.id)
        # self.assertEqual(new_recipe_2.event_id, event.id)
        # self.assertEqual(new_recipe_2.root_superseded_recipe_id, self.recipe_2.id)
        # self.assertDictEqual(new_recipe_2.input, self.recipe_2.input)
        # # Make sure identical jobs (Job 1) are NOT superseded
        # for job in Job.objects.filter(id__in=self.old_job_1_ids):
        #     self.assertFalse(job.is_superseded)
        # # Make sure old jobs (Job 2) are superseded
        # for job in Job.objects.filter(id__in=self.old_job_2_ids):
        #     self.assertTrue(job.is_superseded)
        # # Make sure identical jobs (Job 1) were copied to new recipes
        # recipe_job_1 = RecipeNode.objects.get(recipe=new_recipe_1.id)
        # self.assertEqual(recipe_job_1.node_name, 'Job 1')
        # self.assertEqual(recipe_job_1.job_id, self.job_1_1.id)
        # recipe_job_2 = RecipeNode.objects.get(recipe=new_recipe_2.id)
        # self.assertEqual(recipe_job_2.node_name, 'Job 1')
        # self.assertEqual(recipe_job_2.job_id, self.job_2_1.id)
        # # Should be three messages, two for processing new recipe input and one for canceling superseded jobs
        # self.assertEqual(len(message.new_messages), 3)
        # found_process_recipe_input_1 = False
        # found_process_recipe_input_2 = False
        # found_cancel_jobs = False
        # for msg in message.new_messages:
        #     if msg.type == 'process_recipe_input':
        #         if msg.recipe_id == new_recipe_1.id:
        #             found_process_recipe_input_1 = True
        #         elif msg.recipe_id == new_recipe_2.id:
        #             found_process_recipe_input_2 = True
        #     elif msg.type == 'cancel_jobs':
        #         found_cancel_jobs = True
        #         self.assertSetEqual(set(msg._job_ids), set(self.old_job_2_ids))
        # self.assertTrue(found_process_recipe_input_1)
        # self.assertTrue(found_process_recipe_input_2)
        # self.assertTrue(found_cancel_jobs)

        # # Test executing message again
        # message_json_dict = message.to_json()
        # message = ReprocessRecipes.from_json(message_json_dict)
        # result = message.execute()
        # self.assertTrue(result)

        # # Make sure we don't reprocess twice
        # for new_recipe in Recipe.objects.filter(id__in=[new_recipe_1.id, new_recipe_2.id]):
        #     self.assertFalse(new_recipe.is_superseded)
        # # Should get same messages
        # self.assertEqual(len(message.new_messages), 3)
        # found_process_recipe_input_1 = False
        # found_process_recipe_input_2 = False
        # found_cancel_jobs = False
        # for msg in message.new_messages:
        #     if msg.type == 'process_recipe_input':
        #         if msg.recipe_id == new_recipe_1.id:
        #             found_process_recipe_input_1 = True
        #         elif msg.recipe_id == new_recipe_2.id:
        #             found_process_recipe_input_2 = True
        #     elif msg.type == 'cancel_jobs':
        #         found_cancel_jobs = True
        #         self.assertSetEqual(set(msg._job_ids), set(self.old_job_2_ids))
        # self.assertTrue(found_process_recipe_input_1)
        # self.assertTrue(found_process_recipe_input_2)
        # self.assertTrue(found_cancel_jobs)
