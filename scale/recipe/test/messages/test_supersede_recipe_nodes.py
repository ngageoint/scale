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
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        job_2_a = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_b = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_c = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_d = job_test_utils.create_job(job_type=job_type, save=False)
        recipe_2_e = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_f = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_g = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_h = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        job_2_e_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_e_2 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_f_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_f_2 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_g_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_g_2 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_h_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_h_2 = job_test_utils.create_job(job_type=job_type, save=False)
        recipe_2_e_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_e_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_f_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_f_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_g_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_g_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_h_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_h_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        node_2_a = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_a', job=job_2_a, save=False)
        node_2_b = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_b', job=job_2_b, save=False)
        node_2_c = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_c', job=job_2_c, save=False)
        node_2_d = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_d', job=job_2_d, save=False)
        node_2_e = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_e', sub_recipe=recipe_2_e,
                                                        save=False)
        node_2_f = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_f', sub_recipe=recipe_2_f,
                                                        save=False)
        node_2_g = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_g', sub_recipe=recipe_2_g,
                                                        save=False)
        node_2_h = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_h', sub_recipe=recipe_2_h,
                                                        save=False)
        node_2_e_1 = recipe_test_utils.create_recipe_node(recipe=recipe_2_e, node_name='node_1', job=job_2_e_1,
                                                          save=False)
        node_2_e_2 = recipe_test_utils.create_recipe_node(recipe=recipe_2_e, node_name='node_2', job=job_2_e_2,
                                                          save=False)
        node_2_f_1 = recipe_test_utils.create_recipe_node(recipe=recipe_2_f, node_name='node_1', job=job_2_f_1,
                                                          save=False)
        node_2_f_2 = recipe_test_utils.create_recipe_node(recipe=recipe_2_f, node_name='node_2', job=job_2_f_2,
                                                          save=False)
        node_2_g_1 = recipe_test_utils.create_recipe_node(recipe=recipe_2_g, node_name='node_1', job=job_2_g_1,
                                                          save=False)
        node_2_g_2 = recipe_test_utils.create_recipe_node(recipe=recipe_2_g, node_name='node_2', job=job_2_g_2,
                                                          save=False)
        node_2_h_1 = recipe_test_utils.create_recipe_node(recipe=recipe_2_h, node_name='node_1', job=job_2_h_1,
                                                          save=False)
        node_2_h_2 = recipe_test_utils.create_recipe_node(recipe=recipe_2_h, node_name='node_2', job=job_2_h_2,
                                                          save=False)
        node_2_e_3 = recipe_test_utils.create_recipe_node(recipe=recipe_2_e, node_name='node_3',
                                                          sub_recipe=recipe_2_e_3, save=False)
        node_2_e_4 = recipe_test_utils.create_recipe_node(recipe=recipe_2_e, node_name='node_4',
                                                          sub_recipe=recipe_2_e_4, save=False)
        node_2_f_3 = recipe_test_utils.create_recipe_node(recipe=recipe_2_f, node_name='node_3',
                                                          sub_recipe=recipe_2_f_3, save=False)
        node_2_f_4 = recipe_test_utils.create_recipe_node(recipe=recipe_2_f, node_name='node_4',
                                                          sub_recipe=recipe_2_f_4, save=False)
        node_2_g_3 = recipe_test_utils.create_recipe_node(recipe=recipe_2_g, node_name='node_3',
                                                          sub_recipe=recipe_2_g_3, save=False)
        node_2_g_4 = recipe_test_utils.create_recipe_node(recipe=recipe_2_g, node_name='node_4',
                                                          sub_recipe=recipe_2_g_4, save=False)
        node_2_h_3 = recipe_test_utils.create_recipe_node(recipe=recipe_2_h, node_name='node_3',
                                                          sub_recipe=recipe_2_h_3, save=False)
        node_2_h_4 = recipe_test_utils.create_recipe_node(recipe=recipe_2_h, node_name='node_4',
                                                          sub_recipe=recipe_2_h_4, save=False)
        Recipe.objects.bulk_create([recipe_1, recipe_1_e, recipe_1_f, recipe_1_g, recipe_1_h, recipe_1_e_3,
                                    recipe_1_e_4, recipe_1_f_3, recipe_1_f_4, recipe_1_g_3, recipe_1_g_4, recipe_1_h_3,
                                    recipe_1_h_4, recipe_2, recipe_2_e, recipe_2_f, recipe_2_g, recipe_2_h,
                                    recipe_2_e_3, recipe_2_e_4, recipe_2_f_3, recipe_2_f_4, recipe_2_g_3, recipe_2_g_4,
                                    recipe_2_h_3, recipe_2_h_4])
        Job.objects.bulk_create([job_1_a, job_1_b, job_1_c, job_1_d, job_1_e_1, job_1_e_2, job_1_f_1, job_1_f_2,
                                 job_1_g_1, job_1_g_2, job_1_h_1, job_1_h_2, job_2_a, job_2_b, job_2_c, job_2_d,
                                 job_2_e_1, job_2_e_2, job_2_f_1, job_2_f_2, job_2_g_1, job_2_g_2, job_2_h_1,
                                 job_2_h_2])
        RecipeNode.objects.bulk_create([node_1_a, node_1_b, node_1_c, node_1_d, node_1_e, node_1_f, node_1_g, node_1_h,
                                        node_1_e_1, node_1_e_2, node_1_f_1, node_1_f_2, node_1_g_1, node_1_g_2,
                                        node_1_h_1, node_1_h_2, node_1_e_3, node_1_e_4, node_1_f_3, node_1_f_4,
                                        node_1_g_3, node_1_g_4, node_1_h_3, node_1_h_4, node_2_a, node_2_b, node_2_c,
                                        node_2_d, node_2_e, node_2_f, node_2_g, node_2_h, node_2_e_1, node_2_e_2,
                                        node_2_f_1, node_2_f_2, node_2_g_1, node_2_g_2, node_2_h_1, node_2_h_2,
                                        node_2_e_3, node_2_e_4, node_2_f_3, node_2_f_4, node_2_g_3, node_2_g_4,
                                        node_2_h_3, node_2_h_4])

        when = now()
        supersede_jobs = {'node_c', 'node_d'}
        supersede_subrecipes = {'node_f', 'node_g', 'node_h'}
        unpublish_jobs = {'node_d'}
        supersede_recursive = {'node_g'}
        unpublish_recursive = {'node_h'}

        # Create message
        message = create_supersede_recipe_nodes_messages([recipe_1.id, recipe_2.id], when, supersede_jobs,
                                                         supersede_subrecipes, unpublish_jobs, supersede_recursive,
                                                         unpublish_recursive)[0]

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        # Ensure jobs for node_c and node_d are superseded
        qry = Job.objects.filter(id__in=[job_1_c.id, job_1_d.id, job_2_c.id, job_2_d.id], is_superseded=True)
        self.assertEqual(qry.count(), 4)
        # Ensure sub-recipes for node_f, node_g, and node_h are superseded
        recipe_ids = [recipe_1_f.id, recipe_1_g.id, recipe_1_h.id, recipe_2_f.id, recipe_2_g.id, recipe_2_h.id]
        qry = Recipe.objects.filter(id__in=recipe_ids, is_superseded=True)
        self.assertEqual(qry.count(), 8)
        # Ensure jobs for node_a and node_b are NOT superseded
        qry = Job.objects.filter(id__in=[job_1_a.id, job_1_b.id, job_2_a.id, job_2_b.id], is_superseded=False)
        self.assertEqual(qry.count(), 4)
        # Ensure sub-recipes for node_e are NOT superseded
        recipe_ids = [recipe_1_e.id, recipe_2_e.id]
        qry = Recipe.objects.filter(id__in=recipe_ids, is_superseded=False)
        self.assertEqual(qry.count(), 2)

        # Should be four messages
        # 1. Canceling jobs for node_c and node_d
        # 2. Unpublishing jobs for node_d
        # 3. Recursively supersede sub-recipes for node_g
        # 4. Recursively supersede/unpublish sub-recipes for node_h
        self.assertEqual(len(message.new_messages), 4)
        msg_cancel_jobs = None
        msg_unpublish_jobs = None
        msg_recur_supersede = None
        msg_recur_unpublish = None
        for msg in message.new_messages:
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
        self.assertSetEqual(set(msg_cancel_jobs._job_ids), {job_1_c.id, job_1_d.id, job_2_c.id, job_2_d.id})
        self.assertEqual(msg_cancel_jobs.when, when)

        self.assertIsNotNone(msg_unpublish_jobs)
        self.assertSetEqual(set(msg_unpublish_jobs._job_ids), {job_1_d.id, job_2_d.id})
        self.assertEqual(msg_unpublish_jobs.when, when)

        self.assertIsNotNone(msg_recur_supersede)
        self.assertSetEqual(set(msg_recur_supersede._recipe_ids), {recipe_1_g.id, recipe_2_g.id})
        self.assertEqual(msg_recur_supersede.when, when)
        self.assertTrue(msg_recur_supersede.supersede_all)
        self.assertFalse(msg_recur_supersede.unpublish_all)
        self.assertTrue(msg_recur_supersede.supersede_recursive_all)
        self.assertFalse(msg_recur_supersede.unpublish_recursive_all)

        self.assertIsNotNone(msg_recur_unpublish)
        self.assertSetEqual(set(msg_recur_unpublish._recipe_ids), {recipe_1_h.id, recipe_2_h.id})
        self.assertEqual(msg_recur_unpublish.when, when)
        self.assertTrue(msg_recur_unpublish.supersede_all)
        self.assertTrue(msg_recur_unpublish.unpublish_all)
        self.assertTrue(msg_recur_unpublish.supersede_recursive_all)
        self.assertTrue(msg_recur_unpublish.unpublish_recursive_all)

        # Test executing message again
        message.new_messages = []
        result = message.execute()
        self.assertTrue(result)

        # Check for same results and messages
        # Ensure jobs for node_c and node_d are superseded
        qry = Job.objects.filter(id__in=[job_1_c.id, job_1_d.id, job_2_c.id, job_2_d.id], is_superseded=True)
        self.assertEqual(qry.count(), 4)
        # Ensure sub-recipes for node_f, node_g, and node_h are superseded
        recipe_ids = [recipe_1_f.id, recipe_1_g.id, recipe_1_h.id, recipe_2_f.id, recipe_2_g.id, recipe_2_h.id]
        qry = Recipe.objects.filter(id__in=recipe_ids, is_superseded=True)
        self.assertEqual(qry.count(), 8)
        # Ensure jobs for node_a and node_b are NOT superseded
        qry = Job.objects.filter(id__in=[job_1_a.id, job_1_b.id, job_2_a.id, job_2_b.id], is_superseded=False)
        self.assertEqual(qry.count(), 4)
        # Ensure sub-recipes for node_e are NOT superseded
        recipe_ids = [recipe_1_e.id, recipe_2_e.id]
        qry = Recipe.objects.filter(id__in=recipe_ids, is_superseded=False)
        self.assertEqual(qry.count(), 2)

        # Should be four messages
        # 1. Canceling jobs for node_c and node_d
        # 2. Unpublishing jobs for node_d
        # 3. Recursively supersede sub-recipes for node_g
        # 4. Recursively supersede/unpublish sub-recipes for node_h
        self.assertEqual(len(message.new_messages), 4)
        msg_cancel_jobs = None
        msg_unpublish_jobs = None
        msg_recur_supersede = None
        msg_recur_unpublish = None
        for msg in message.new_messages:
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
        self.assertSetEqual(set(msg_cancel_jobs._job_ids), {job_1_c.id, job_1_d.id, job_2_c.id, job_2_d.id})
        self.assertEqual(msg_cancel_jobs.when, when)

        self.assertIsNotNone(msg_unpublish_jobs)
        self.assertSetEqual(set(msg_unpublish_jobs._job_ids), {job_1_d.id, job_2_d.id})
        self.assertEqual(msg_unpublish_jobs.when, when)

        self.assertIsNotNone(msg_recur_supersede)
        self.assertSetEqual(set(msg_recur_supersede._recipe_ids), {recipe_1_g.id, recipe_2_g.id})
        self.assertEqual(msg_recur_supersede.when, when)
        self.assertTrue(msg_recur_supersede.supersede_all)
        self.assertFalse(msg_recur_supersede.unpublish_all)
        self.assertTrue(msg_recur_supersede.supersede_recursive_all)
        self.assertFalse(msg_recur_supersede.unpublish_recursive_all)

        self.assertIsNotNone(msg_recur_unpublish)
        self.assertSetEqual(set(msg_recur_unpublish._recipe_ids), {recipe_1_h.id, recipe_2_h.id})
        self.assertEqual(msg_recur_unpublish.when, when)
        self.assertTrue(msg_recur_unpublish.supersede_all)
        self.assertTrue(msg_recur_unpublish.unpublish_all)
        self.assertTrue(msg_recur_unpublish.supersede_recursive_all)
        self.assertTrue(msg_recur_unpublish.unpublish_recursive_all)

    def test_execute_recursively(self):
        """Tests calling SupersedeRecipeNodes.execute() recursively"""

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
        recipe_2 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        job_2_a = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_b = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_c = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_d = job_test_utils.create_job(job_type=job_type, save=False)
        recipe_2_e = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_f = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_g = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_h = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        job_2_e_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_e_2 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_f_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_f_2 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_g_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_g_2 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_h_1 = job_test_utils.create_job(job_type=job_type, save=False)
        job_2_h_2 = job_test_utils.create_job(job_type=job_type, save=False)
        recipe_2_e_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_e_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_f_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_f_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_g_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_g_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_h_3 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        recipe_2_h_4 = recipe_test_utils.create_recipe(recipe_type=recipe_type, save=False)
        node_2_a = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_a', job=job_2_a, save=False)
        node_2_b = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_b', job=job_2_b, save=False)
        node_2_c = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_c', job=job_2_c, save=False)
        node_2_d = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_d', job=job_2_d, save=False)
        node_2_e = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_e', sub_recipe=recipe_2_e,
                                                        save=False)
        node_2_f = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_f', sub_recipe=recipe_2_f,
                                                        save=False)
        node_2_g = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_g', sub_recipe=recipe_2_g,
                                                        save=False)
        node_2_h = recipe_test_utils.create_recipe_node(recipe=recipe_2, node_name='node_h', sub_recipe=recipe_2_h,
                                                        save=False)
        node_2_e_1 = recipe_test_utils.create_recipe_node(recipe=recipe_2_e, node_name='node_1', job=job_2_e_1,
                                                          save=False)
        node_2_e_2 = recipe_test_utils.create_recipe_node(recipe=recipe_2_e, node_name='node_2', job=job_2_e_2,
                                                          save=False)
        node_2_f_1 = recipe_test_utils.create_recipe_node(recipe=recipe_2_f, node_name='node_1', job=job_2_f_1,
                                                          save=False)
        node_2_f_2 = recipe_test_utils.create_recipe_node(recipe=recipe_2_f, node_name='node_2', job=job_2_f_2,
                                                          save=False)
        node_2_g_1 = recipe_test_utils.create_recipe_node(recipe=recipe_2_g, node_name='node_1', job=job_2_g_1,
                                                          save=False)
        node_2_g_2 = recipe_test_utils.create_recipe_node(recipe=recipe_2_g, node_name='node_2', job=job_2_g_2,
                                                          save=False)
        node_2_h_1 = recipe_test_utils.create_recipe_node(recipe=recipe_2_h, node_name='node_1', job=job_2_h_1,
                                                          save=False)
        node_2_h_2 = recipe_test_utils.create_recipe_node(recipe=recipe_2_h, node_name='node_2', job=job_2_h_2,
                                                          save=False)
        node_2_e_3 = recipe_test_utils.create_recipe_node(recipe=recipe_2_e, node_name='node_3',
                                                          sub_recipe=recipe_2_e_3, save=False)
        node_2_e_4 = recipe_test_utils.create_recipe_node(recipe=recipe_2_e, node_name='node_4',
                                                          sub_recipe=recipe_2_e_4, save=False)
        node_2_f_3 = recipe_test_utils.create_recipe_node(recipe=recipe_2_f, node_name='node_3',
                                                          sub_recipe=recipe_2_f_3, save=False)
        node_2_f_4 = recipe_test_utils.create_recipe_node(recipe=recipe_2_f, node_name='node_4',
                                                          sub_recipe=recipe_2_f_4, save=False)
        node_2_g_3 = recipe_test_utils.create_recipe_node(recipe=recipe_2_g, node_name='node_3',
                                                          sub_recipe=recipe_2_g_3, save=False)
        node_2_g_4 = recipe_test_utils.create_recipe_node(recipe=recipe_2_g, node_name='node_4',
                                                          sub_recipe=recipe_2_g_4, save=False)
        node_2_h_3 = recipe_test_utils.create_recipe_node(recipe=recipe_2_h, node_name='node_3',
                                                          sub_recipe=recipe_2_h_3, save=False)
        node_2_h_4 = recipe_test_utils.create_recipe_node(recipe=recipe_2_h, node_name='node_4',
                                                          sub_recipe=recipe_2_h_4, save=False)
        Recipe.objects.bulk_create([recipe_1, recipe_1_e, recipe_1_f, recipe_1_g, recipe_1_h, recipe_1_e_3,
                                    recipe_1_e_4, recipe_1_f_3, recipe_1_f_4, recipe_1_g_3, recipe_1_g_4, recipe_1_h_3,
                                    recipe_1_h_4, recipe_2, recipe_2_e, recipe_2_f, recipe_2_g, recipe_2_h,
                                    recipe_2_e_3, recipe_2_e_4, recipe_2_f_3, recipe_2_f_4, recipe_2_g_3, recipe_2_g_4,
                                    recipe_2_h_3, recipe_2_h_4])
        Job.objects.bulk_create([job_1_a, job_1_b, job_1_c, job_1_d, job_1_e_1, job_1_e_2, job_1_f_1, job_1_f_2,
                                 job_1_g_1, job_1_g_2, job_1_h_1, job_1_h_2, job_2_a, job_2_b, job_2_c, job_2_d,
                                 job_2_e_1, job_2_e_2, job_2_f_1, job_2_f_2, job_2_g_1, job_2_g_2, job_2_h_1,
                                 job_2_h_2])
        RecipeNode.objects.bulk_create([node_1_a, node_1_b, node_1_c, node_1_d, node_1_e, node_1_f, node_1_g, node_1_h,
                                        node_1_e_1, node_1_e_2, node_1_f_1, node_1_f_2, node_1_g_1, node_1_g_2,
                                        node_1_h_1, node_1_h_2, node_1_e_3, node_1_e_4, node_1_f_3, node_1_f_4,
                                        node_1_g_3, node_1_g_4, node_1_h_3, node_1_h_4, node_2_a, node_2_b, node_2_c,
                                        node_2_d, node_2_e, node_2_f, node_2_g, node_2_h, node_2_e_1, node_2_e_2,
                                        node_2_f_1, node_2_f_2, node_2_g_1, node_2_g_2, node_2_h_1, node_2_h_2,
                                        node_2_e_3, node_2_e_4, node_2_f_3, node_2_f_4, node_2_g_3, node_2_g_4,
                                        node_2_h_3, node_2_h_4])

        when = now()
        supersede_jobs = {'node_c', 'node_d'}
        supersede_subrecipes = {'node_f', 'node_g', 'node_h'}
        unpublish_jobs = {'node_d'}
        supersede_recursive = {'node_g'}
        unpublish_recursive = {'node_h'}

        # Create original message
        message = create_supersede_recipe_nodes_messages([recipe_1.id, recipe_2.id], when, supersede_jobs,
                                                         supersede_subrecipes, unpublish_jobs, supersede_recursive,
                                                         unpublish_recursive)[0]

        # Execute original message and all resulting messages
        messages = [message]
        while messages:
            msg = messages.pop(0)
            result = msg.execute()
            self.assertTrue(result)
            messages.extend(msg.new_messages)

        # Ensure jobs for node_c and node_d are superseded, as well as recursive jobs under node_g and node_h
        superseded_job_ids = [job_1_c.id, job_1_d.id, job_1_g_1.id, job_1_g_2.id, job_1_h_1.id, job_1_h_2.id,
                              job_2_c.id, job_2_d.id, job_2_g_1.id, job_2_g_2.id, job_2_h_1.id, job_2_h_2.id]
        qry = Job.objects.filter(id__in=superseded_job_ids, is_superseded=True)
        self.assertEqual(qry.count(), 12)
        # Ensure sub-recipes for node_f, node_g, and node_h are superseded, as well as recursive sub-recipes under
        # node_g and node_h
        superseded_recipe_ids = [recipe_1_f.id, recipe_1_g.id, recipe_1_h.id, recipe_1_g_3.id, recipe_1_g_4.id,
                                 recipe_1_h_3.id, recipe_1_h_4.id, recipe_2_f.id, recipe_2_g.id, recipe_2_h.id,
                                 recipe_2_g_3.id, recipe_2_g_4.id, recipe_2_h_3.id, recipe_2_h_4.id]
        qry = Recipe.objects.filter(id__in=superseded_recipe_ids, is_superseded=True)
        self.assertEqual(qry.count(), 14)
        # Ensure jobs for node_a and node_b are NOT superseded, as well as recursive jobs under node_e and node_f
        job_ids = [job_1_a.id, job_1_b.id, job_1_e_1.id, job_1_e_2.id, job_1_f_1.id, job_1_f_2.id, job_2_a.id,
                   job_2_b.id, job_2_e_1.id, job_2_e_2.id, job_2_f_1.id, job_2_f_2.id]
        qry = Job.objects.filter(id__in=job_ids, is_superseded=False)
        self.assertEqual(qry.count(), 12)
        # Ensure sub-recipes for node_e are NOT superseded, as well as recursive sub-recipes under node_f
        recipe_ids = [recipe_1_e.id, recipe_1_f_3.id, recipe_1_f_4.id, recipe_2_e.id, recipe_2_f_3.id, recipe_2_f_4.id]
        qry = Recipe.objects.filter(id__in=recipe_ids, is_superseded=False)
        self.assertEqual(qry.count(), 6)
