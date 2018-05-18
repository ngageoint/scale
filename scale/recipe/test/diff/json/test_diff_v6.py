from __future__ import unicode_literals

import django
from django.test import TestCase

from job.models import JobType
from job.test import utils as job_test_utils
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from recipe.diff.exceptions import InvalidDiff
from recipe.diff.json.diff_v6 import convert_diff_to_v6, RecipeDiffV6
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
        graph_a = RecipeDefinition(definition_a).get_graph()

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
        graph_b = RecipeDefinition(definition_b).get_graph()

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
        graph_a = RecipeDefinition(definition_a).get_graph()

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
        graph_b = RecipeDefinition(definition_b).get_graph()

        diff = RecipeGraphDelta(graph_a, graph_b)
        json = convert_diff_to_v6(diff)
        RecipeDiffV6(diff=json.get_dict(), do_validate=True)  # Revalidate
        self.assertFalse(json.get_dict()['can_be_reprocessed'])

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        RecipeDiffV6(do_validate=True)

        # Invalid version
        diff = {'version': 'BAD'}
        self.assertRaises(InvalidDiff, RecipeDiffV6, diff, True)
