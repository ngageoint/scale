from __future__ import unicode_literals

import django
from django.test import TestCase

from data.interface.interface import Interface
from data.interface.parameter import FileParameter, JsonParameter
from job.models import JobType
from job.test import utils as job_test_utils
from recipe.configuration.definition.recipe_definition import LegacyRecipeDefinition as OldRecipeDefinition
from recipe.definition.definition import RecipeDefinition
from recipe.diff.diff import RecipeDiff
from recipe.diff.exceptions import InvalidDiff
from recipe.diff.json.diff_v6 import convert_diff_to_v6, convert_recipe_diff_to_v6_json, RecipeDiffV6
from recipe.handlers.graph import RecipeGraph
from recipe.handlers.graph_delta import RecipeGraphDelta


class TestRecipeDiffV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_diff_to_v6_empty(self):
        """Tests calling convert_diff_to_v6() with an empty diff"""

        # Try diff with empty graphs
        graph_a = RecipeGraph()
        graph_b = RecipeGraph()
        diff = RecipeGraphDelta(graph_a, graph_b)
        json = convert_diff_to_v6(diff)
        RecipeDiffV6(diff=json.get_dict(), do_validate=True)  # Revalidate

    def test_convert_diff_to_v6_full_diff(self):
        """Tests calling convert_diff_to_v6() with a full diff with all types (deleted, new, changed, etc) of nodes"""

        job_a = job_test_utils.create_job()
        job_b = job_test_utils.create_job()
        job_c = job_test_utils.create_job()
        job_d = job_test_utils.create_job()
        job_e = job_test_utils.create_job()
        job_f = job_test_utils.create_job()

        new_job_type_d = JobType.objects.get(id=job_d.job_type_id)
        new_job_type_d.version = 'new_version'
        new_job_type_d.save()

        definition_a = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }, {
                'name': 'Recipe Input 2',
                'type': 'property'
            }],
            'jobs': [{
                'name': 'Job A',
                'job_type': {
                    'name': job_a.job_type.name,
                    'version': job_a.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 1',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job B',
                'job_type': {
                    'name': job_b.job_type.name,
                    'version': job_b.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 2',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job C',
                'job_type': {
                    'name': job_c.job_type.name,
                    'version': job_c.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 2',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job D',
                'job_type': {
                    'name': job_d.job_type.name,
                    'version': job_d.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job A',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }, {
                    'name': 'Job B',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 2',
                    }],
                }]
            }, {
                'name': 'Job E',
                'job_type': {
                    'name': job_e.job_type.name,
                    'version': job_e.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job D',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }]
            }]
        }
        graph_a = OldRecipeDefinition(definition_a).get_graph()

        definition_b = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }, {
                'name': 'Recipe Input 2',
                'type': 'property'
            }],
            'jobs': [{
                'name': 'Job A',
                'job_type': {
                    'name': job_a.job_type.name,
                    'version': job_a.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 1',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job B',
                'job_type': {
                    'name': job_b.job_type.name,
                    'version': job_b.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 2',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job D',
                'job_type': {
                    'name': new_job_type_d.name,
                    'version': new_job_type_d.version,
                },
                'dependencies': [{
                    'name': 'Job A',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }, {
                    'name': 'Job B',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 2',
                    }],
                }]
            }, {
                'name': 'Job E',
                'job_type': {
                    'name': job_e.job_type.name,
                    'version': job_e.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job D',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }]
            }, {
                'name': 'Job F',
                'job_type': {
                    'name': job_f.job_type.name,
                    'version': job_f.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job B',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }]
            }]
        }
        graph_b = OldRecipeDefinition(definition_b).get_graph()

        diff = RecipeGraphDelta(graph_a, graph_b)
        json = convert_diff_to_v6(diff)
        RecipeDiffV6(diff=json.get_dict(), do_validate=True)  # Revalidate
        self.assertTrue(json.get_dict()['can_be_reprocessed'])

    def test_convert_diff_to_v6_new_required_input(self):
        """Tests calling convert_diff_to_v6() with a diff containing a new required input that blocks reprocessing"""

        job_a = job_test_utils.create_job()

        definition_a = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }, {
                'name': 'Recipe Input 2',
                'type': 'property'
            }],
            'jobs': [{
                'name': 'Job A',
                'job_type': {
                    'name': job_a.job_type.name,
                    'version': job_a.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 1',
                    'job_input': 'Job Input 1',
                }]
            }]
        }
        graph_a = OldRecipeDefinition(definition_a).get_graph()

        definition_b = {
            'version': '1.0',
            'input_data': [{
                'name': 'New Recipe Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }, {
                'name': 'Recipe Input 2',
                'type': 'property'
            }],
            'jobs': [{
                'name': 'Job A',
                'job_type': {
                    'name': job_a.job_type.name,
                    'version': job_a.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'New Recipe Input 1',
                    'job_input': 'Job Input 1',
                }]
            }]
        }
        graph_b = OldRecipeDefinition(definition_b).get_graph()

        diff = RecipeGraphDelta(graph_a, graph_b)
        json = convert_diff_to_v6(diff)
        RecipeDiffV6(diff=json.get_dict(), do_validate=True)  # Revalidate
        self.assertFalse(json.get_dict()['can_be_reprocessed'])

    def test_convert_recipe_diff_to_v6_json_empty(self):
        """Tests calling convert_recipe_diff_to_v6_json() with an empty diff"""

        # Try diff with empty recipe definitions
        interface_a = Interface()
        interface_b = Interface()
        definition_a = RecipeDefinition(interface_a)
        definition_b = RecipeDefinition(interface_b)
        diff = RecipeDiff(definition_a, definition_b)
        json = convert_recipe_diff_to_v6_json(diff)
        RecipeDiffV6(diff=json.get_dict(), do_validate=True)  # Revalidate
        self.assertTrue(json.get_dict()['can_be_reprocessed'])

    def test_convert_recipe_diff_to_v6_json_with_changes(self):
        """Tests calling convert_recipe_diff_to_v6_json() with a diff containing a variety of changes"""

        interface_1 = Interface()
        interface_1.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_1.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2 = Interface()
        interface_2.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_2.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2.add_parameter(JsonParameter('json_param_2', 'object', required=False))

        definition_1 = RecipeDefinition(interface_1)
        definition_1.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_1.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_1.add_job_node('C', 'job_type_3', '1.0', 2)
        definition_1.add_recipe_node('D', 'recipe_type_1', 1)
        definition_1.add_job_node('E', 'job_type_4', '1.0', 1)
        definition_1.add_dependency('A', 'B')
        definition_1.add_dependency('A', 'C')
        definition_1.add_dependency('B', 'E')
        definition_1.add_dependency('C', 'D')
        definition_1.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_1.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_1.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_1.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_1.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')

        definition_2 = RecipeDefinition(interface_2)
        # Nodes B and E are deleted
        definition_2.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_2.add_job_node('C', 'job_type_3', '2.1', 1)  # Change to job type version and revision
        definition_2.add_recipe_node('D', 'recipe_type_1', 1)
        definition_2.add_recipe_node('F', 'recipe_type_2', 5)  # New node
        definition_2.add_dependency('A', 'C')
        definition_2.add_dependency('C', 'D')
        definition_2.add_dependency('D', 'F')
        definition_2.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_2.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_2.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_2.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')
        definition_2.add_recipe_input_connection('F', 'f_input_1', 'json_param_2')

        diff = RecipeDiff(definition_1, definition_2)
        json = convert_recipe_diff_to_v6_json(diff)
        RecipeDiffV6(diff=json.get_dict(), do_validate=True)  # Revalidate
        self.assertTrue(json.get_dict()['can_be_reprocessed'])

    def test_convert_recipe_diff_to_v6_json_new_required_input(self):
        """Tests calling convert_recipe_diff_to_v6_json() with a diff where there is a breaking recipe interface
        change
        """

        interface_1 = Interface()
        interface_1.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_1.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2 = Interface()
        interface_2.add_parameter(FileParameter('file_param_1', ['image/gif']))
        interface_2.add_parameter(JsonParameter('json_param_1', 'object'))
        interface_2.add_parameter(JsonParameter('json_param_2', 'object', required=True))

        definition_1 = RecipeDefinition(interface_1)
        definition_1.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_1.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_1.add_job_node('C', 'job_type_3', '1.0', 2)
        definition_1.add_recipe_node('D', 'recipe_type_1', 1)
        definition_1.add_dependency('A', 'B')
        definition_1.add_dependency('A', 'C')
        definition_1.add_dependency('C', 'D')
        definition_1.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_1.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_1.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_1.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_1.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')

        definition_2 = RecipeDefinition(interface_2)
        definition_2.add_job_node('A', 'job_type_1', '1.0', 1)
        definition_2.add_job_node('B', 'job_type_2', '2.0', 1)
        definition_2.add_job_node('C', 'job_type_3', '1.1', 1)  # Change to job type version and revision
        definition_2.add_recipe_node('D', 'recipe_type_1', 1)
        definition_2.add_dependency('A', 'B')
        definition_2.add_dependency('A', 'C')
        definition_2.add_dependency('C', 'D')
        definition_2.add_recipe_input_connection('A', 'input_1', 'file_param_1')
        definition_2.add_dependency_input_connection('B', 'b_input_1', 'A', 'a_output_1')
        definition_2.add_dependency_input_connection('C', 'c_input_1', 'A', 'a_output_2')
        definition_2.add_dependency_input_connection('D', 'd_input_1', 'C', 'c_output_1')
        definition_2.add_recipe_input_connection('D', 'd_input_2', 'json_param_1')

        diff = RecipeDiff(definition_1, definition_2)
        json = convert_recipe_diff_to_v6_json(diff)
        RecipeDiffV6(diff=json.get_dict(), do_validate=True)  # Revalidate
        self.assertFalse(json.get_dict()['can_be_reprocessed'])

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        RecipeDiffV6(do_validate=True)

        # Invalid version
        diff = {'version': 'BAD'}
        self.assertRaises(InvalidDiff, RecipeDiffV6, diff, True)
