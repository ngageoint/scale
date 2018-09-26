from __future__ import unicode_literals

import django
from django.test import TestCase

from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from job.models import Job
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.instance.exceptions import InvalidRecipe
from recipe.instance.json.recipe_v6 import convert_recipe_to_v6_json, RecipeInstanceV6
from recipe.instance.recipe import RecipeInstance
from recipe.test import utils as recipe_test_utils


class TestRecipeInstanceV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_recipe_to_v6_json_empty(self):
        """Tests calling convert_recipe_to_v6_json() with an empty recipe instance"""

        recipe = recipe_test_utils.create_recipe()
        definition = RecipeDefinition(Interface())
        recipe_instance = RecipeInstance(definition, recipe, [])
        json = convert_recipe_to_v6_json(recipe_instance)
        RecipeInstanceV6(json=json.get_dict(), do_validate=True)  # Revalidate
        self.assertDictEqual(json.get_dict()['nodes'], {})

    def test_convert_recipe_to_v6_json(self):
        """Tests calling convert_recipe_to_v6_json() successfully"""

        job_type_1 = job_test_utils.create_job_type()
        job_type_2 = job_test_utils.create_job_type()
        job_type_3 = job_test_utils.create_job_type()
        job_type_4 = job_test_utils.create_job_type()
        recipe_type_1 = recipe_test_utils.create_recipe_type()

        interface = Interface()
        interface.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface.add_parameter(JsonParameter('json_param_1', 'object'))

        definition = RecipeDefinition(interface)
        definition.add_job_node('A', job_type_1.name, job_type_1.version, job_type_1.revision_num)
        definition.add_job_node('B', job_type_2.name, job_type_2.version, job_type_2.revision_num)
        definition.add_job_node('C', job_type_3.name, job_type_3.version, job_type_3.revision_num)
        definition.add_recipe_node('D', recipe_type_1.name, recipe_type_1.revision_num)
        definition.add_job_node('E', job_type_4.name, job_type_4.version, job_type_4.revision_num)
        definition.add_dependency('A', 'B')
        definition.add_dependency('A', 'C')
        definition.add_dependency('B', 'E')
        definition.add_dependency('C', 'D')
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
        recipe_d = recipe_test_utils.create_recipe(recipe_type=recipe_type_1)
        recipe_node_a = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='A', job=job_a, save=False)
        recipe_node_b = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='B', job=job_b, save=False)
        recipe_node_c = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='C', job=job_c, save=False)
        recipe_node_d = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='D', sub_recipe=recipe_d,
                                                             save=False)
        recipe_node_e = recipe_test_utils.create_recipe_node(recipe=recipe, node_name='E', job=job_e, save=False)
        recipe_nodes = [recipe_node_a, recipe_node_b, recipe_node_c, recipe_node_d, recipe_node_e]

        recipe_instance = RecipeInstance(definition, recipe, recipe_nodes)
        json = convert_recipe_to_v6_json(recipe_instance)
        RecipeInstanceV6(json=json.get_dict(), do_validate=True)  # Revalidate
        self.assertSetEqual(set(json.get_dict()['nodes'].keys()), {'A', 'B', 'C', 'D', 'E'})

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        RecipeInstanceV6(do_validate=True)

        # Invalid version
        json = {'version': 'BAD'}
        self.assertRaises(InvalidRecipe, RecipeInstanceV6, json, True)
