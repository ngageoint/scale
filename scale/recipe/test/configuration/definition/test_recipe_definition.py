from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch

import job.test.utils as job_test_utils
import storage.test.utils as storage_test_utils
from job.configuration.data.data_file import AbstractDataFileStore
from job.configuration.results.job_results import JobResults
from job.models import Job
from recipe.configuration.data.exceptions import InvalidRecipeData
from recipe.configuration.data.recipe_data import LegacyRecipeData
from recipe.configuration.definition.exceptions import InvalidDefinition
from recipe.configuration.definition.recipe_definition import LegacyRecipeDefinition as RecipeDefinition


class DummyDataFileStore(AbstractDataFileStore):

    def get_workspaces(self, workspace_ids):
        results = {}
        if 1 in workspace_ids:
            results[long(1)] = True
        return results

    def store_files(self, files, input_file_ids, job_exe):
        pass


class TestRecipeDefinitionGetGraph(TestCase):

    def setUp(self):
        django.setup()

        self.input_name_1 = 'Test Input 1'
        self.output_name_1 = 'Test Output 1'
        interface_1 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': self.input_name_1,
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': self.output_name_1,
                'type': 'files',
                'media_type': 'image/png',
            }],
        }
        self.job_type_1 = job_test_utils.create_job_type(interface=interface_1)
        self.job_1 = job_test_utils.create_job(job_type=self.job_type_1)

        self.input_name_2 = 'Test Input 2'
        self.output_name_2 = 'Test Output 2'
        interface_2 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': self.input_name_2,
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': self.output_name_2,
                'type': 'file',
            }],
        }
        self.job_type_2 = job_test_utils.create_job_type(interface=interface_2)
        self.job_2 = job_test_utils.create_job(job_type=self.job_type_2)
        self.file_1 = storage_test_utils.create_file(media_type='text/plain')

    def test_successful(self):
        """Tests calling RecipeDefinition.get_graph() successfully"""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': self.input_name_1,
                }]
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type_2.name,
                    'version': self.job_type_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': self.output_name_1,
                        'input': self.input_name_2,
                    }],
                }],
            }],
        }

        recipe_definition = RecipeDefinition(definition)
        graph = recipe_definition.get_graph()

        self.assertEqual(len(graph.inputs), 1)
        self.assertEqual(len(graph._root_nodes), 1)
        self.assertEqual(len(graph._nodes), 2)


