from __future__ import unicode_literals

import django
from django.test import TestCase

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
from recipe.models import Recipe


class TestRecipeHandler(TestCase):

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
        self.recipe_type = recipe_test_utils.create_recipe_type(definition=self.definition)
        self.recipe = recipe_test_utils.create_recipe(recipe_type=self.recipe_type)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_failed', job=self.job_failed)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_completed', job=self.job_completed)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_running', job=self.job_running)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_queued', job=self.job_queued)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_canceled', job=self.job_canceled)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_fa_co_a', job=self.job_fa_co_a)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_fa_co_b', job=self.job_fa_co_b)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_co_ru_qu_a', job=self.job_co_ru_qu_a)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_co_ru_qu_b', job=self.job_co_ru_qu_b)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_qu_ca_a', job=self.job_qu_ca_a)
        recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='job_qu_ca_b', job=self.job_qu_ca_b)

    def test_get_blocked_jobs(self):
        """Tests calling RecipeHandler.get_blocked_jobs()"""

        handler = Recipe.objects.get_recipe_handlers_for_jobs([self.job_failed.id])[self.job_failed.id]
        blocked_jobs = handler.get_blocked_jobs()
        blocked_job_ids = set()
        for blocked_job in blocked_jobs:
            blocked_job_ids.add(blocked_job.id)

        self.assertSetEqual(blocked_job_ids, {self.job_fa_co_b.id, self.job_qu_ca_a.id, self.job_qu_ca_b.id})

    def test_get_existing_jobs_to_queue(self):
        """Tests calling RecipeHandler.get_existing_jobs_to_queue()"""

        input_name_1 = 'Test Input 1'
        output_name_1 = 'Test Output 1'
        interface_1 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': input_name_1,
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': output_name_1,
                'type': 'files',
                'media_type': 'image/png',
            }],
        }
        job_type_1 = job_test_utils.create_job_type(interface=interface_1)
        job_1 = job_test_utils.create_job(job_type=job_type_1)

        input_name_2 = 'Test Input 2'
        output_name_2 = 'Test Output 2'
        interface_2 = {
            'version': '1.0',
            'command': 'my_cmd',
            'command_arguments': 'args',
            'input_data': [{
                'name': input_name_2,
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': output_name_2,
                'type': 'file',
            }],
        }
        job_type_2 = job_test_utils.create_job_type(interface=interface_2)
        job_2 = job_test_utils.create_job(job_type=job_type_2)
        file_1 = storage_test_utils.create_file(media_type='text/plain')

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
                    'name': job_type_1.name,
                    'version': job_type_1.version,
                },
                'recipe_inputs': [{
                    'recipe_input': 'Recipe Input',
                    'job_input': input_name_1,
                }]
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': job_type_2.name,
                    'version': job_type_2.version,
                },
                'dependencies': [{
                    'name': 'Job 1',
                    'connections': [{
                        'output': output_name_1,
                        'input': input_name_2,
                    }],
                }],
            }],
        }
        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file_1.id,
            }],
            'workspace_id': 1,
        }
        recipe_type = recipe_test_utils.create_recipe_type(definition=definition)
        recipe = recipe_test_utils.create_recipe(recipe_type=recipe_type, data=data)
        recipe_test_utils.create_recipe_job(recipe=recipe, job_name='Job 1', job=job_1)
        recipe_test_utils.create_recipe_job(recipe=recipe, job_name='Job 2', job=job_2)

        handler = Recipe.objects.get_recipe_handlers_for_jobs([job_1.id])[job_1.id]
        jobs_to_queue = handler.get_existing_jobs_to_queue()

        # Make sure only Job 1 is returned and that its job data is correct
        self.assertEqual(len(jobs_to_queue), 1)
        self.assertEqual(jobs_to_queue[0][0].id, job_1.id)
        self.assertDictEqual(jobs_to_queue[0][1].get_dict(), {
            'version': '1.0',
            'input_data': [{
                'name': input_name_1,
                'file_id': file_1.id,
            }],
            'output_data': [{
                'name': output_name_1,
                'workspace_id': 1,
            }],
        })

    def test_get_pending_jobs(self):
        """Tests calling RecipeHandler.get_pending_jobs()"""

        handler = Recipe.objects.get_recipe_handlers_for_jobs([self.job_failed.id])[self.job_failed.id]
        pending_jobs = handler.get_pending_jobs()
        pending_job_ids = set()
        for pending_job in pending_jobs:
            pending_job_ids.add(pending_job.id)

        self.assertSetEqual(pending_job_ids, {self.job_co_ru_qu_a.id, self.job_co_ru_qu_b.id})
