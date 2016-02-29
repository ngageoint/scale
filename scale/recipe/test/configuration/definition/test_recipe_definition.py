#@PydevCodeAnalysisIgnore
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
from recipe.configuration.data.recipe_data import RecipeData
from recipe.configuration.definition.exceptions import InvalidDefinition
from recipe.configuration.definition.recipe_definition import RecipeDefinition


class DummyDataFileStore(AbstractDataFileStore):

    def get_workspaces(self, workspace_ids):
        results = {}
        if 1 in workspace_ids:
            results[long(1)] = True
        return results

    def store_files(self, files, input_file_ids, job_exe):
        pass


class TestRecipeDefinitionGetJobTypes(TestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()
        self.job_type2 = job_test_utils.create_job_type()

    def test_get_job_types_one(self):
        '''Tests getting a job type from the definition.'''
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
        '''Tests getting job types from the definition.'''
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
        '''Tests getting job types when there are no jobs defined.'''
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_types()
        self.assertSetEqual(results, set())

    def test_get_job_types_unique(self):
        '''Tests getting job types without duplicates.'''
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
        '''Tests getting a job type key from the definition.'''
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
        '''Tests getting job type keys from the definition.'''
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
        '''Tests getting job type keys when there are no jobs defined.'''
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [],
        }

        recipe_definition = RecipeDefinition(definition)

        results = recipe_definition.get_job_type_keys()
        self.assertSetEqual(results, set())

    def test_get_job_type_keys_unique(self):
        '''Tests getting job type keys without duplicates.'''
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
        '''Tests calling RecipeDefinition.get_job_type_map() successfully.'''

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


class TestRecipeDefinitionGetNextJobsToQueue(TestCase):

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

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful_new_recipe(self, mock_store):
        '''Tests calling RecipeDefinition.get_next_jobs_to_queue() successfully when a new recipe is being created.'''

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
        recipe_definition.validate_job_interfaces()

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file_1.id,
            }],
            'workspace_id': 1,
        }
        recipe_data = RecipeData(data)
        recipe_definition.validate_data(recipe_data)

        job_1 = Job.objects.select_related('job_type').get(pk=self.job_1.id)
        job_2 = Job.objects.select_related('job_type').get(pk=self.job_2.id)

        results = recipe_definition.get_next_jobs_to_queue(recipe_data, {'Job 1': job_1, 'Job 2': job_2}, {})

        # Make sure only Job 1 is returned and that its job data is correct
        self.assertListEqual([self.job_1.id], results.keys())
        self.assertDictEqual(results[self.job_1.id].get_dict(), {
            'version': '1.0',
            'input_data': [{
                'name': self.input_name_1,
                'file_id': self.file_1.id,
            }],
            'output_data': [{
                'name': self.output_name_1,
                'workspace_id': 1,
            }],
        })

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful_job_1_completed(self, mock_store):
        '''Tests calling RecipeDefinition.get_next_jobs_to_queue() successfully when job 1 has been completed.'''

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
        recipe_definition.validate_job_interfaces()

        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file_1.id,
            }],
            'workspace_id': 1,
        }
        recipe_data = RecipeData(data)
        recipe_definition.validate_data(recipe_data)

        png_file_ids = [98, 99, 100]
        job_results = JobResults()
        job_results.add_file_list_parameter(self.output_name_1, png_file_ids)
        job_1 = Job.objects.select_related('job_type').get(pk=self.job_1.id)
        job_1.results = job_results.get_dict()
        job_1.save()
        job_2 = Job.objects.select_related('job_type').get(pk=self.job_2.id)

        results = recipe_definition.get_next_jobs_to_queue(recipe_data, {'Job 2': job_2}, {'Job 1': job_1})

        # Make sure only Job 2 is returned and that its job data is correct
        self.assertListEqual([self.job_2.id], results.keys())
        self.assertDictEqual(results[self.job_2.id].get_dict(), {
            'version': '1.0',
            'input_data': [{
                'name': self.input_name_2,
                'file_ids': png_file_ids,
            }],
            'output_data': [{
                'name': self.output_name_2,
                'workspace_id': 1,
            }],
        })


