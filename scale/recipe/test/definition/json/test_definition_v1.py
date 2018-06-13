from __future__ import unicode_literals

import django
from django.test import TestCase

from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from recipe.definition.definition import RecipeDefinition
from recipe.definition.exceptions import InvalidDefinition
from recipe.definition.json.definition_v1 import convert_recipe_definition_to_v1_json, RecipeDefinitionV1


class TestRecipeDefinitionV1(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_recipe_definition_to_v1_json_empty(self):
        """Tests calling convert_recipe_definition_to_v1_json() with an empty definition"""

        interface = Interface()
        definition = RecipeDefinition(interface)
        json = convert_recipe_definition_to_v1_json(definition)
        RecipeDefinitionV1(definition=json.get_dict(), do_validate=True)  # Revalidate

    def test_convert_recipe_definition_to_v1_json_full(self):
        """Tests calling convert_recipe_definition_to_v1_json() with a full definition"""

        interface = Interface()
        interface.add_parameter(FileParameter('file_param_a', ['image/gif']))
        interface.add_parameter(JsonParameter('json_param_a', 'object'))
        interface.add_parameter(JsonParameter('json_param_b', 'object', required=False))

        definition = RecipeDefinition(interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        definition.add_job_node('B', 'job_type_2', '2.0', 1)
        definition.add_job_node('C', 'job_type_3', '1.0', 2)
        definition.add_recipe_node('D', 'recipe_type_1', 1)
        definition.add_job_node('E', 'job_type_4', '1.0', 1)
        definition.add_dependency('A', 'B')
        definition.add_dependency('A', 'C')
        definition.add_dependency('B', 'E')
        definition.add_dependency('C', 'D')
        definition.add_recipe_input_connection('A', 'input_1', 'file_param_a')
        definition.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition.add_recipe_input_connection('D', 'd_input_2', 'json_param_a')

        json = convert_recipe_definition_to_v1_json(definition)
        RecipeDefinitionV1(definition=json.get_dict(), do_validate=True)  # Revalidate
        job_names = {job_dict['name'] for job_dict in json.get_dict()['jobs']}
        self.assertSetEqual(job_names, {'A', 'B', 'C', 'E'})  # D is omitted (recipe node)

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        RecipeDefinitionV1(do_validate=True)

        # Invalid version
        definition = {'version': 'BAD'}
        self.assertRaises(InvalidDefinition, RecipeDefinitionV1, definition, True)

        # Valid v1 definition
        def_v1_dict = {'version': '1.0',
                       'input_data': [{'name': 'foo', 'media_types': ['image/tiff'], 'type': 'files'},
                                      {'name': 'bar', 'type': 'property', 'required': False}],
                       'jobs': [{'name': 'node_a', 'job_type': {'name': 'job-type-1', 'version': '1.0'},
                                 'recipe_inputs': [{'recipe_input': 'foo', 'job_input': 'input_a'}]},
                                {'name': 'node_b', 'job_type': {'name': 'job-type-2', 'version': '2.0'},
                                 'recipe_inputs': [{'recipe_input': 'foo', 'job_input': 'input_a'}],
                                 'dependencies': [{'name': 'node_a',
                                                   'connections': [{'output': 'output_a', 'input': 'input_b'}]}]}]}
        RecipeDefinitionV1(definition=def_v1_dict, do_validate=True)