class TestRecipeDefinitionGetJobTypes(TestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()
        self.job_type2 = job_test_utils.create_job_type()

    def test_get_job_types_one(self):
        """Tests getting a job type from the definition."""
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_types()
        self.assertSetEqual(results, {self.job_type1})

    def test_get_job_types_multi(self):
        """Tests getting job types from the definition."""
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
            }],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_types()
        self.assertSetEqual(results, {self.job_type1, self.job_type2})

    def test_get_job_types_empty(self):
        """Tests getting job types when there are no jobs defined."""
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_types()
        self.assertSetEqual(results, set())

    def test_get_job_types_unique(self):
        """Tests getting job types without duplicates."""
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1a',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
            }, {
                'name': 'Job 1b',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_types()
        self.assertSetEqual(results, {self.job_type1, self.job_type2})


class TestRecipeDefinitionGetJobTypeKeys(TestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()
        self.job_type2 = job_test_utils.create_job_type()

    def test_get_job_type_keys_one(self):
        """Tests getting a job type key from the definition."""
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_type_keys()
        self.assertSetEqual(results, {(self.job_type1.name, self.job_type1.version)})

    def test_get_job_type_keys_multi(self):
        """Tests getting job type keys from the definition."""
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
            }],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_type_keys()
        self.assertSetEqual(results, {(self.job_type1.name, self.job_type1.version),
                                      (self.job_type2.name, self.job_type2.version)})

    def test_get_job_type_keys_empty(self):
        """Tests getting job type keys when there are no jobs defined."""
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_type_keys()
        self.assertSetEqual(results, set())

    def test_get_job_type_keys_unique(self):
        """Tests getting job type keys without duplicates."""
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1a',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
            }, {
                'name': 'Job 1b',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_type_keys()
        self.assertSetEqual(results, {(self.job_type1.name, self.job_type1.version),
                                      (self.job_type2.name, self.job_type2.version)})


class TestRecipeDefinitionGetJobTypeMap(TestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()
        self.job_type2 = job_test_utils.create_job_type()

    def test_successful_new_recipe(self):
        """Tests calling RecipeDefinition.get_job_type_map() successfully."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Input 1',
                }]
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Output 1',
                        'input': 'Input 2',
                    }]
                }]
            }]
        }
        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_type_map()
        self.assertDictEqual(results, {'Job 1': self.job_type1, 'Job 2': self.job_type2})


class TestRecipeDefinitionInit(TestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()
        self.job_type2 = job_test_utils.create_job_type()

    def test_init_bare_min(self):
        """Tests calling RecipeDefinition constructor with bare minimum JSON."""

        # No exception is success
        RecipeDefinition({'jobs': []})

    def test_init_bad_version(self):
        """Tests calling RecipeDefinition constructor with bad version number."""

        definition = {
            'version': 'BAD VERSION',
            'jobs': [],
        }
        self.assertRaises(InvalidDefinition, RecipeDefinition, definition)

    def test_init_undefined_recipe_input(self):
        """Tests calling RecipeDefinition constructor with an undefined recipe input."""

        definition = {
            'version': '1.0',
            'jobs': [{
                'name': 'myjob',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'NAME',
                    'job_input': 'input',
                }],
            }],
        }
        self.assertRaises(InvalidDefinition, RecipeDefinition, definition)

    def test_init_undefined_dependency(self):
        """Tests calling RecipeDefinition constructor with an undefined job dependency."""

        definition = {
            'version': '1.0',
            'jobs': [{
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                }],
            }],
        }
        self.assertRaises(InvalidDefinition, RecipeDefinition, definition)

    def test_init_dulicate_job_input(self):
        """Tests calling RecipeDefinition constructor with duplicate job inputs."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'property',
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Dup Input',
                }],
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Output 1',
                        'input': 'Dup Input',
                    }],
                }],
            }],
        }
        self.assertRaises(InvalidDefinition, RecipeDefinition, definition)

    def test_init_cyclic_dependency(self):
        """Tests calling RecipeDefinition constructor with a cyclic dependency."""

        job_type3 = job_test_utils.create_job_type()
        job_type4 = job_test_utils.create_job_type()

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'property',
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Input 1',
                }],
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Output 1',
                        'input': 'Input 2',
                    }],
                }, {
                    'name': 'Job 4',
                    'connections': [{
                         'output': 'Output 1',
                         'input': 'Input 2',
                     }],
                }],
            }, {
                'name': 'Job 3',
                'job_type': {
                    'name': job_type3.name,
                    'version': job_type3.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Output 1',
                        'input': 'Input 1',
                    }],
                }, {
                    'name': 'Job 2',
                    'connections': [{
                        'output': 'Output 1',
                        'input': 'Input 1',
                    }],
                }],
            }, {
                'name': 'Job 4',
                'job_type': {
                    'name': job_type4.name,
                    'version': job_type4.version,
                },
                'dependencies': [{
                    'name': 'Job 3',
                    'connections': [{
                        'output': 'Output 1',
                        'input': 'Input 1',
                    }],
                }],
            }],
        }
        self.assertRaises(InvalidDefinition, RecipeDefinition, definition)

    def test_init_successful(self):
        """Tests calling RecipeDefinition constructor successfully."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'property'
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Input 1',
                }],
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Output 1',
                        'input': 'Input 2',
                    }],
                }],
            }],
        }

        # No exception is success
        RecipeDefinition(definition)

    def test_init_input_data_name(self):
        """Tests calling RecipeDefinition constructor with good and bad input_data names."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'property',
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Input 1',
                }],
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Output 1',
                        'input': 'Input 2',
                    }],
                }],
            }],
        }

        good_names = ['foo', 'bar', 'name with spaces', 'name_with_undersores']
        bad_names = [
            'Speci@lCharacter', 'dont_use_bang!', 'dont.use.periods',
            'names_should_be_less_than_256_characters123456789012345678901234567890123456789012345678901234567890123456'
            '7890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012'
            '345678901234567890123456789012345678901234567890',
        ]

        for good_name in good_names:
            definition['input_data'][0]['name'] = good_name
            definition['jobs'][1]['recipe_inputs'][0]['recipe_input'] = good_name

            # No exception is success
            RecipeDefinition(definition)

        for bad_name in bad_names:
            definition['input_data'][0]['name'] = bad_name
            definition['jobs'][1]['recipe_inputs'][0]['recipe_input'] = bad_name

            # No exception is success
            self.assertRaises(InvalidDefinition, RecipeDefinition, definition)

    def test_init_job_name(self):
        """Tests calling RecipeDefinition constructor with good and bad job names."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'property',
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type1.name,
                    'version': self.job_type1.version,
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type2.name,
                    'version': self.job_type2.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': 'Input 1',
                }],
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': 'Output 1',
                        'input': 'Input 2',
                    }],
                }],
            }],
        }

        good_names = ['foo', 'bar', 'name with spaces', 'name_with_undersores']
        bad_names = [
            'Speci@lCharacter', 'dont_use_bang!', 'dont.use.periods',
            'names_should_be_less_than_256_characters123456789012345678901234567890123456789012345678901234567890123456'
            '7890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012'
            '345678901234567890123456789012345678901234567890',
        ]

        for good_name in good_names:
            definition['jobs'][0]['name'] = good_name
            definition['jobs'][1]['dependencies'][0]['name'] = good_name

            # No exception is success
            RecipeDefinition(definition)

        for bad_name in bad_names:
            definition['jobs'][1]['dependencies'][0]['name'] = bad_name

            # No exception is success
            self.assertRaises(InvalidDefinition, RecipeDefinition, definition)


class TestRecipeDefinitionValidateData(TestCase):

    def setUp(self):
        django.setup()

        self.input_name_1 = 'Test Input 1'
        self.output_name_1 = 'Test Output 1'
        interface_1 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': self.input_name_1,
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': self.output_name_1,
                'type': 'files',
                'media_type': 'image/png',
            }],
        }
        self.job_type_1 = job_test_utils.create_job_type(interface=interface_1)

        self.input_name_2 = 'Test Input 2'
        self.output_name_2 = 'Test Output 2'
        interface_2 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': self.input_name_2,
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': self.output_name_2,
                'type': 'file',
            }],
        }
        self.job_type_2 = job_test_utils.create_job_type(interface=interface_2)

        self.input_name_3 = 'Test Input 3'
        self.output_name_3 = 'Test Output 3'
        interface_3 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': self.input_name_3,
                'type': 'file',
                'media_types': ['text/plain'],
            }],
        }
        self.job_type_3 = job_test_utils.create_job_type(interface=interface_3)

        self.file_1 = storage_test_utils.create_file(media_type='text/plain')

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_missing_workspace(self, mock_store):
        """Tests calling RecipeDefinition.validate_data() with a missing required workspace."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': self.input_name_1,
                }],
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type_2.name,
                    'version': self.job_type_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': self.output_name_1,
                        'input': self.input_name_2,
                    }],
                }],
            }],
        }
        recipe = RecipeDefinition(definition)
        recipe.validate_job_interfaces()

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file_1.id,
            }],
        }
        recipe_data = LegacyRecipeData(data)

        self.assertRaises(InvalidRecipeData, recipe.validate_data, recipe_data)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful(self, mock_store):
        """Tests calling RecipeDefinition.validate_data() successfully."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': self.input_name_1,
                }],
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type_2.name,
                    'version': self.job_type_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': self.output_name_1,
                        'input': self.input_name_2,
                    }],
                }],
            }],
        }
        recipe = RecipeDefinition(definition)
        recipe.validate_job_interfaces()

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file_1.id,
            }],
            'workspace_id': 1,
        }
        recipe_data = LegacyRecipeData(data)

        # No exception is success
        recipe.validate_data(recipe_data)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful_no_workspace(self, mock_store):
        """Tests calling RecipeDefinition.validate_data() successfully with no workspace."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 3',
                'job_type': {
                    'name': self.job_type_3.name,
                    'version': self.job_type_3.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': self.input_name_3,
                }],
            }],
        }
        recipe = RecipeDefinition(definition)
        recipe.validate_job_interfaces()

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file_1.id,
            }],
        }
        recipe_data = LegacyRecipeData(data)

        # No exception is success
        recipe.validate_data(recipe_data)


