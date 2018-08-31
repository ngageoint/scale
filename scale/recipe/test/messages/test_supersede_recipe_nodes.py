from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

from job.models import Job
from job.test import utils as job_test_utils
from recipe.messages.supersede_recipe_nodes import create_supersede_recipe_nodes_messages, SupersedeRecipeNodes
from recipe.models import Recipe, RecipeNode
from recipe.test import utils as recipe_test_utils


class TestSupersedeRecipeNodes(TestCase):

    def setUp(self):
        django.setup()

    def test_json(self):
        """Tests coverting a SupersedeRecipeNodes message to and from JSON"""

        # Create 2 recipes with 2 jobs and 3 sub-recipes each
        job_type_1 = job_test_utils.create_seed_job_type()
        job_type_2 = job_test_utils.create_seed_job_type()
        sub_recipe_type_1 = recipe_test_utils.create_recipe_type()
        sub_recipe_type_2 = recipe_test_utils.create_recipe_type()
        sub_recipe_type_3 = recipe_test_utils.create_recipe_type()
        recipe_type = recipe_test_utils.create_recipe_type()

        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        job_1_1 = job_test_utils.create_job(job_type=job_type_1, save=False)
        job_1_2 = job_test_utils.create_job(job_type=job_type_2, save=False)
        sub_recipe_1_1 = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_1, save=False)
        sub_recipe_1_2 = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_2, save=False)
        sub_recipe_1_3 = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_3, save=False)
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        job_2_1 = job_test_utils.create_job(job_type=job_type_1, save=False)
        job_2_2 = job_test_utils.create_job(job_type=job_type_2, save=False)
        sub_recipe_2_1 = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_1, save=False)
        sub_recipe_2_2 = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_2, save=False)
        sub_recipe_2_3 = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type_3, save=False)
        Job.objects.bulk_create([job_1_1, job_1_2, job_2_1, job_2_2])
        Recipe.objects.bulk_create([recipe_1, recipe_2, sub_recipe_1_1, sub_recipe_1_2, sub_recipe_1_3, sub_recipe_2_1,
                                    sub_recipe_2_2, sub_recipe_2_3])

        node_1_1 = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_a', job=job_1_1, save=False)
        node_1_2 = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_b', job=job_1_2, save=False)
        node_1_3 = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_c', sub_recipe=sub_recipe_1_1,
                                                        save=False)
        node_1_4 = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_d', sub_recipe=sub_recipe_1_2,
                                                        save=False)
        node_1_5 = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_e', sub_recipe=sub_recipe_1_3,
                                                        save=False)
        node_2_1 = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_a', job=job_2_1, save=False)
        node_2_2 = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_b', job=job_2_2, save=False)
        node_2_3 = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_c', sub_recipe=sub_recipe_2_1,
                                                        save=False)
        node_2_4 = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_d', sub_recipe=sub_recipe_2_2,
                                                        save=False)
        node_2_5 = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_e', sub_recipe=sub_recipe_2_3,
                                                        save=False)
        RecipeNode.objects.bulk_create([node_1_1, node_1_2, node_1_3, node_1_4, node_1_5, node_2_1, node_2_2, node_2_3,
                                        node_2_4, node_2_5])

        when = now()
        supersede_jobs = {'node_a', 'node_b'}
        supersede_subrecipes = {'node_c', 'node_d'}
        unpublish_jobs = {'node_b'}
        supersede_recursive = {'node_c'}
        unpublish_recursive = {'node_d'}

        # Create message
        message = create_supersede_recipe_nodes_messages([recipe_1.id, recipe_2.id], when, supersede_jobs,
                                                         supersede_subrecipes, unpublish_jobs, supersede_recursive,
                                                         unpublish_recursive)[0]

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = SupersedeRecipeNodes.from_json(message_json_dict)
        result = new_message.execute()
        self.assertTrue(result)

        # Ensure jobs from both recipes are superseded
        for job in Job.objects.filter(id__in=[job_1_1.id, job_1_2.id, job_2_1.id, job_2_2.id]):
            self.assertTrue(job.is_superseded)
            self.assertEqual(job.superseded, when)
        # Ensure sub-recipes 'node_c' and 'node_d' from both recipes are superseded
        for recipe in Recipe.objects.filter(id__in=[sub_recipe_1_1.id, sub_recipe_1_2.id, sub_recipe_2_1.id,
                                                    sub_recipe_2_2.id]):
            self.assertTrue(recipe.is_superseded)
            self.assertEqual(recipe.superseded, when)
        # Ensure sub-recipes 'node_e' from both recipes are NOT superseded
        for recipe in Recipe.objects.filter(id__in=[sub_recipe_1_3.id, sub_recipe_2_3.id]):
            self.assertFalse(recipe.is_superseded)
            self.assertIsNone(recipe.superseded)

        # Should be four messages
        # 1. Canceling jobs 'node_a' and 'node_b'
        # 2. Unpublishing jobs 'node_b'
        # 3. Recursively supersede sub-recipes 'node_c'
        # 4. Recursively supersede/unpublish sub-recipes 'node_d'
        self.assertEqual(len(new_message.new_messages), 4)
        msg_cancel_jobs = None
        msg_unpublish_jobs = None
        msg_recur_supersede = None
        msg_recur_unpublish = None
        for msg in new_message.new_messages:
            if msg.type == 'cancel_jobs':
                msg_cancel_jobs = msg
            elif msg.type == 'unpublish_jobs':
                msg_unpublish_jobs = msg
            elif msg.type == 'supersede_recipe_nodes':
                if msg.unpublish_recursive_all:
                    msg_recur_unpublish = msg
                else:
                    msg_recur_supersede = msg

        self.assertIsNotNone(msg_cancel_jobs)
        self.assertSetEqual(set(msg_cancel_jobs._job_ids), {job_1_1.id, job_1_2.id, job_2_1.id, job_2_2.id})
        self.assertEqual(msg_cancel_jobs.when, when)

        self.assertIsNotNone(msg_unpublish_jobs)
        self.assertSetEqual(set(msg_unpublish_jobs._job_ids), {job_1_2.id, job_2_2.id})
        self.assertEqual(msg_unpublish_jobs.when, when)

        self.assertIsNotNone(msg_recur_supersede)
        self.assertSetEqual(set(msg_recur_supersede._recipe_ids), {sub_recipe_1_1.id, sub_recipe_2_1.id})
        self.assertEqual(msg_recur_supersede.when, when)
        self.assertTrue(msg_recur_supersede.supersede_all)
        self.assertFalse(msg_recur_supersede.unpublish_all)
        self.assertTrue(msg_recur_supersede.supersede_recursive_all)
        self.assertFalse(msg_recur_supersede.unpublish_recursive_all)

        self.assertIsNotNone(msg_recur_unpublish)
        self.assertSetEqual(set(msg_recur_unpublish._recipe_ids), {sub_recipe_1_2.id, sub_recipe_2_2.id})
        self.assertEqual(msg_recur_unpublish.when, when)
        self.assertTrue(msg_recur_unpublish.supersede_all)
        self.assertTrue(msg_recur_unpublish.unpublish_all)
        self.assertTrue(msg_recur_unpublish.supersede_recursive_all)
        self.assertTrue(msg_recur_unpublish.unpublish_recursive_all)

    def test_execute(self):
        """Tests calling SupersedeRecipeNodes.execute() successfully"""

        # Create 2 recipes with 4 jobs and 4 sub-recipes each
        # The sub-recipes will themselves have 2 jobs and 2 sub-recipes each
        job_type = job_test_utils.create_seed_job_type()
        recipe_type = recipe_test_utils.create_recipe_type()

        recipe_1 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        job_1_a = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_b = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_c = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_d = job_test_utils.create_job(job_type=job_type, save=False)
        recipe_1_e = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_f = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_g = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_h = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        job_1_e_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_e_2 = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_f_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_f_2 = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_g_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_g_2 = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_h_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_1_h_2 = job_test_utils.create_job(job_type=job_type, save=False)
        recipe_1_e_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_e_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_f_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_f_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_g_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_g_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_h_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_1_h_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        node_1_a = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_a', job=job_1_a, save=False)
        node_1_b = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_b', job=job_1_b, save=False)
        node_1_c = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_c', job=job_1_c, save=False)
        node_1_d = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_d', job=job_1_d, save=False)
        node_1_e = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_e', sub_recipe=recipe_1_e,
                                                        save=False)
        node_1_f = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_f', sub_recipe=recipe_1_f,
                                                        save=False)
        node_1_g = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_g', sub_recipe=recipe_1_g,
                                                        save=False)
        node_1_h = recipe_test_utils.create_recipe_node(recipe=recipe_1, node_name='node_h', sub_recipe=recipe_1_h,
                                                        save=False)
        node_1_e_1 = recipe_test_utils.create_recipe_node(recipe=recipe_1_e, node_name='node_1', job=job_1_e_1,
                                                          save=False)
        node_1_e_2 = recipe_test_utils.create_recipe_node(recipe=recipe_1_e, node_name='node_2', job=job_1_e_2,
                                                          save=False)
        node_1_f_1 = recipe_test_utils.create_recipe_node(recipe=recipe_1_f, node_name='node_1', job=job_1_f_1,
                                                          save=False)
        node_1_f_2 = recipe_test_utils.create_recipe_node(recipe=recipe_1_f, node_name='node_2', job=job_1_f_2,
                                                          save=False)
        node_1_g_1 = recipe_test_utils.create_recipe_node(recipe=recipe_1_g, node_name='node_1', job=job_1_g_1,
                                                          save=False)
        node_1_g_2 = recipe_test_utils.create_recipe_node(recipe=recipe_1_g, node_name='node_2', job=job_1_g_2,
                                                          save=False)
        node_1_h_1 = recipe_test_utils.create_recipe_node(recipe=recipe_1_h, node_name='node_1', job=job_1_h_1,
                                                          save=False)
        node_1_h_2 = recipe_test_utils.create_recipe_node(recipe=recipe_1_h, node_name='node_2', job=job_1_h_2,
                                                          save=False)
        node_1_e_3 = recipe_test_utils.create_recipe_node(recipe=recipe_1_e, node_name='node_3',
                                                          sub_recipe=recipe_1_e_3, save=False)
        node_1_e_4 = recipe_test_utils.create_recipe_node(recipe=recipe_1_e, node_name='node_4',
                                                          sub_recipe=recipe_1_e_4, save=False)
        node_1_f_3 = recipe_test_utils.create_recipe_node(recipe=recipe_1_f, node_name='node_3',
                                                          sub_recipe=recipe_1_f_3, save=False)
        node_1_f_4 = recipe_test_utils.create_recipe_node(recipe=recipe_1_f, node_name='node_4',
                                                          sub_recipe=recipe_1_f_4, save=False)
        node_1_g_3 = recipe_test_utils.create_recipe_node(recipe=recipe_1_g, node_name='node_3',
                                                          sub_recipe=recipe_1_g_3, save=False)
        node_1_g_4 = recipe_test_utils.create_recipe_node(recipe=recipe_1_g, node_name='node_4',
                                                          sub_recipe=recipe_1_g_4, save=False)
        node_1_h_3 = recipe_test_utils.create_recipe_node(recipe=recipe_1_h, node_name='node_3',
                                                          sub_recipe=recipe_1_h_3, save=False)
        node_1_h_4 = recipe_test_utils.create_recipe_node(recipe=recipe_1_h, node_name='node_4',
                                                          sub_recipe=recipe_1_h_4, save=False)


        # batch = batch_test_utils.create_batch()
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
