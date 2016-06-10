from __future__ import unicode_literals

import django
from django.test import TestCase

from job.test import utils as job_test_utils
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from recipe.handlers.graph_delta import RecipeGraphDelta


class TestRecipeGraphDelta(TestCase):

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

    def test_init_identical(self):
        """Tests creating a RecipeGraphDelta between two identical graphs"""

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
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_a.job_type.name,
                    'version': self.job_a.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 1',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_b.job_type.name,
                    'version': self.job_b.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 2',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job 3',
                'job_type': {
                    'name': self.job_c.job_type.name,
                    'version': self.job_c.job_type.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input 2',
                    'job_input': 'Job Input 1',
                }]
            }, {
                'name': 'Job 4',
                'job_type': {
                    'name': self.job_d.job_type.name,
                    'version': self.job_d.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }, {
                    'name': 'Job 2',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 2',
                    }],
                }]
            }, {
                'name': 'Job 5',
                'job_type': {
                    'name': self.job_e.job_type.name,
                    'version': self.job_e.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job 2',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }]
            }, {
                'name': 'Job 6',
                'job_type': {
                    'name': self.job_f.job_type.name,
                    'version': self.job_f.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job 4',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }]
            }, {
                'name': 'Job 7',
                'job_type': {
                    'name': self.job_g.job_type.name,
                    'version': self.job_g.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job 4',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }, {
                    'name': 'Job 5',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 2',
                    }],
                }]
            }, {
                'name': 'Job 8',
                'job_type': {
                    'name': self.job_h.job_type.name,
                    'version': self.job_h.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job 3',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 1',
                    }],
                }, {
                    'name': 'Job 4',
                    'connections': [{
                        'output': 'Job Output 1',
                        'input': 'Job Input 2',
                    }],
                }]
            }]
        }
        graph_b = RecipeDefinition(definition_b).get_graph()

        delta = RecipeGraphDelta(graph_a, graph_b)

        expected_results = {'Job 1': 'Job A', 'Job 2': 'Job B', 'Job 3': 'Job C', 'Job 4': 'Job D', 'Job 5': 'Job E',
                            'Job 6': 'Job F', 'Job 7': 'Job G', 'Job 8': 'Job H'}
        self.assertDictEqual(delta.get_identical_nodes(), expected_results)