class TestRecipeDefinitionValidateJobInterfaces(TestCase):

    def setUp(self):
        django.setup()

        self.input_name_1 = 'Test Input 1'
        self.output_name_1 = 'Test Output 1'

        interface_1 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': self.input_name_1,
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': self.output_name_1,
                'type': 'files',
                'media_type': 'image/png',
            }],
        }
        self.job_type_1 = job_test_utils.create_job_type(interface=interface_1)

        self.input_name_2 = 'Test Input 2'
        self.output_name_2 = 'Test Output 2'

        interface_2 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': self.input_name_2,
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': self.output_name_2,
                'type': 'file',
            }],
        }
        self.job_type_2 = job_test_utils.create_job_type(interface=interface_2)

    def test_invalid_job_type(self):
        """Tests calling RecipeDefinition.validate_job_interfaces() with an invalid job type."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'property',
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': 'BAD',
                    'version': 'BAD',
                },
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': 'invalid-job-type-name',
                    'version': 'invalid-job-type-version',
                },
            }],
        }
        recipe = RecipeDefinition(definition)

        self.assertRaises(InvalidDefinition, recipe.validate_job_interfaces)

    def test_successful(self):
        """Tests calling RecipeDefinition.validate_job_interfaces() successfully."""

        definition = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_type_1.name,
                    'version': self.job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': self.input_name_1,
                }],
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_type_2.name,
                    'version': self.job_type_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': self.output_name_1,
                        'input': self.input_name_2,
                    }],
                }],
            }],
        }
        recipe = RecipeDefinition(definition)

        # No exception is success
        recipe.validate_job_interfaces()
