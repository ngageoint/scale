from __future__ import unicode_literals

import django
from django.test import TestCase

from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from data.filter.filter import DataFilter
from data.interface.interface import Interface
from job.models import Job
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json
from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition
from recipe.models import Recipe, RecipeCondition, RecipeNode
from recipe.test import utils as recipe_test_utils


class TestRecipe(TestCase):

    def setUp(self):
        django.setup()

    def test_get_jobs_to_update(self):
        """Tests calling Recipe.get_jobs_to_update()"""

        job_type = job_test_utils.create_job_type()
        sub_recipe_type = recipe_test_utils.create_recipe_type()

        definition = RecipeDefinition(Interface())
        definition.add_job_node('A', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('B', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('C', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('D', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('E', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('F', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('G', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('H', job_type.name, job_type.version, job_type.revision_num)
        definition.add_dependency('A', 'C')
        definition.add_dependency('A', 'E')
        definition.add_dependency('A', 'H')
        definition.add_dependency('B', 'E')
        definition.add_dependency('B', 'G')
        definition.add_dependency('C', 'D')
        definition.add_dependency('E', 'F')
        definition.add_dependency('G', 'H')

        job_a = job_test_utils.create_job(job_type=job_type, status='COMPLETED', save=False)
        job_c = job_test_utils.create_job(job_type=job_type, status='CANCELED', num_exes=0, save=False)
        job_d = job_test_utils.create_job(job_type=job_type, status='PENDING', num_exes=0, save=False)
        job_e = job_test_utils.create_job(job_type=job_type, status='BLOCKED', num_exes=0, save=False)
        job_f = job_test_utils.create_job(job_type=job_type, status='PENDING', num_exes=0, save=False)
        job_h = job_test_utils.create_job(job_type=job_type, status='PENDING', num_exes=0, save=False)
        Job.objects.bulk_create([job_a, job_c, job_d, job_e, job_f, job_h])

        recipe_b = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type, save=False)
        recipe_b.jobs_completed = 3
        recipe_b.jobs_running = 2
        recipe_b.jobs_total = 5
        recipe_g = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type, save=False)
        recipe_g.jobs_completed = 2
        recipe_g.jobs_failed = 1
        recipe_g.jobs_total = 3
        Recipe.objects.bulk_create([recipe_b, recipe_g])

        definition_json_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_json_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', job=job_a, save=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='B', sub_recipe=recipe_b,
                                                             save=False)
        recipe_node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='C', job=job_c, save=False)
        recipe_node_d = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='D', job=job_d, save=False)
        recipe_node_e = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='E', job=job_e, save=False)
        recipe_node_f = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='F', job=job_f, save=False)
        recipe_node_g = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='G', sub_recipe=recipe_g,
                                                             save=False)
        recipe_node_h = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='H', job=job_h, save=False)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_b, recipe_node_c, recipe_node_d, recipe_node_e,
                                        recipe_node_f, recipe_node_g, recipe_node_h])

        recipe_instance = Recipe.objects.get_recipe_instance(recipe.id)
        results = recipe_instance.get_jobs_to_update()
        self.assertSetEqual(set(results['BLOCKED']), {job_d.id, job_h.id})
        self.assertSetEqual(set(results['PENDING']), {job_e.id})

    def test_get_nodes_to_create(self):
        """Tests calling Recipe.get_nodes_to_create()"""

        job_type = job_test_utils.create_job_type()
        sub_recipe_type = recipe_test_utils.create_recipe_type()

        # Create recipe
        definition = RecipeDefinition(Interface())
        definition.add_job_node('A', job_type.name, job_type.version, job_type.revision_num)
        definition.add_condition_node('B', Interface(), DataFilter(True))
        definition.add_condition_node('C', Interface(), DataFilter(True))
        definition.add_condition_node('D', Interface(), DataFilter(False))
        definition.add_job_node('E', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('F', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('G', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_recipe_node('H', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_dependency('A', 'D')
        definition.add_dependency('A', 'E')
        definition.add_dependency('B', 'E')
        definition.add_dependency('B', 'F')
        definition.add_dependency('C', 'F')
        definition.add_dependency('D', 'G')
        definition.add_dependency('E', 'G')
        definition.add_dependency('E', 'H')
        definition_json_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_json_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)

        # Nodes A, B, and D already exist
        job_a = job_test_utils.create_job(job_type=job_type, status='COMPLETED', save=True)
        condition_b = recipe_test_utils.create_recipe_condition(is_processed=True, is_accepted=True, save=False)
        condition_d = recipe_test_utils.create_recipe_condition(is_processed=True, is_accepted=False, save=False)
        RecipeCondition.objects.bulk_create([condition_b, condition_d])
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', job=job_a, save=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='B', condition=condition_b,
                                                             save=False)
        recipe_node_d = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='D', condition=condition_d,
                                                             save=False)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_b, recipe_node_d])

        recipe_instance = Recipe.objects.get_recipe_instance(recipe.id)
        nodes_to_create = recipe_instance.get_nodes_to_create()
        self.assertSetEqual(set(nodes_to_create.keys()), {'C', 'E', 'H'})

    def test_get_nodes_to_process_input(self):
        """Tests calling Recipe.get_nodes_to_process_input()"""

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        job_type = job_test_utils.create_job_type()
        sub_recipe_type = recipe_test_utils.create_recipe_type()

        # Create recipe
        definition = RecipeDefinition(Interface())
        definition.add_job_node('A', job_type.name, job_type.version, job_type.revision_num)
        definition.add_condition_node('B', Interface(), DataFilter(True))
        definition.add_condition_node('C', Interface(), DataFilter(True))
        definition.add_condition_node('D', Interface(), DataFilter(False))
        definition.add_job_node('E', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('F', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('G', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_recipe_node('H', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_dependency('A', 'D')
        definition.add_dependency('A', 'E')
        definition.add_dependency('B', 'E')
        definition.add_dependency('B', 'F')
        definition.add_dependency('C', 'F')
        definition.add_dependency('D', 'G')
        definition.add_dependency('E', 'G')
        definition.add_dependency('E', 'H')
        definition_json_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_json_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, input=data_dict)

        # Nodes A, B, and D already exist
        job_a = job_test_utils.create_job(job_type=job_type, status='COMPLETED', input=data_dict, output=data_dict,
                                          save=True)
        condition_b = recipe_test_utils.create_recipe_condition(is_processed=True, is_accepted=True, save=False)
        condition_d = recipe_test_utils.create_recipe_condition(is_processed=True, is_accepted=False, save=False)
        RecipeCondition.objects.bulk_create([condition_b, condition_d])
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', job=job_a, save=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='B', condition=condition_b,
                                                             save=False)
        recipe_node_d = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='D', condition=condition_d,
                                                             save=False)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_b, recipe_node_d])

        recipe_instance = Recipe.objects.get_recipe_instance(recipe.id)
        nodes_to_process = recipe_instance.get_nodes_to_process_input()
        self.assertSetEqual(set(nodes_to_process.keys()), {'C', 'E'})

    def test_get_original_leaf_nodes(self):
        """Tests calling Recipe.get_original_leaf_nodes()"""

        job_type = job_test_utils.create_job_type()
        sub_recipe_type = recipe_test_utils.create_recipe_type()

        definition = RecipeDefinition(Interface())
        definition.add_job_node('A', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('B', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('C', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('D', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('E', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('F', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('G', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('H', job_type.name, job_type.version, job_type.revision_num)
        definition.add_dependency('A', 'C')
        definition.add_dependency('A', 'E')
        definition.add_dependency('A', 'H')
        definition.add_dependency('C', 'D')
        definition.add_dependency('G', 'H')

        job_a = job_test_utils.create_job(job_type=job_type, status='COMPLETED', save=False, is_superseded=True)
        job_c = job_test_utils.create_job(job_type=job_type, status='CANCELED', num_exes=0, save=False)
        job_d = job_test_utils.create_job(job_type=job_type, status='PENDING', num_exes=0, save=False)
        job_e = job_test_utils.create_job(job_type=job_type, status='BLOCKED', num_exes=0, save=False)
        job_f = job_test_utils.create_job(job_type=job_type, status='PENDING', num_exes=0, save=False)
        job_h = job_test_utils.create_job(job_type=job_type, status='PENDING', num_exes=0, save=False)
        Job.objects.bulk_create([job_a, job_c, job_d, job_e, job_f, job_h])

        recipe_b = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type, save=False)
        recipe_b.jobs_completed = 3
        recipe_b.jobs_running = 2
        recipe_b.jobs_total = 5
        recipe_g = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type, save=False)
        recipe_g.jobs_completed = 2
        recipe_g.jobs_failed = 1
        recipe_g.jobs_total = 3
        Recipe.objects.bulk_create([recipe_b, recipe_g])

        definition_json_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_json_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', job=job_a, save=False,
                                                             is_original=False)
        recipe_node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='C', job=job_c, save=False,
                                                             is_original=False)
        recipe_node_d = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='D', job=job_d, save=False,
                                                             is_original=False)
        recipe_node_e = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='E', job=job_e, save=False)
        recipe_node_f = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='F', job=job_f, save=False)
        recipe_node_h = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='H', job=job_h, save=False)

        recipe_node_g = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='G', sub_recipe=recipe_g,
                                                             save=False, is_original=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='B', sub_recipe=recipe_b,
                                                             save=False)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_b, recipe_node_c, recipe_node_d, recipe_node_e,
                                        recipe_node_f, recipe_node_g, recipe_node_h])

        recipe_instance = Recipe.objects.get_recipe_instance(recipe.id)
        results = recipe_instance.get_original_leaf_nodes()
        self.assertEqual(len(results.values()), 4)

        leaf_jobs = [node.job.id for node in results.values() if node.node_type == JobNodeDefinition.NODE_TYPE]
        leaf_recipes = [node.recipe.id for node in results.values() if node.node_type == RecipeNodeDefinition.NODE_TYPE]

        self.assertItemsEqual(leaf_jobs, [recipe_node_e.job.id, recipe_node_f.job.id, recipe_node_h.job.id])
        self.assertItemsEqual(leaf_recipes, [recipe_node_b.sub_recipe.id])

    def test_has_completed_empty(self):
        """Tests calling Recipe.has_completed() when a recipe is empty and has not created its nodes yet"""

        job_type = job_test_utils.create_job_type()
        sub_recipe_type = recipe_test_utils.create_recipe_type()

        definition = RecipeDefinition(Interface())
        definition.add_job_node('A', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('B', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('C', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('D', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('E', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('F', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('G', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('H', job_type.name, job_type.version, job_type.revision_num)
        definition.add_dependency('A', 'C')
        definition.add_dependency('A', 'E')
        definition.add_dependency('A', 'H')
        definition.add_dependency('C', 'D')
        definition.add_dependency('G', 'H')

        definition_json_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_json_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)

        recipe_instance = Recipe.objects.get_recipe_instance(recipe.id)
        self.assertFalse(recipe_instance.has_completed())

    def test_has_completed_false(self):
        """Tests calling Recipe.has_completed() when an entire recipe has not completed"""

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        job_type = job_test_utils.create_job_type()
        sub_recipe_type = recipe_test_utils.create_recipe_type()

        definition = RecipeDefinition(Interface())
        definition.add_job_node('A', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('B', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('C', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('D', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('E', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('F', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('G', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('H', job_type.name, job_type.version, job_type.revision_num)
        definition.add_dependency('A', 'C')
        definition.add_dependency('A', 'E')
        definition.add_dependency('A', 'H')
        definition.add_dependency('C', 'D')
        definition.add_dependency('G', 'H')

        job_a = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_c = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_d = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_e = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_f = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_h = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        Job.objects.bulk_create([job_a, job_c, job_d, job_e, job_f, job_h])

        recipe_b = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type, save=False)
        recipe_b.is_completed = True
        recipe_g = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type, save=False)
        recipe_g.is_completed = False
        Recipe.objects.bulk_create([recipe_b, recipe_g])

        definition_json_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_json_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', job=job_a, save=False,
                                                             is_original=False)
        recipe_node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='C', job=job_c, save=False,
                                                             is_original=False)
        recipe_node_d = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='D', job=job_d, save=False,
                                                             is_original=False)
        recipe_node_e = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='E', job=job_e, save=False)
        recipe_node_f = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='F', job=job_f, save=False)
        recipe_node_h = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='H', job=job_h, save=False)

        recipe_node_g = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='G', sub_recipe=recipe_g,
                                                             save=False, is_original=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='B', sub_recipe=recipe_b,
                                                             save=False)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_b, recipe_node_c, recipe_node_d, recipe_node_e,
                                        recipe_node_f, recipe_node_g, recipe_node_h])

        recipe_instance = Recipe.objects.get_recipe_instance(recipe.id)
        self.assertFalse(recipe_instance.has_completed())

    def test_has_completed_true(self):
        """Tests calling Recipe.has_completed() when an entire recipe has completed"""

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        job_type = job_test_utils.create_job_type()
        sub_recipe_type = recipe_test_utils.create_recipe_type()

        definition = RecipeDefinition(Interface())
        definition.add_job_node('A', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('B', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('C', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('D', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('E', job_type.name, job_type.version, job_type.revision_num)
        definition.add_job_node('F', job_type.name, job_type.version, job_type.revision_num)
        definition.add_recipe_node('G', sub_recipe_type.name, sub_recipe_type.revision_num)
        definition.add_job_node('H', job_type.name, job_type.version, job_type.revision_num)
        definition.add_condition_node('I', Interface(), DataFilter(False))
        definition.add_job_node('J', job_type.name, job_type.version, job_type.revision_num)
        definition.add_dependency('A', 'C')
        definition.add_dependency('A', 'E')
        definition.add_dependency('A', 'H')
        definition.add_dependency('C', 'D')
        definition.add_dependency('G', 'H')
        definition.add_dependency('A', 'I')
        definition.add_dependency('I', 'J')

        job_a = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_c = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_d = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_e = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_f = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        job_h = job_test_utils.create_job(job_type=job_type, status='COMPLETED', output=data_dict, save=False)
        Job.objects.bulk_create([job_a, job_c, job_d, job_e, job_f, job_h])

        condition_i = recipe_test_utils.create_recipe_condition(is_processed=True, is_accepted=False, save=True)
        recipe_b = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type, save=False)
        recipe_b.is_completed = True
        recipe_g = recipe_test_utils.create_recipe(recipe_type=sub_recipe_type, save=False)
        recipe_g.is_completed = True
        Recipe.objects.bulk_create([recipe_b, recipe_g])

        definition_json_dict = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition_json_dict)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', job=job_a, save=False,
                                                             is_original=False)
        recipe_node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='C', job=job_c, save=False,
                                                             is_original=False)
        recipe_node_d = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='D', job=job_d, save=False,
                                                             is_original=False)
        recipe_node_e = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='E', job=job_e, save=False)
        recipe_node_f = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='F', job=job_f, save=False)
        recipe_node_h = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='H', job=job_h, save=False)
        recipe_node_i = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='I', condition=condition_i,
                                                             save=False)

        recipe_node_g = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='G', sub_recipe=recipe_g,
                                                             save=False, is_original=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='B', sub_recipe=recipe_b,
                                                             save=False)
        RecipeNode.objects.bulk_create([recipe_node_a, recipe_node_b, recipe_node_c, recipe_node_d, recipe_node_e,
                                        recipe_node_f, recipe_node_g, recipe_node_h, recipe_node_i])

        recipe_instance = Recipe.objects.get_recipe_instance(recipe.id)
        self.assertTrue(recipe_instance.has_completed())
