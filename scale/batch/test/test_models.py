from __future__ import unicode_literals

import datetime

import django
from django.test import TransactionTestCase
from django.utils.timezone import utc
from mock import patch

import batch.test.utils as batch_test_utils
import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from batch.exceptions import BatchError
from batch.models import Batch, BatchRecipe
from data.data.json.data_v6 import DataV6
from job.models import Job
from recipe.models import Recipe, RecipeInputFile, RecipeTypeRevision


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
        self.event = trigger_test_utils.create_trigger_event(trigger_type='BATCH')

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


        manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'test-job',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': 'My first job',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 3600,
                'interface': {
                    'command': 'my_command args',
                    'inputs': {
                        'files': [{
                            'name': 'TEST_INPUT_1',
                            'type': 'file',
                            'media_types': ['text/plain'],
                        }]
                    },
                    'outputs': {
                        'files': [{
                            'name': 'TEST_OUTPUT_1',
                            'type': 'files',
                            'media_type': 'image/png',
                        }],
                    }
                }
            }
        }
        self.seed_job_type = job_test_utils.create_seed_job_type(manifest=manifest)

        self.definition_v6 = {
            'version': '6',
            'input': {'files':[{'name': 'TEST_INPUT_1', 'media_types': ['text/plain'],
                                'required': False, 'multiple': False}],
                     'json':[]},
            'nodes': {
                'job-a': {
                    'dependencies':[],
                    'input': {'TEST_INPUT_1': {'type': 'recipe', 'input': 'TEST_INPUT_1'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.seed_job_type.name,
                        'job_type_version': self.seed_job_type.version,
                        'job_type_revision': self.seed_job_type.revision_num,
                    }
                }
            }
        }

        self.recipe_type_v6 = recipe_test_utils.create_recipe_type_v6(definition=self.definition_v6)
        self.recipe_type_rev_v6 = RecipeTypeRevision.objects.get(recipe_type_id=self.recipe_type_v6.id)

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

        self.data_dict = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': self.file.id,
            }],
            'workspace_id': self.workspace.id,
        }

        self.input_data = DataV6(self.data_dict, do_validate=False).get_data()

    def test_create_successful(self):
        """Tests calling BatchManager.create_batch() successfully"""

        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6)

        batch = Batch.objects.get(pk=batch.id)
        self.assertIsNotNone(batch.title)
        self.assertIsNotNone(batch.description)
        self.assertEqual(batch.status, 'SUBMITTED')
        self.assertEqual(batch.recipe_type, self.recipe_type_v6)

        jobs = Job.objects.filter(job_type__name='scale-batch-creator')

        # Fails here?
        self.assertEqual(len(jobs), 1)
        self.assertEqual(batch.creator_job.id, jobs[0].id)

    def test_schedule_no_changes(self):
        """Tests calling BatchManager.schedule_recipes() for a recipe type that has nothing to reprocess"""

        recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
        recipe.save()
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.total_count, 0)

        batch_recipes = BatchRecipe.objects.all()
        self.assertEqual(len(batch_recipes), 0)

    @patch('batch.models.CommandMessageManager')
    def test_schedule_new_batch(self, mock_msg_mgr):
        """Tests calling BatchManager.schedule_recipes() for a batch that has never been started"""

        recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
        recipe.save()
        recipe_test_utils.edit_recipe_type_v6(recipe_type=self.recipe_type_v6, definition=self.definition_2)
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

    @patch('batch.models.CommandMessageManager')
    @patch('recipe.messages.update_recipe_definition.create_sub_update_recipe_definition_message')
    def test_schedule_partial_batch(self, mock_create, mock_msg_mgr):
        """Tests calling BatchManager.schedule_recipes() for a batch that is incomplete"""

        for i in range(5):
            recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
            recipe.save()
        partials = []
        for i in range(5):
            recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
            recipe.is_superseded = True
            recipe.save()
            partials.append(recipe)
        recipe_test_utils.edit_recipe_type_v6(recipe_type=self.recipe_type_v6, definition=self.definition_2)
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6)

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

    def test_schedule_invalid_status(self):
        """Tests calling BatchManager.schedule_recipes() for a batch that was already created"""

        recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
        recipe.save()
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6)

        Batch.objects.schedule_recipes(batch.id)

        self.assertRaises(BatchError, Batch.objects.schedule_recipes, batch.id)

    @patch('batch.models.CommandMessageManager')
    def test_schedule_date_range_created(self, mock_msg_mgr):
        """Tests calling BatchManager.schedule_recipes() for a batch with a created date range restriction"""

        recipe1 = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
        recipe1.save()
        Recipe.objects.filter(pk=recipe1.id).update(created=datetime.datetime(2016, 1, 1, tzinfo=utc))
        recipe2 = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
        recipe2.save()
        Recipe.objects.filter(pk=recipe2.id).update(created=datetime.datetime(2016, 2, 1, tzinfo=utc))
        recipe3 = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
        recipe3.save()
        Recipe.objects.filter(pk=recipe3.id).update(created=datetime.datetime(2016, 3, 1, tzinfo=utc))

        recipe_test_utils.edit_recipe_type_v6(recipe_type=self.recipe_type, definition=self.definition_2)

        definition = {
            'date_range': {
                'started': '2016-01-10T00:00:00.000Z',
                'ended': '2016-02-10T00:00:00.000Z',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

    def test_schedule_date_range_data_none(self):
        """Tests calling BatchManager.schedule_recipes() for a batch data date range where no data matches"""

        recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
        recipe.save()

        recipe_test_utils.edit_recipe_type_v6(recipe_type=self.recipe_type_v6, definition=self.definition_2)

        definition = {
            'date_range': {
                'type': 'data',
                'started': '2016-01-01T00:00:00.000Z',
                'ended': '2016-01-10T00:00:00.000Z',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 0)
        self.assertEqual(batch.total_count, 0)

    @patch('batch.models.CommandMessageManager')
    def test_schedule_date_range_data_started(self, mock_msg_mgr):
        """Tests calling BatchManager.schedule_recipes() for a batch with a data started date range restriction"""

        file1 = storage_test_utils.create_file()
        file1.data_started = datetime.datetime(2016, 1, 1, tzinfo=utc)
        file1.save()
        data1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file1.id,
            }],
            'workspace_id': self.workspace.id,
        }
        input_data_1 = DataV6(data1).get_data()
        recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=input_data_1)
        recipe.save()
        recipe_file_1 = RecipeInputFile()
        recipe_file_1.recipe_id = recipe.id
        recipe_file_1.input_file_id = file1.id
        recipe_file_1.recipe_input = 'Recipe Input'
        recipe_file_1.created = recipe.created
        recipe_file_1.save()

        file2 = storage_test_utils.create_file()
        file2.data_started = datetime.datetime(2016, 2, 1, tzinfo=utc)
        file2.save()
        data2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file2.id,
            }],
            'workspace_id': self.workspace.id,
        }
        input_data_2 = DataV6(data2).get_data()
        recipe2 = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=input_data_2)
        recipe2.save()
        recipe_file_2 = RecipeInputFile()
        recipe_file_2.recipe_id = recipe2.id
        recipe_file_2.input_file_id = file2.id
        recipe_file_2.recipe_input = 'Recipe Input'
        recipe_file_2.created = recipe2.created
        recipe_file_2.save()

        recipe_test_utils.edit_recipe_type_v6(recipe_type=self.recipe_type_v6, definition=self.definition_2)

        definition = {
            'date_range': {
                'type': 'data',
                'started': '2016-01-10T00:00:00.000Z',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

    @patch('batch.models.CommandMessageManager')
    def test_schedule_date_range_data_ended(self, mock_msg_mgr):
        """Tests calling BatchManager.schedule_recipes() for a batch with a data ended date range restriction"""

        file1 = storage_test_utils.create_file()
        file1.data_started = datetime.datetime(2016, 1, 1, tzinfo=utc)
        file1.data_ended = datetime.datetime(2016, 1, 10, tzinfo=utc)
        file1.save()
        data1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file1.id,
            }],
            'workspace_id': self.workspace.id,
        }
        input_data_1 = DataV6(data1).get_data()
        recipe1 = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=input_data_1)
        recipe1.save()
        recipe_file_1 = RecipeInputFile()
        recipe_file_1.recipe_id = recipe1.id
        recipe_file_1.input_file_id = file1.id
        recipe_file_1.recipe_input = 'Recipe Input'
        recipe_file_1.created = recipe1.created
        recipe_file_1.save()

        file2 = storage_test_utils.create_file()
        file2.data_started = datetime.datetime(2016, 2, 1, tzinfo=utc)
        file2.data_ended = datetime.datetime(2016, 2, 10, tzinfo=utc)
        file2.save()
        data2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file2.id,
            }],
            'workspace_id': self.workspace.id,
        }
        input_data_2 = DataV6(data2).get_data()
        recipe2 = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=input_data_2)
        recipe2.save()
        recipe_file_2 = RecipeInputFile()
        recipe_file_2.recipe_id = recipe2.id
        recipe_file_2.input_file_id = file2.id
        recipe_file_2.recipe_input = 'Recipe Input'
        recipe_file_2.created = recipe2.created
        recipe_file_2.save()

        recipe_test_utils.edit_recipe_type_v6(recipe_type=self.recipe_type_v6, definition=self.definition_2)

        definition = {
            'date_range': {
                'type': 'data',
                'ended': '2016-01-15T00:00:00.000Z',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

    @patch('batch.models.CommandMessageManager')
    def test_schedule_date_range_data_full(self, mock_msg_mgr):
        """Tests calling BatchManager.schedule_recipes() for a batch with a data date range restriction"""
        file1 = storage_test_utils.create_file()
        file1.data_started = datetime.datetime(2016, 1, 1, tzinfo=utc)
        file1.save()
        data1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file1.id,
            }],
            'workspace_id': self.workspace.id,
        }
        input_data_1 = DataV6(data1).get_data()
        recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=input_data_1)
        recipe.save()
        recipe_file_1 = RecipeInputFile()
        recipe_file_1.recipe_id = recipe.id
        recipe_file_1.input_file_id = file1.id
        recipe_file_1.recipe_input = 'Recipe Input'
        recipe_file_1.created = recipe.created
        recipe_file_1.save()

        file2 = storage_test_utils.create_file()
        file2.data_started = datetime.datetime(2016, 2, 1, tzinfo=utc)
        file2.data_ended = datetime.datetime(2016, 2, 10, tzinfo=utc)
        file2.save()
        data2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file2.id,
            }],
            'workspace_id': self.workspace.id,
        }
        input_data_2 = DataV6(data2).get_data()
        recipe2 = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=input_data_2)
        recipe2.save()
        recipe_file_2 = RecipeInputFile()
        recipe_file_2.recipe_id = recipe2.id
        recipe_file_2.input_file_id = file2.id
        recipe_file_2.recipe_input = 'Recipe Input'
        recipe_file_2.created = recipe2.created
        recipe_file_2.save()

        file3 = storage_test_utils.create_file()
        file3.data_ended = datetime.datetime(2016, 3, 1, tzinfo=utc)
        file3.save()
        data3 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Recipe Input',
                'file_id': file3.id,
            }],
            'workspace_id': self.workspace.id,
        }
        input_data_3 = DataV6(data3).get_data()
        recipe3 = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=input_data_3)
        recipe3.save()

        recipe_test_utils.edit_recipe_type_v6(recipe_type=self.recipe_type_v6, definition=self.definition_2)

        definition = {
            'date_range': {
                'type': 'data',
                'started': '2016-02-01T00:00:00.000Z',
                'ended': '2016-02-10T00:00:00.000Z',
            },
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

    @patch('batch.models.CommandMessageManager')
    def test_schedule_all_jobs(self, mock_msg_mgr):
        """Tests calling BatchManager.schedule_recipes() for a batch that forces all jobs to be re-processed"""

        recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
        recipe.save()

        definition_json = {
            'all_jobs': True,
        }
        definition = BatchDefinition(definition_json)
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

    @patch('batch.models.CommandMessageManager')
    def test_schedule_job_names(self, mock_msg_mgr):
        """Tests calling BatchManager.schedule_recipes() for a batch that forces all jobs to be re-processed"""

        recipe = Recipe.objects.create_recipe_v6(self.recipe_type_rev_v6, self.event.id, input_data=self.input_data)
        recipe.save()
        recipe_test_utils.edit_recipe_type_v6(recipe_type=self.recipe_type_v6, definition=self.definition_2)

        definition = {
            'job_names': ['Job 1'],
        }
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.created_count, 1)
        self.assertEqual(batch.total_count, 1)

    def test_schedule_trigger_rule_true(self):
        """Tests calling BatchManager.schedule_recipes() using the default trigger rule of a recipe type."""

        # Make sure trigger condition skips mismatched media types
        storage_test_utils.create_file(media_type='text/ignore')

        definition = {
            'trigger_rule': True,
        }

        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.total_count, 1)

        self.assertEqual(batch.created_count, 1)
        recipe = Recipe.objects.get(batch_id=batch.id)
        self.assertEqual(recipe.batch, batch)
        self.assertEqual(recipe.recipe_type, self.recipe_type_v6)
        self.assertIsNone(recipe.superseded_recipe)

    def test_schedule_trigger_rule_custom(self):
        """Tests calling BatchManager.schedule_recipes() using a custom trigger rule."""

        file1 = storage_test_utils.create_file(media_type='text/custom', data_type_tags=['test'])

        definition = {
            'trigger_rule': {
                'condition': {
                    'media_type': 'text/custom',
                    'data_types': ['test'],
                },
                'data': {
                    'input_data_name': 'Recipe Input',
                    'workspace_name': self.workspace.name,
                },
            },
        }

        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6, definition=definition)

        Batch.objects.schedule_recipes(batch.id)

        batch = Batch.objects.get(pk=batch.id)
        self.assertEqual(batch.status, 'CREATED')
        self.assertEqual(batch.total_count, 1)

        self.assertEqual(batch.created_count, 1)
        recipe = Recipe.objects.get(batch_id=batch.id)
        self.assertEqual(recipe.batch, batch)
        self.assertEqual(recipe.recipe_type, self.recipe_type_v6)
        self.assertIsNone(recipe.superseded_recipe)
        self.assertEqual(recipe.input['input_data'][0]['file_id'], file1.id)