class TestRecipeDefinitionGetUnqueuedJobStatuses(TestCase):

    def setUp(self):
        django.setup()

        self.job_failed = job_test_utils.create_job(status='FAILED')
        self.job_completed = job_test_utils.create_job(status='COMPLETED')
        self.job_running = job_test_utils.create_job(status='RUNNING')
        self.job_queued = job_test_utils.create_job(status='QUEUED')
        self.job_canceled = job_test_utils.create_job(status='CANCELED')

        self.job_fa_co_a = job_test_utils.create_job(status='BLOCKED')
        self.job_fa_co_b = job_test_utils.create_job(status='PENDING')

        self.job_co_ru_qu_a = job_test_utils.create_job(status='BLOCKED')
        self.job_co_ru_qu_b = job_test_utils.create_job(status='BLOCKED')

        self.job_qu_ca_a = job_test_utils.create_job(status='PENDING')
        self.job_qu_ca_b = job_test_utils.create_job(status='PENDING')

        self.definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'job_failed',
                'job_type': {
                    'name': self.job_failed.job_type.name,
                    'version': self.job_failed.job_type.version,
                },
            }, {
                'name': 'job_completed',
                'job_type': {
                    'name': self.job_completed.job_type.name,
                    'version': self.job_completed.job_type.version,
                },
            }, {
                'name': 'job_running',
                'job_type': {
                    'name': self.job_running.job_type.name,
                    'version': self.job_running.job_type.version,
                },
            }, {
                'name': 'job_queued',
                'job_type': {
                    'name': self.job_queued.job_type.name,
                    'version': self.job_queued.job_type.version,
                },
            }, {
                'name': 'job_canceled',
                'job_type': {
                    'name': self.job_canceled.job_type.name,
                    'version': self.job_canceled.job_type.version,
                },
            }, {
                'name': 'job_fa_co_a',
                'job_type': {
                    'name': self.job_fa_co_a.job_type.name,
                    'version': self.job_fa_co_a.job_type.version,
                },
                'dependencies': [{
                    'name': 'job_failed',
                }, {
                    'name': 'job_completed',
                }],
            }, {
               'name': 'job_fa_co_b',
               'job_type': {
                   'name': self.job_fa_co_b.job_type.name,
                   'version': self.job_fa_co_b.job_type.version,
               },
               'dependencies': [{
                   'name': 'job_fa_co_a',
               }],
            }, {
                'name': 'job_co_ru_qu_a',
                'job_type': {
                    'name': self.job_co_ru_qu_a.job_type.name,
                    'version': self.job_co_ru_qu_a.job_type.version,
                },
                'dependencies': [{
                    'name': 'job_completed',
                }, {
                    'name': 'job_running',
                }, {
                    'name': 'job_queued',
                }],
            }, {
                'name': 'job_co_ru_qu_b',
                'job_type': {
                    'name': self.job_co_ru_qu_b.job_type.name,
                    'version': self.job_co_ru_qu_b.job_type.version,
                },
                'dependencies': [{
                    'name': 'job_co_ru_qu_a',
                }],
            }, {
                'name': 'job_qu_ca_a',
                'job_type': {
                    'name': self.job_qu_ca_a.job_type.name,
                    'version': self.job_qu_ca_a.job_type.version,
                },
                'dependencies': [{
                    'name': 'job_queued',
                }, {
                    'name': 'job_canceled',
                }],
            }, {
                'name': 'job_qu_ca_b',
                'job_type': {
                    'name': self.job_qu_ca_b.job_type.name,
                    'version': self.job_qu_ca_b.job_type.version,
                },
                'dependencies': [{
                    'name': 'job_qu_ca_a',
                }],
            }],
        }

    def test_successful(self):
        '''Tests calling RecipeDefinition.get_unqueued_job_statuses() successfully.'''

        recipe_definition = RecipeDefinition(self.definition)
        recipe_definition.validate_job_interfaces()

        recipe_jobs = {
            'job_failed': self.job_failed,
            'job_completed': self.job_completed,
            'job_running': self.job_running,
            'job_queued': self.job_queued,
            'job_canceled': self.job_canceled,
            'job_fa_co_a': self.job_fa_co_a,
            'job_fa_co_b': self.job_fa_co_b,
            'job_co_ru_qu_a': self.job_co_ru_qu_a,
            'job_co_ru_qu_b': self.job_co_ru_qu_b,
            'job_qu_ca_a': self.job_qu_ca_a,
            'job_qu_ca_b': self.job_qu_ca_b,
        }
        results = recipe_definition.get_unqueued_job_statuses(recipe_jobs)

        expected_results = {
            self.job_fa_co_a.id: 'BLOCKED',
            self.job_fa_co_b.id: 'BLOCKED',
            self.job_co_ru_qu_a.id: 'PENDING',
            self.job_co_ru_qu_b.id: 'PENDING',
            self.job_qu_ca_a.id: 'BLOCKED',
            self.job_qu_ca_b.id: 'BLOCKED',
        }

        self.assertDictEqual(results, expected_results)


class TestRecipeDefinitionInit(TestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type()
        self.job_type2 = job_test_utils.create_job_type()

    def test_init_bare_min(self):
        '''Tests calling RecipeDefinition constructor with bare minimum JSON.'''

        # No exception is success
        RecipeDefinition({'jobs': []})

    def test_init_bad_version(self):
        '''Tests calling RecipeDefinition constructor with bad version number.'''

        definition = {
            'version': 'BAD VERSION',
            'jobs': [],
        }
        self.assertRaises(InvalidDefinition, RecipeDefinition, definition)

    def test_init_undefined_recipe_input(self):
        '''Tests calling RecipeDefinition constructor with an undefined recipe input.'''

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
        '''Tests calling RecipeDefinition constructor with an undefined job dependency.'''

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
        '''Tests calling RecipeDefinition constructor with duplicate job inputs.'''

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
        '''Tests calling RecipeDefinition constructor with a cyclic dependency.'''

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
        '''Tests calling RecipeDefinition constructor successfully.'''

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
        '''Tests calling RecipeDefinition constructor with good and bad input_data names.'''

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
        '''Tests calling RecipeDefinition constructor with good and bad job names.'''

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
        '''Tests calling RecipeDefinition.validate_data() with a missing required workspace.'''

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
        recipe_data = RecipeData(data)

        self.assertRaises(InvalidRecipeData, recipe.validate_data, recipe_data)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful(self, mock_store):
        '''Tests calling RecipeDefinition.validate_data() successfully.'''

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
        recipe_data = RecipeData(data)

        # No exception is success
        recipe.validate_data(recipe_data)

    @patch('recipe.configuration.data.recipe_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful_no_workspace(self, mock_store):
        '''Tests calling RecipeDefinition.validate_data() successfully with no workspace.'''

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
        recipe_data = RecipeData(data)

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
        '''Tests calling RecipeDefinition.validate_job_interfaces() with an invalid job type.'''

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
        '''Tests calling RecipeDefinition.validate_job_interfaces() successfully.'''

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
