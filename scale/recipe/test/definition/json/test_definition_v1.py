from __future__ import unicode_literals

import django
from django.test import TestCase

from data.filter.filter import DataFilter
from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from job.test import utils as job_test_utils
from recipe.definition.definition import RecipeDefinition
from recipe.definition.exceptions import InvalidDefinition
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json, RecipeDefinitionV6


class TestRecipeDefinitionV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_recipe_definition_to_v6_json_empty(self):
        """Tests calling convert_recipe_definition_to_v6_json() with an empty definition"""

        interface = Interface()
        definition = RecipeDefinition(interface)
        json = convert_recipe_definition_to_v6_json(definition)
        RecipeDefinitionV6(definition=json.get_dict(), do_validate=True)  # Revalidate
        self.assertDictEqual(json.get_dict()['input'], {'files': [], 'json': []})

    def test_convert_recipe_definition_to_v6_json_full(self):
        """Tests calling convert_recipe_definition_to_v6_json() with a full definition"""

        interface = Interface()
        interface.add_parameter(FileParameter('file_param_a', ['image/gif']))
        interface.add_parameter(JsonParameter('json_param_a', 'object'))
        interface.add_parameter(JsonParameter('json_param_b', 'object', required=False))

        definition = RecipeDefinition(interface)
        definition.add_job_node('A', 'job_type_1', '1.0', 1)
        definition.add_job_node('B', 'job_type_2', '2.0', 1)
        definition.add_job_node('C', 'job_type_3', '1.0', 2)
        definition.add_recipe_node('D', 'recipe_type_1', 1)
        definition.add_condition_node('E', Interface(), DataFilter())
        definition.add_job_node('F', 'job_type_4', '1.0', 1)
        definition.add_dependency('A', 'B')
        definition.add_dependency('A', 'C')
        definition.add_dependency('B', 'E')
        definition.add_dependency('C', 'D')
        definition.add_dependency('E', 'F')
        definition.add_recipe_input_connection('A', 'input_a', 'file_param_a')
        definition.add_dependency_input_connection('B', 'b_input_a', 'A', 'a_output_1')
        definition.add_dependency_input_connection('C', 'c_input_a', 'A', 'a_output_2')
        definition.add_dependency_input_connection('D', 'd_input_a', 'C', 'c_output_1')
        definition.add_recipe_input_connection('D', 'd_input_b', 'json_param_a')

        json = convert_recipe_definition_to_v6_json(definition)
        RecipeDefinitionV6(definition=json.get_dict(), do_validate=True)  # Revalidate
        self.assertSetEqual(set(json.get_dict()['nodes'].keys()), {'A', 'B', 'C', 'D', 'E', 'F'})

    def test_get_definition_empty(self):
        """Tests calling get_definition() from an empty JSON"""

        json = RecipeDefinitionV6(do_validate=True)
        definition = json.get_definition()
        self.assertDictEqual(definition.input_interface.parameters, {})
        self.assertDictEqual(definition.graph, {})

    def test_get_definition_full(self):
        """Tests calling get_definition() from a full JSON"""

        json_dict = {
            'input': {
                'files': [{'name': 'foo', 'media_types': ['image/tiff'], 'required': True, 'multiple': True}],
                'json': [{'name': 'bar', 'type': 'integer', 'required': False}]
            },
            'nodes': {
                'node_a': {
                    'dependencies': [],
                    'input': {
                        'input_a': {'type': 'recipe', 'input': 'foo'}
                    },
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': 'job-type-1',
                        'job_type_version': '1.0',
                        'job_type_revision': 1
                    }
                },
                'node_b': {
                    'dependencies': [{'name': 'node_a'}],
                    'input': {
                        'input_a': {'type': 'recipe', 'input': 'foo'},
                        'input_b': {'type': 'dependency', 'node': 'node_a', 'output': 'output_a'}
                    },
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': 'job-type-2',
                        'job_type_version': '2.0',
                        'job_type_revision': 1
                    }
                },
                'node_c': {
                    'dependencies': [{'name': 'node_b'}],
                    'input': {
                        'input_a': {'type': 'recipe', 'input': 'bar'},
                        'input_b': {'type': 'dependency', 'node': 'node_b', 'output': 'output_a'}
                    },
                    'node_type': {
                        'node_type': 'condition',
                        'interface': {'files': [{'name': 'input_b', 'media_types': ['image/tiff'], 'required': True, 'multiple': True}],
                                       'json': []},
                        'data_filter': {'filters': [{'name': 'input_b', 'type': 'media-type', 'condition': '==', 'values': ['image/tiff']}]}
                    }
                },
                'node_d': {
                    'dependencies': [{'name': 'node_c'}],
                    'input': {
                        'input_a': {'type': 'recipe', 'input': 'bar'},
                        'input_b': {'type': 'dependency', 'node': 'node_c', 'output': 'output_a'}
                    },
                    'node_type': {
                        'node_type': 'recipe',
                        'recipe_type_name': 'recipe-type-1',
                        'recipe_type_revision': 5
                    }
                },
                'node_e': {
                    'dependencies': [{'name': 'node_c', 'acceptance': False}],
                    'input': {
                        'input_a': {'type': 'recipe', 'input': 'bar'},
                        'input_b': {'type': 'dependency', 'node': 'node_c', 'output': 'output_a'}
                    },
                    'node_type': {
                        'node_type': 'recipe',
                        'recipe_type_name': 'recipe-type-2',
                        'recipe_type_revision': 1
                    }
                }
            }
        }

        json = RecipeDefinitionV6(definition=json_dict, do_validate=True)
        definition = json.get_definition()
        self.assertSetEqual(set(definition.input_interface.parameters.keys()), {'foo', 'bar'})
        self.assertSetEqual(set(definition.graph.keys()), {'node_a', 'node_b', 'node_c', 'node_d', 'node_e'})

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        RecipeDefinitionV6(do_validate=True)

        # Invalid version
        definition = {'version': 'BAD'}
        self.assertRaises(InvalidDefinition, RecipeDefinitionV6, definition, True)

        # Valid v6 definition
        def_v6_dict = {'version': '6',
                       'input': {'files': [{'name': 'foo', 'media_types': ['image/tiff'], 'required': True,
                                            'multiple': True}],
                                 'json': [{'name': 'bar', 'type': 'string', 'required': False}]},
                       'nodes': {'node_a': {'dependencies': [],
                                            'input': {'input_a': {'type': 'recipe', 'input': 'foo'}},
                                            'node_type': {'node_type': 'job', 'job_type_name': 'job-type-1',
                                                          'job_type_version': '1.0', 'job_type_revision': 1}},
                                 'node_b': {'dependencies': [{'name': 'node_a'}],
                                            'input': {'input_a': {'type': 'recipe', 'input': 'foo'},
                                                      'input_b': {'type': 'dependency', 'node': 'node_a',
                                                                  'output': 'output_a'}},
                                            'node_type': {'node_type': 'job', 'job_type_name': 'job-type-2',
                                                          'job_type_version': '2.0', 'job_type_revision': 1}},
                                 'node_c': {'dependencies': [{'name': 'node_b'}],
                                            'input': {'input_a': {'type': 'recipe', 'input': 'bar'},
                                                      'input_b': {'type': 'dependency', 'node': 'node_b',
                                                                  'output': 'output_a'}},
                                            'node_type': {'node_type': 'condition',
                                                                       'interface': {'files': [{'name': 'input_b',
                                                                                                'media_types': ['image/tiff'],
                                                                                                'required': True,
                                                                                                'multiple': True}],
                                                                                     'json': []},
                                                                       'data_filter': {'filters': [{'name': 'output_a',
                                                                                                    'type': 'media-type',
                                                                                                    'condition': '==',
                                                                                                    'values': ['image/tiff']}]}}},
                                 'node_d': {'dependencies': [{'name': 'node_c'}],
                                            'input': {'input_a': {'type': 'recipe', 'input': 'bar'},
                                                      'input_b': {'type': 'dependency', 'node': 'node_c',
                                                                  'output': 'output_a'}},
                                            'node_type': {'node_type': 'recipe', 'recipe_type_name': 'recipe-type-1',
                                                          'recipe_type_revision': 5}}}}

        try:
            RecipeDefinitionV6(definition=def_v6_dict, do_validate=True)
        except InvalidDefinition:
            self.fail('Recipe definition failed validation unexpectedly')
