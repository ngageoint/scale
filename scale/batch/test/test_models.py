from __future__ import unicode_literals

import datetime

import django
from django.test import TransactionTestCase

import batch.test.utils as batch_test_utils
import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from batch.exceptions import BatchError
from batch.models import Batch, BatchJob, BatchRecipe
from job.models import Job
from recipe.configuration.data.recipe_data import RecipeData
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from recipe.models import Recipe


class TestBatchManager(TransactionTestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.file = storage_test_utils.create_file()

        configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
            },
            'data': {
                'input_data_name': 'Recipe Input',
                'workspace_name': self.workspace.name,
            },
        }
        self.rule = trigger_test_utils.create_trigger_rule(configuration=configuration)
        self.event = trigger_test_utils.create_trigger_event(rule=self.rule)

        interface_1 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }],
        }
        self.job_type_1 = job_test_utils.create_job_type(interface=interface_1)

        self.definition_1 = {
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
                    'job_input': 'Test Input 1',
                }],
            }],
        }
        RecipeDefinition(self.definition_1).validate_job_interfaces()
        self.recipe_type = recipe_test_utils.create_recipe_type(definition=self.definition_1, trigger_rule=self.rule)

        self.interface_2 = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 2',
                'type': 'files',
                'media_types': ['image/tiff'],
            }],
            'output_data': [{
                'name': 'Test Output 2',
                'type': 'file',
            }],
        }
        self.job_type_2 = job_test_utils.create_job_type(interface=self.interface_2)
        self.definition_2 = {
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
                    'job_input': 'Test Input 1',
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
                        'output': 'Test Output 1',
                        'input': 'Test Input 2',
                    }],
                }],
            }],
        }

        self.data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file.id,
            }],
            'workspace_id': self.workspace.id,
        }

    def test_create_successful(self):
        """Tests calling BatchManager.create_batch() successfully"""

        batch = batch_test_utils.create_batch(self.recipe_type)

        batch = Batch.objects.get(pk=batch.id)
        self.assertIsNotNone(batch.title)
        self.assertIsNotNone(batch.description)
        self.assertEqual(batch.status, 'SUBMITTED')
        self.assertEqual(batch.recipe_type, self.recipe_type)

        jobs = Job.objects.filter(job_type__name='scale-batch-creator')
        self.assertEqual(len(jobs), 1)
        self.assertEqual(batch.creator_job.id, jobs[0].id)

    def test_schedule_no_changes(self):
        """Tests calling BatchManager.schedule_recipes() for a recipe type that has nothing to reprocess"""

        Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data), event=self.event)
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.total_count, 0)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 0)

    def test_schedule_new_batch(self):
        """Tests calling BatchManager.schedule_recipes() for a batch that has never been started"""
        handler = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data),
                                               event=self.event)
        recipe_test_utils.edit_recipe_type(self.recipe_type, self.definition_2)
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 1)
        self.assertEqual(batch_recipes[0].batch, batch)
        self.assertEqual(batch_recipes[0].recipe.recipe_type, self.recipe_type)
        self.assertEqual(batch_recipes[0].superseded_recipe, handler.recipe)

    def test_schedule_partial_batch(self):
        """Tests calling BatchManager.schedule_recipes() for a batch that is incomplete"""
        for i in range(5):
            Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data), event=self.event)
        partials = []
        for i in range(5):
            handler = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data),
                                                   event=self.event)
            handler.recipe.is_superseded = True
            handler.recipe.save()
            partials.append(handler.recipe)
        recipe_test_utils.edit_recipe_type(self.recipe_type, self.definition_2)
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.created_count, 5)
        self.assertEqual(batch.total_count, 5)

        for recipe in partials:
            recipe.is_superseded = False
            recipe.save()
        batch.status = 'SUBMITTED'
        batch.save()

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 10)
        self.assertEqual(batch.total_count, 10)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 10)

    def test_schedule_invalid_status(self):
        """Tests calling BatchManager.schedule_recipes() for a batch that was already created"""

        Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data), event=self.event)
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type)

        Batch.objects.schedule_recipes(batch.id)

        self.assertRaises(BatchError, Batch.objects.schedule_recipes, batch.id)

    def test_schedule_date_range_created(self):
        """Tests calling BatchManager.schedule_recipes() for a batch with a created date range restriction"""
        recipe1 = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data),
                                               event=self.event).recipe
        Recipe.objects.filter(pk=recipe1.id).update(created=datetime.datetime(2016, 1, 1))
        recipe2 = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data),
                                               event=self.event).recipe
        Recipe.objects.filter(pk=recipe2.id).update(created=datetime.datetime(2016, 2, 1))
        recipe3 = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data),
                                               event=self.event).recipe
        Recipe.objects.filter(pk=recipe3.id).update(created=datetime.datetime(2016, 3, 1))

        recipe_test_utils.edit_recipe_type(self.recipe_type, self.definition_2)

        definition = {
            'date_range': {
                'started': '2016-01-10',
                'ended': '2016-02-10',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 1)
        self.assertEqual(batch_recipes[0].superseded_recipe, recipe2)

    def test_schedule_date_range_data_none(self):
        """Tests calling BatchManager.schedule_recipes() for a batch data date range where no data matches"""
        Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data), event=self.event)

        recipe_test_utils.edit_recipe_type(self.recipe_type, self.definition_2)

        definition = {
            'date_range': {
                'type': 'data',
                'started': '2016-01-01',
                'ended': '2016-01-10',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 0)
        self.assertEqual(batch.total_count, 0)

    def test_schedule_date_range_data_started(self):
        """Tests calling BatchManager.schedule_recipes() for a batch with a data started date range restriction"""
        file1 = storage_test_utils.create_file()
        file1.data_started = datetime.datetime(2016, 1, 1)
        file1.save()
        data1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file1.id,
            }],
            'workspace_id': self.workspace.id,
        }
        Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(data1), event=self.event)

        file2 = storage_test_utils.create_file()
        file2.data_started = datetime.datetime(2016, 2, 1)
        file2.save()
        data2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file2.id,
            }],
            'workspace_id': self.workspace.id,
        }
        recipe2 = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(data2),
                                               event=self.event).recipe

        recipe_test_utils.edit_recipe_type(self.recipe_type, self.definition_2)

        definition = {
            'date_range': {
                'type': 'data',
                'started': '2016-01-10',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 1)
        self.assertEqual(batch_recipes[0].superseded_recipe, recipe2)

    def test_schedule_date_range_data_ended(self):
        """Tests calling BatchManager.schedule_recipes() for a batch with a data ended date range restriction"""
        file1 = storage_test_utils.create_file()
        file1.data_started = datetime.datetime(2016, 1, 1)
        file1.data_ended = datetime.datetime(2016, 1, 10)
        file1.save()
        data1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file1.id,
            }],
            'workspace_id': self.workspace.id,
        }
        recipe1 = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(data1),
                                               event=self.event).recipe

        file2 = storage_test_utils.create_file()
        file2.data_started = datetime.datetime(2016, 2, 1)
        file2.data_ended = datetime.datetime(2016, 2, 10)
        file2.save()
        data2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file2.id,
            }],
            'workspace_id': self.workspace.id,
        }
        Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(data2), event=self.event)

        recipe_test_utils.edit_recipe_type(self.recipe_type, self.definition_2)

        definition = {
            'date_range': {
                'type': 'data',
                'ended': '2016-01-15',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 1)
        self.assertEqual(batch_recipes[0].superseded_recipe, recipe1)

    def test_schedule_date_range_data_full(self):
        """Tests calling BatchManager.schedule_recipes() for a batch with a data date range restriction"""
        file1 = storage_test_utils.create_file()
        file1.data_started = datetime.datetime(2016, 1, 1)
        file1.save()
        data1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file1.id,
            }],
            'workspace_id': self.workspace.id,
        }
        Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(data1), event=self.event)

        file2 = storage_test_utils.create_file()
        file2.data_started = datetime.datetime(2016, 2, 1)
        file2.data_ended = datetime.datetime(2016, 2, 10)
        file2.save()
        data2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file2.id,
            }],
            'workspace_id': self.workspace.id,
        }
        recipe2 = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(data2),
                                               event=self.event).recipe

        file3 = storage_test_utils.create_file()
        file3.data_ended = datetime.datetime(2016, 3, 1)
        file3.save()
        data3 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file3.id,
            }],
            'workspace_id': self.workspace.id,
        }
        Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(data3), event=self.event)

        recipe_test_utils.edit_recipe_type(self.recipe_type, self.definition_2)

        definition = {
            'date_range': {
                'type': 'data',
                'started': '2016-02-01',
                'ended': '2016-02-10',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 1)
        self.assertEqual(batch_recipes[0].superseded_recipe, recipe2)

    def test_schedule_all_jobs(self):
        """Tests calling BatchManager.schedule_recipes() for a batch that forces all jobs to be re-processed"""
        handler = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data),
                                               event=self.event)

        definition = {
            'all_jobs': True,
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 1)
        self.assertEqual(batch_recipes[0].batch, batch)
        self.assertEqual(batch_recipes[0].recipe.recipe_type, self.recipe_type)
        self.assertEqual(batch_recipes[0].superseded_recipe, handler.recipe)

    def test_schedule_job_names(self):
        """Tests calling BatchManager.schedule_recipes() for a batch that forces all jobs to be re-processed"""
        handler = Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data),
                                               event=self.event)
        recipe_test_utils.edit_recipe_type(self.recipe_type, self.definition_2)

        definition = {
            'job_names': ['Job 1'],
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 1)
        self.assertEqual(batch_recipes[0].batch, batch)
        self.assertEqual(batch_recipes[0].recipe.recipe_type, self.recipe_type)
        self.assertEqual(batch_recipes[0].superseded_recipe, handler.recipe)

        batch_jobs = BatchJob.objects.all()
        self.assertEqual(len(batch_jobs), 2)
        for batch_job in batch_jobs:
            self.assertIn(batch_job.job.job_type, [self.job_type_1, self.job_type_2])

    def test_schedule_priority(self):
        """Tests calling BatchManager.schedule_recipes() for a batch that overrides job priority"""
        Recipe.objects.create_recipe(recipe_type=self.recipe_type, data=RecipeData(self.data), event=self.event)

        definition = {
            'all_jobs': True,
            'priority': 1111,
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

        batch_job = BatchJob.objects.get(batch=batch, job__job_type=self.job_type_1)
        self.assertEqual(batch_job.job.priority, 1111)
