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
                            'media_type': 'image/tiff',
                        }],
                    }
                }
            }
        }
        self.seed_job_type = job_test_utils.create_seed_job_type(manifest=manifest)

        self.definition_v6 = {
            'version': '6',
            'input': {'files':[{'name': 'TEST_INPUT_1', 'media_types': ['text/plain'],
                                'required': True, 'multiple': False}],
                     'json':[]},
            'nodes': {
                'job-a': {
                    'dependencies':[],
                    'input': {'TEST_INPUT_1': {'type': 'recipe', 'input': 'TEST_INPUT_1'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.seed_job_type.name,
                        'job_type_version': self.seed_job_type.version,
                        'job_type_revision': 1,
                    }
                }
            }
        }

        self.recipe_type_v6 = recipe_test_utils.create_recipe_type_v6(definition=self.definition_v6)
        self.recipe_type_rev_v6 = RecipeTypeRevision.objects.get(recipe_type_id=self.recipe_type_v6.id)

        manifest_2 = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'test-job-2',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': 'My second job',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 3600,
                'interface': {
                    'command': 'my_command args',
                    'inputs': {
                        'files': [{
                            'name': 'TEST_INPUT_2',
                            'type': 'file',
                            'media_types': ['image/tiff'],
                        }]
                    },
                    'outputs': {
                        'files': [{
                            'name': 'TEST_OUTPUT_2',
                            'type': 'file',
                            'media_type': 'image/png',
                        }],
                    }
                }
            }
        }
        self.seed_job_type_2 = job_test_utils.create_seed_job_type(manifest=manifest_2)

        self.definition_2_v6 = {
            'version': '6',
            'input': {'files':[{'name': 'TEST_INPUT_1', 'media_types': ['text/plain'],
                                'required': True, 'multiple': False}],
                     'json':[]},
            'nodes': {
                'job-a': {
                    'dependencies':[],
                    'input': {'TEST_INPUT_1': {'type': 'recipe', 'input': 'TEST_INPUT_1'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.seed_job_type.name,
                        'job_type_version': self.seed_job_type.version,
                        'job_type_revision': 1,
                    }
                },
                'job-b': {
                    'dependencies':[{'name': 'job-a'}],
                    'input': {'TEST_INPUT_2': {'type': 'dependency', 'node': 'job-a', 'output': 'TEST_OUTPUT_1'}},
                    'node_type': {
                        'node_type': 'job',
                        'job_type_name': self.seed_job_type_2.name,
                        'job_type_version': self.seed_job_type_2.version,
                        'job_type_revision': 1,
                    }
                }
            }
        }

        self.data_dict = {
            'version': '1.0',
            'input_data': [{
                'name': 'TEST_INPUT_1',
                'file_id': self.file.id,
            }],
            'workspace_id': self.workspace.id,
        }

        self.input_data = DataV6(self.data_dict, do_validate=False).get_data()

    def test_create_successful_v6(self):
        """Tests calling BatchManager.create_batch_v6"""
        batch = batch_test_utils.create_batch(recipe_type=self.recipe_type_v6)

        batch = Batch.objects.get(pk=batch.id)
        self.assertIsNotNone(batch.title)
        self.assertIsNotNone(batch.description)
        self.assertEqual(batch.recipe_type, self.recipe_type_v6)

        # Create message
        from batch.messages.create_batch_recipes import create_batch_recipes_message
        message = create_batch_recipes_message(batch.id)
        result = message.execute()
        self.assertTrue(result)

        batch = Batch.objects.get(pk=batch.id)
        self.assertTrue(batch.is_creation_done)
