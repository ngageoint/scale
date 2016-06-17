from __future__ import unicode_literals

import django
from django.test import TestCase

from job.test import utils as job_test_utils
from recipe.configuration.definition.recipe_definition import RecipeDefinition


class TestRecipeGraph(TestCase):

    def setUp(self):
        django.setup()

        self.job_a = job_test_utils.create_job()
        self.job_b = job_test_utils.create_job()
        self.job_c = job_test_utils.create_job()
        self.job_d = job_test_utils.create_job()
        self.job_e = job_test_utils.create_job()
        self.job_f = job_test_utils.create_job()
        self.job_g = job_test_utils.create_job()
        self.job_h = job_test_utils.create_job()

        definition = {
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
                    'name': self.job_a.job_type.name,
                    'version': self.job_a.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 1',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job B',
                'job_type': {
                    'name': self.job_b.job_type.name,
                    'version': self.job_b.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 2',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job C',
                'job_type': {
                    'name': self.job_c.job_type.name,
                    'version': self.job_c.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 2',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job D',
                'job_type': {
                    'name': self.job_d.job_type.name,
                    'version': self.job_d.job_type.version,
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
                    'name': self.job_e.job_type.name,
                    'version': self.job_e.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job B',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }]
            }, {
                'name': 'Job F',
                'job_type': {
                    'name': self.job_f.job_type.name,
                    'version': self.job_f.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job D',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }]
            }, {
                'name': 'Job G',
                'job_type': {
                    'name': self.job_g.job_type.name,
                    'version': self.job_g.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job D',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }, {
                    'name': 'Job E',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 2',
                    }],
                }]
            }, {
                'name': 'Job H',
                'job_type': {
                    'name': self.job_h.job_type.name,
                    'version': self.job_h.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job C',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }, {
                    'name': 'Job D',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 2',
                    }],
                }]
            }]
        }

        recipe_definition = RecipeDefinition(definition)
        self.graph = recipe_definition.get_graph()

    def test_get_topological_order(self):
        """Tests calling RecipeGraph.get_topological_order() successfully"""

        order = self.graph.get_topological_order()

        # Note: There are multiple valid topological orderings so a code change could cause this test to fail even if
        # get_topological_order() is still correct
        valid_order = ['Job C', 'Job B', 'Job A', 'Job E', 'Job D', 'Job G', 'Job F', 'Job H']

        self.assertListEqual(order, valid_order)
