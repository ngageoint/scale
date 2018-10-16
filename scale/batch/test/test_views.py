from __future__ import unicode_literals

import json
from datetime import timedelta

import django
from django.test import TestCase, TransactionTestCase
from mock import patch
from rest_framework import status

import job.test.utils as job_test_utils
import recipe.test.utils as recipe_test_utils
import batch.test.utils as batch_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util
from batch.configuration.configuration import BatchConfiguration
from batch.definition.definition import BatchDefinition
from batch.messages.create_batch_recipes import CreateBatchRecipes
from batch.models import Batch, BatchMetrics
from recipe.configuration.definition.recipe_definition import LegacyRecipeDefinition
from recipe.diff.forced_nodes import ForcedNodes
from recipe.models import RecipeType
from util.parse import datetime_to_string, duration_to_string


class TestBatchesViewV5(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

        self.recipe_type1 = recipe_test_utils.create_recipe_type(name='test1', version='1.0')
        self.batch1 = batch_test_utils.create_batch_old(recipe_type=self.recipe_type1, status='SUBMITTED')

        self.recipe_type2 = recipe_test_utils.create_recipe_type(name='test2', version='1.0')
        self.batch2 = batch_test_utils.create_batch_old(recipe_type=self.recipe_type2, status='CREATED')

    def test_successful(self):
        """Tests successfully calling the batches view."""

        url = '/v5/batches/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.batch1.id:
                expected = self.batch1
            elif entry['id'] == self.batch2.id:
                expected = self.batch2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['recipe_type']['id'], expected.recipe_type.id)

    def test_status(self):
        """Tests successfully calling the batches view filtered by status."""

        url = '/v5/batches/?status=SUBMITTED'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['recipe_type']['id'], self.batch1.recipe_type.id)

    def test_recipe_type_id(self):
        """Tests successfully calling the batches view filtered by recipe type identifier."""

        url = '/v5/batches/?recipe_type_id=%s' % self.batch1.recipe_type.id
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['recipe_type']['id'], self.batch1.recipe_type.id)

    def test_recipe_type_name(self):
        """Tests successfully calling the batches view filtered by recipe type name."""

        url = '/v5/batches/?recipe_type_name=%s' % self.batch1.recipe_type.name
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['recipe_type']['name'], self.batch1.recipe_type.name)

    def test_order_by(self):
        """Tests successfully calling the batches view with sorting."""

        recipe_type1b = recipe_test_utils.create_recipe_type(name='2test2', version='2.0')
        batch_test_utils.create_batch_old(recipe_type=recipe_type1b)

        recipe_type1c = recipe_test_utils.create_recipe_type(name='1test1', version='3.0')
        batch_test_utils.create_batch_old(recipe_type=recipe_type1c)

        url = '/v5/batches/?order=recipe_type__name&order=-recipe_type__version'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)
        self.assertEqual(result['results'][0]['recipe_type']['id'], recipe_type1c.id)
        self.assertEqual(result['results'][1]['recipe_type']['id'], recipe_type1b.id)
        self.assertEqual(result['results'][2]['recipe_type']['id'], self.recipe_type1.id)
        self.assertEqual(result['results'][3]['recipe_type']['id'], self.recipe_type2.id)

    def test_create(self):
        """Tests creating a new batch."""
        json_data = {
            'recipe_type_id': self.recipe_type1.id,
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'definition': {
                'version': '1.0',
                'all_jobs': True,
            },
        }

        url = '/v5/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        batch = Batch.objects.filter(title='batch-title-test').first()

        result = json.loads(response.content)
        self.assertEqual(result['id'], batch.id)
        self.assertEqual(result['title'], 'batch-title-test')
        self.assertEqual(result['description'], 'batch-description-test')
        self.assertEqual(result['recipe_type']['id'], self.recipe_type1.id)
        self.assertIsNotNone(result['event'])
        self.assertIsNotNone(result['creator_job'])
        self.assertIsNotNone(result['definition'])

    def test_create_trigger_true(self):
        """Tests creating a new batch using the default trigger rule."""
        storage_test_utils.create_file(media_type='text/plain')

        json_data = {
            'recipe_type_id': self.recipe_type1.id,
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'definition': {
                'version': '1.0',
                'trigger_rule': True,
            },
        }

        url = '/v5/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        batch = Batch.objects.filter(title='batch-title-test').first()

        result = json.loads(response.content)
        self.assertEqual(result['id'], batch.id)
        self.assertEqual(result['title'], 'batch-title-test')
        self.assertEqual(result['description'], 'batch-description-test')
        self.assertEqual(result['recipe_type']['id'], self.recipe_type1.id)
        self.assertIsNotNone(result['event'])
        self.assertIsNotNone(result['creator_job'])
        self.assertIsNotNone(result['definition'])

    def test_create_trigger_custom(self):
        """Tests creating a new batch using a custom trigger rule."""
        workspace = storage_test_utils.create_workspace()
        storage_test_utils.create_file(media_type='text/plain', data_type='test', workspace=workspace)

        json_data = {
            'recipe_type_id': self.recipe_type1.id,
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'definition': {
                'version': '1.0',
                'trigger_rule': {
                    'condition': {
                        'media_type': 'text/custom',
                        'data_types': ['test'],
                    },
                    'data': {
                        'input_data_name': 'Recipe Input',
                        'workspace_name': workspace.name,
                    },
                },
            },
        }

        url = '/v5/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        batch = Batch.objects.filter(title='batch-title-test').first()

        result = json.loads(response.content)
        self.assertEqual(result['id'], batch.id)
        self.assertEqual(result['title'], 'batch-title-test')
        self.assertEqual(result['description'], 'batch-description-test')
        self.assertEqual(result['recipe_type']['id'], self.recipe_type1.id)
        self.assertIsNotNone(result['event'])
        self.assertIsNotNone(result['creator_job'])
        self.assertIsNotNone(result['definition'])

    def test_create_missing_param(self):
        """Tests creating a batch with missing fields."""
        json_data = {
            'title': 'batch-test',
        }

        url = '/v5/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_bad_param(self):
        """Tests creating a batch with invalid type fields."""
        json_data = {
            'recipe_type_id': 'BAD',
            'title': 'batch-test',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'all_jobs': True,
            },
        }

        url = '/v5/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_bad_definition(self):
        """Tests creating a new batch with an invalid definition."""
        json_data = {
            'recipe_type_id': self.recipe_type1.id,
            'title': 'batch-test',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'date_range': {
                    'type': 'BAD',
                },
            },
        }

        url = '/v5/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestBatchesViewV6(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.recipe_type_1 = recipe_test_utils.create_recipe_type()
        self.batch_1 = batch_test_utils.create_batch(recipe_type=self.recipe_type_1, is_creation_done=False)

        self.recipe_type_2 = recipe_test_utils.create_recipe_type()
        self.batch_2 = batch_test_utils.create_batch(recipe_type=self.recipe_type_2, is_creation_done=True)

    def test_invalid_version(self):
        """Tests calling the batches view with an invalid REST API version"""

        url = '/v1/batches/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful_get(self):
        """Tests successfully calling the batches view"""

        url = '/v6/batches/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)

    def test_recipe_type_id(self):
        """Tests successfully calling the batches view filtered by recipe type identifier"""

        url = '/v6/batches/?recipe_type_id=%s' % self.batch_1.recipe_type.id
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['recipe_type']['id'], self.batch_1.recipe_type.id)

    def test_is_creation_done(self):
        """Tests successfully calling the batches view filtered by is_creation_done"""

        url = '/v6/batches/?is_creation_done=false'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.batch_1.id)

    def test_root_batch_and_superseded(self):
        """Tests successfully calling the batches view filtered by is_superseded and root_batch_id"""

        url = '/v6/batches/?root_batch_id=%s&is_superseded=True' % self.batch_2.root_batch_id
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.batch_2.superseded_batch_id)

    def test_root_batch_id(self):
        """Tests successfully calling the batches view filtered by root_batch_id"""

        url = '/v6/batches/?root_batch_id=%s&order=id' % self.batch_2.root_batch_id
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['id'], self.batch_2.superseded_batch_id)
        self.assertEqual(result['results'][1]['id'], self.batch_2.id)

    def test_order_by(self):
        """Tests successfully calling the batches view with sorting"""

        url = '/v6/batches/?order=-id'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)
        self.assertEqual(result['results'][0]['id'], self.batch_2.id)
        self.assertEqual(result['results'][1]['id'], self.batch_2.superseded_batch_id)
        self.assertEqual(result['results'][2]['id'], self.batch_1.id)
        self.assertEqual(result['results'][3]['id'], self.batch_1.superseded_batch_id)

    def test_create_invalid_version(self):
        """Tests creating a new batch with an invalid REST API version"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True)
        json_data = {
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'recipe_type_id': self.recipe_type_1.id,
            'definition': {}
        }

        url = '/v1/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_create_invalid_recipe_type(self):
        """Tests creating a new batch with an invalid recipe type"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True)
        json_data = {
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'recipe_type_id': 999999,
            'definition': {
                'previous_batch': {
                    'root_batch_id': self.batch_1.root_batch_id
                }
            }
        }

        url = '/v6/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_invalid_definition(self):
        """Tests creating a new batch with an invalid definition"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True)
        json_data = {
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'recipe_type_id': self.recipe_type_1.id,
            'definition': {
                'previous_batch': {
                    'bad_definition': 'foo'
                }
            }
        }

        url = '/v6/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_invalid_configuration(self):
        """Tests creating a new batch with an invalid configuration"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True)
        json_data = {
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'recipe_type_id': self.recipe_type_1.id,
            'definition': {
                'previous_batch': {
                    'root_batch_id': self.batch_1.root_batch_id
                }
            },
            'configuration': {
                'bad-config': 'foo'
            }
        }

        url = '/v6/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    @patch('batch.views.CommandMessageManager')
    @patch('batch.views.create_batch_recipes_message')
    def test_create_successful(self, mock_create, mock_msg_mgr):
        """Tests creating a new batch successfully"""

        msg = CreateBatchRecipes()
        mock_create.return_value = msg

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True, recipes_total=777)
        json_data = {
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'recipe_type_id': self.recipe_type_1.id,
            'definition': {
                'previous_batch': {
                    'root_batch_id': self.batch_1.root_batch_id
                }
            },
            'configuration': {
                'priority': 100
            }
        }

        url = '/v6/batches/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        result = json.loads(response.content)
        new_batch_id = result['id']

        # Check location header
        self.assertTrue('/v6/batches/%d/' % new_batch_id in response['Location'])
        # Check that create_batch_recipes message was created and sent
        mock_create.assert_called_with(new_batch_id)
        # Check correct root batch ID in new batch
        self.assertEqual(result['root_batch']['id'], self.batch_1.root_batch_id)
        # Check correct recipe estimation count
        self.assertEqual(result['recipes_estimated'], 777)


class TestBatchDetailsViewV5(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

        self.recipe_type = recipe_test_utils.create_recipe_type()
        self.batch = batch_test_utils.create_batch_old(recipe_type=self.recipe_type)

    def test_not_found(self):
        """Tests successfully calling the v5 batch details view with a batch id that does not exist"""

        url = '/v5/batches/100000/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the v5 batch details view"""

        url = '/v5/batches/%d/' % self.batch.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.batch.id)
        self.assertEqual(result['title'], self.batch.title)
        self.assertEqual(result['description'], self.batch.description)
        self.assertEqual(result['status'], self.batch.status)

        self.assertEqual(result['recipe_type']['id'], self.recipe_type.id)
        self.assertIsNotNone(result['event'])
        self.assertIsNotNone(result['creator_job'])
        self.assertIsNotNone(result['definition'])

    def test_successful_with_new_batch(self):
        """Tests successfully calling the v5 batch details view with a new (v6) batch"""

        recipe_type = recipe_test_utils.create_recipe_type()
        prev_batch = batch_test_utils.create_batch(recipe_type=recipe_type, is_creation_done=True, recipes_total=10)
        definition = BatchDefinition()
        definition.root_batch_id = prev_batch.root_batch_id
        definition.forced_nodes = ForcedNodes()
        definition.forced_nodes.add_node('job_a')
        definition.forced_nodes.add_node('job_b')
        new_batch = batch_test_utils.create_batch(recipe_type=recipe_type, definition=definition, recipes_total=10)

        url = '/v5/batches/%d/' % new_batch.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], new_batch.id)
        self.assertEqual(result['title'], new_batch.title)
        self.assertEqual(result['description'], new_batch.description)
        self.assertEqual(result['created_count'], 10)
        self.assertEqual(result['total_count'], 10)
        self.assertDictEqual(result['definition'], {'version': '1.0', 'job_names': ['job_a', 'job_b'],
                                                    'all_jobs': False})


class TestBatchDetailsViewV6(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

    def test_invalid_version(self):
        """Tests calling the v6 batch details view with an invalid version"""

        batch = batch_test_utils.create_batch()

        url = '/v1/batches/%d' % batch.id
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_not_found(self):
        """Tests successfully calling the v6 batch details view with a batch id that does not exist"""

        url = '/v6/batches/100000/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the v6 batch details view"""

        job_type = job_test_utils.create_job_type()
        recipe_definition_dict = {'jobs': [{'name': 'job_a', 'job_type': {'name': job_type.name,
                                                                          'version': job_type.version}}]}
        recipe_type = recipe_test_utils.create_recipe_type(definition=recipe_definition_dict)
        configuration = BatchConfiguration()
        configuration.priority = 100
        batch = batch_test_utils.create_batch(recipe_type=recipe_type, configuration=configuration)

        url = '/v6/batches/%d/' % batch.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], batch.id)
        self.assertEqual(result['title'], batch.title)
        self.assertEqual(result['description'], batch.description)
        self.assertEqual(result['recipe_type']['id'], batch.recipe_type.id)
        self.assertDictEqual(result['definition'], batch.get_v6_definition_json())
        self.assertDictEqual(result['configuration'], batch.get_v6_configuration_json())

    def test_successful_with_old_batch(self):
        """Tests successfully calling the v6 batch details view with an old-style batch"""

        batch = batch_test_utils.create_batch_old()

        url = '/v6/batches/%d/' % batch.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], batch.id)
        self.assertEqual(result['title'], batch.title)
        self.assertEqual(result['description'], batch.description)
        self.assertEqual(result['recipe_type']['id'], batch.recipe_type.id)
        self.assertDictEqual(result['definition'], {})
        self.assertDictEqual(result['configuration'], {})

    def test_edit_invalid_version(self):
        """Tests editing a batch with an invalid REST API version"""

        batch = batch_test_utils.create_batch()

        json_data = {
            'title': 'New Title',
            'description': 'New Description',
            'configuration': {
                'priority': 200
            }
        }

        url = '/v1/batches/%d/' % batch.id
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_edit_invalid_batch(self):
        """Tests editing an invalid batch ID"""

        json_data = {
            'title': 'New Title',
            'description': 'New Description',
            'configuration': {
                'priority': 200
            }
        }

        url = '/v6/batches/%d/' % 999999
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_edit_invalid_configuration(self):
        """Tests editing a batch with an invalid configuration"""

        batch = batch_test_utils.create_batch()

        json_data = {
            'title': 'New Title',
            'description': 'New Description',
            'configuration': {
                'bad': 'foo'
            }
        }

        url = '/v6/batches/%d/' % batch.id
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_edit_successful(self):
        """Tests editing a batch successfully"""

        batch = batch_test_utils.create_batch()

        json_data = {
            'title': 'New Title',
            'description': 'New Description',
            'configuration': {
                'priority': 267
            }
        }

        url = '/v6/batches/%d/' % batch.id
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

        batch = Batch.objects.get(id=batch.id)
        self.assertEqual(batch.title, 'New Title')
        self.assertEqual(batch.description, 'New Description')
        self.assertEqual(batch.get_configuration().priority, 267)

    def test_edit_put_not_allowed(self):
        """Tests editing a batch with HTTP PUT to ensure it is not allowed"""

        batch = batch_test_utils.create_batch()

        json_data = {
            'title': 'New Title',
            'description': 'New Description',
            'configuration': {
                'priority': 267
            }
        }

        url = '/v6/batches/%d/' % batch.id
        response = self.client.generic('PUT', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, 405, response.content)


class TestBatchesComparisonViewV6(TestCase):

    def setUp(self):
        django.setup()

    def test_invalid_version(self):
        """Tests calling the v6 batch comparison view with an invalid version"""

        batch = batch_test_utils.create_batch()

        url = '/v1/batches/comparison/%d/' % batch.root_batch_id
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful_no_batches(self):
        """Tests successfully calling the v6 batch comparison view with a root batch ID that does not exist"""

        url = '/v6/batches/comparison/100000/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertDictEqual(result, {'batches': [], 'metrics': {'jobs_total': [], 'jobs_pending': [],
                                      'jobs_blocked': [], 'jobs_queued': [], 'jobs_running': [], 'jobs_failed': [],
                                      'jobs_completed': [], 'jobs_canceled': [], 'recipes_estimated': [],
                                      'recipes_total': [], 'recipes_completed': [], 'job_metrics': {}}})

    def test_successful(self):
        """Tests successfully calling the v6 batch comparison view"""

        job_type_1 = job_test_utils.create_job_type()
        job_type_2 = job_test_utils.create_job_type()
        job_type_3 = job_test_utils.create_job_type()

        rt_definition_1 = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'job_a',
                'job_type': {
                    'name': job_type_1.name,
                    'version': job_type_1.version,
                }
            }, {
                'name': 'job_b',
                'job_type': {
                    'name': job_type_2.name,
                    'version': job_type_2.version,
                },
                'dependencies': [{'name': 'job_a'}]
            }],
        }
        rt_definition_2 = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'job_c',
                'job_type': {
                    'name': job_type_3.name,
                    'version': job_type_3.version,
                }
            }, {
                'name': 'job_b',
                'job_type': {
                    'name': job_type_2.name,
                    'version': job_type_2.version,
                },
                'dependencies': [{'name': 'job_c'}]
            }],
        }
        recipe_type = recipe_test_utils.create_recipe_type(definition=rt_definition_1)

        # Create a chain of two batches
        batch_1 = batch_test_utils.create_batch(recipe_type=recipe_type, is_creation_done=True, recipes_total=2)
        # Right now test utils will automatically have batch_1 supersede another batch, so we reset this so batch_1 is
        # its own chain
        batch_1.root_batch_id = batch_1.id
        batch_1.superseded_batch = None
        batch_1.save()
        # Change recipe type to new revision
        RecipeType.objects.edit_recipe_type(recipe_type.id, None, None, LegacyRecipeDefinition(rt_definition_2),
                                            None, None)
        recipe_type = RecipeType.objects.get(id=recipe_type.id)
        definition_2 = BatchDefinition()
        definition_2.root_batch_id = batch_1.root_batch_id
        batch_2 = batch_test_utils.create_batch(recipe_type=recipe_type, definition=definition_2)

        # Set metrics to test values
        Batch.objects.filter(id=batch_1.id).update(jobs_total=24, jobs_pending=0, jobs_blocked=10, jobs_queued=0,
                                                   jobs_running=0, jobs_failed=2, jobs_completed=12, jobs_canceled=0,
                                                   recipes_estimated=2, recipes_total=2, recipes_completed=1)
        Batch.objects.filter(id=batch_2.id).update(jobs_total=26, jobs_pending=2, jobs_blocked=6, jobs_queued=3,
                                                   jobs_running=5, jobs_failed=6, jobs_completed=3, jobs_canceled=1,
                                                   recipes_estimated=2, recipes_total=2, recipes_completed=0)
        min_seed_duration_1a = timedelta(seconds=43)
        avg_seed_duration_1a = timedelta(seconds=68)
        max_seed_duration_1a = timedelta(seconds=77)
        min_job_duration_1a = timedelta(seconds=45)
        avg_job_duration_1a = timedelta(seconds=70)
        max_job_duration_1a = timedelta(seconds=79)
        qry = BatchMetrics.objects.filter(batch_id=batch_1.id, job_name='job_a')
        qry.update(jobs_total=12, jobs_pending=0, jobs_blocked=0, jobs_queued=0, jobs_running=0, jobs_failed=0,
                   jobs_completed=12, jobs_canceled=0, min_seed_duration=min_seed_duration_1a,
                   avg_seed_duration=avg_seed_duration_1a, max_seed_duration=max_seed_duration_1a,
                   min_job_duration=min_job_duration_1a, avg_job_duration=avg_job_duration_1a,
                   max_job_duration=max_job_duration_1a)
        min_seed_duration_1b = timedelta(seconds=15)
        avg_seed_duration_1b = timedelta(seconds=18)
        max_seed_duration_1b = timedelta(seconds=23)
        min_job_duration_1b = timedelta(seconds=18)
        avg_job_duration_1b = timedelta(seconds=21)
        max_job_duration_1b = timedelta(seconds=26)
        qry = BatchMetrics.objects.filter(batch_id=batch_1.id, job_name='job_b')
        qry.update(jobs_total=12, jobs_pending=0, jobs_blocked=10, jobs_queued=0, jobs_running=0, jobs_failed=2,
                   jobs_completed=0, jobs_canceled=0, min_seed_duration=min_seed_duration_1b,
                   avg_seed_duration=avg_seed_duration_1b, max_seed_duration=max_seed_duration_1b,
                   min_job_duration=min_job_duration_1b, avg_job_duration=avg_job_duration_1b,
                   max_job_duration=max_job_duration_1b)
        min_seed_duration_2b = timedelta(seconds=9)
        avg_seed_duration_2b = timedelta(seconds=12)
        max_seed_duration_2b = timedelta(seconds=17)
        min_job_duration_2b = timedelta(seconds=12)
        avg_job_duration_2b = timedelta(seconds=15)
        max_job_duration_2b = timedelta(seconds=20)
        qry = BatchMetrics.objects.filter(batch_id=batch_2.id, job_name='job_b')
        qry.update(jobs_total=13, jobs_pending=0, jobs_blocked=0, jobs_queued=0, jobs_running=3, jobs_failed=6,
                   jobs_completed=3, jobs_canceled=1, min_seed_duration=min_seed_duration_2b,
                   avg_seed_duration=avg_seed_duration_2b, max_seed_duration=max_seed_duration_2b,
                   min_job_duration=min_job_duration_2b, avg_job_duration=avg_job_duration_2b,
                   max_job_duration=max_job_duration_2b)
        min_seed_duration_2c = timedelta(seconds=101)
        avg_seed_duration_2c = timedelta(seconds=136)
        max_seed_duration_2c = timedelta(seconds=158)
        min_job_duration_2c = timedelta(seconds=111)
        avg_job_duration_2c = timedelta(seconds=146)
        max_job_duration_2c = timedelta(seconds=168)
        qry = BatchMetrics.objects.filter(batch_id=batch_2.id, job_name='job_c')
        qry.update(jobs_total=13, jobs_pending=2, jobs_blocked=6, jobs_queued=3, jobs_running=2, jobs_failed=0,
                   jobs_completed=0, jobs_canceled=0, min_seed_duration=min_seed_duration_2c,
                   avg_seed_duration=avg_seed_duration_2c, max_seed_duration=max_seed_duration_2c,
                   min_job_duration=min_job_duration_2c, avg_job_duration=avg_job_duration_2c,
                   max_job_duration=max_job_duration_2c)
        expected_job_metrics = {'job_a': {'jobs_total': [12, None], 'jobs_pending': [0, None],
                                          'jobs_blocked': [0, None], 'jobs_queued': [0, None],
                                          'jobs_running': [0, None], 'jobs_failed': [0, None],
                                          'jobs_completed': [12, None], 'jobs_canceled': [0, None],
                                          'min_seed_duration': [duration_to_string(min_seed_duration_1a), None],
                                          'avg_seed_duration': [duration_to_string(avg_seed_duration_1a), None],
                                          'max_seed_duration': [duration_to_string(max_seed_duration_1a), None],
                                          'min_job_duration': [duration_to_string(min_job_duration_1a), None],
                                          'avg_job_duration': [duration_to_string(avg_job_duration_1a), None],
                                          'max_job_duration': [duration_to_string(max_job_duration_1a), None]},
                                'job_b': {'jobs_total': [12, 13], 'jobs_pending': [0, 0],
                                          'jobs_blocked': [10, 0], 'jobs_queued': [0, 0],
                                          'jobs_running': [0, 3], 'jobs_failed': [2, 6],
                                          'jobs_completed': [0, 3], 'jobs_canceled': [0, 1],
                                          'min_seed_duration': [duration_to_string(min_seed_duration_1b),
                                                                duration_to_string(min_seed_duration_2b)],
                                          'avg_seed_duration': [duration_to_string(avg_seed_duration_1b),
                                                                duration_to_string(avg_seed_duration_2b)],
                                          'max_seed_duration': [duration_to_string(max_seed_duration_1b),
                                                                duration_to_string(max_seed_duration_2b)],
                                          'min_job_duration': [duration_to_string(min_job_duration_1b),
                                                               duration_to_string(min_job_duration_2b)],
                                          'avg_job_duration': [duration_to_string(avg_job_duration_1b),
                                                               duration_to_string(avg_job_duration_2b)],
                                          'max_job_duration': [duration_to_string(max_job_duration_1b),
                                                               duration_to_string(max_job_duration_2b)]},
                                'job_c': {'jobs_total': [None, 13], 'jobs_pending': [None, 2],
                                          'jobs_blocked': [None, 6], 'jobs_queued': [None, 3],
                                          'jobs_running': [None, 2], 'jobs_failed': [None, 0],
                                          'jobs_completed': [None, 0], 'jobs_canceled': [None, 0],
                                          'min_seed_duration': [None, duration_to_string(min_seed_duration_2c)],
                                          'avg_seed_duration': [None, duration_to_string(avg_seed_duration_2c)],
                                          'max_seed_duration': [None, duration_to_string(max_seed_duration_2c)],
                                          'min_job_duration': [None, duration_to_string(min_job_duration_2c)],
                                          'avg_job_duration': [None, duration_to_string(avg_job_duration_2c)],
                                          'max_job_duration': [None, duration_to_string(max_job_duration_2c)]}
                               }
        expected_result = {'batches': [{'id': batch_1.id, 'title': batch_1.title, 'description': batch_1.description,
                                        'created': datetime_to_string(batch_1.created)},
                                       {'id': batch_2.id, 'title': batch_2.title, 'description': batch_2.description,
                                        'created': datetime_to_string(batch_2.created)}],
                           'metrics': {'jobs_total': [24, 26], 'jobs_pending': [0, 2], 'jobs_blocked': [10, 6],
                                       'jobs_queued': [0, 3], 'jobs_running': [0, 5], 'jobs_failed': [2, 6],
                                       'jobs_completed': [12, 3], 'jobs_canceled': [0, 1], 'recipes_estimated': [2, 2],
                                       'recipes_total': [2, 2], 'recipes_completed': [1, 0],
                                       'job_metrics': expected_job_metrics}
                          }
        url = '/v6/batches/comparison/%d/' % batch_2.root_batch_id
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertDictEqual(result, expected_result)


class TestBatchesValidationViewV5(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

        self.recipe_type1 = recipe_test_utils.create_recipe_type(name='test1', version='1.0')
        self.recipe1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type1)

    def test_successful(self):
        """Tests validating a batch definition."""
        json_data = {
            'recipe_type_id': self.recipe_type1.id,
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'definition': {
                'version': '1.0',
                'all_jobs': True,
            },
        }

        url = '/v5/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['file_count'], 0)
        self.assertEqual(result['recipe_count'], 1)
        self.assertEqual(len(result['warnings']), 0)

    def test_successful_trigger_true(self):
        """Tests validating a batch definition using the default trigger rule."""
        storage_test_utils.create_file(media_type='text/plain')

        json_data = {
            'recipe_type_id': self.recipe_type1.id,
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'definition': {
                'version': '1.0',
                'trigger_rule': True,
            },
        }

        url = '/v5/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['file_count'], 1)
        self.assertEqual(result['recipe_count'], 0)
        self.assertEqual(len(result['warnings']), 0)

    def test_successful_trigger_custom(self):
        """Tests validating a batch definition with a custom trigger rule."""
        workspace = storage_test_utils.create_workspace()
        storage_test_utils.create_file(media_type='text/plain', data_type='test', workspace=workspace)

        json_data = {
            'recipe_type_id': self.recipe_type1.id,
            'title': 'batch-title-test',
            'description': 'batch-description-test',
            'definition': {
                'version': '1.0',
                'trigger_rule': {
                    'condition': {
                        'media_type': 'text/custom',
                        'data_types': ['test'],
                    },
                    'data': {
                        'input_data_name': 'Recipe Input',
                        'workspace_name': workspace.name,
                    },
                },
            },
        }

        url = '/v5/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['file_count'], 1)
        self.assertEqual(result['recipe_count'], 0)
        self.assertEqual(len(result['warnings']), 0)

    def test_missing_param(self):
        """Tests validating a batch with missing fields."""
        json_data = {
            'title': 'batch-test',
        }

        url = '/v5/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_param(self):
        """Tests validating a batch with invalid type fields."""
        json_data = {
            'recipe_type_id': 'BAD',
            'title': 'batch-test',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'all_jobs': True,
            },
        }

        url = '/v5/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_definition(self):
        """Tests validating a new batch with an invalid definition."""
        json_data = {
            'recipe_type_id': self.recipe_type1.id,
            'title': 'batch-test',
            'description': 'This is a test.',
            'definition': {
                'version': '1.0',
                'date_range': {
                    'type': 'BAD',
                },
            },
        }

        url = '/v5/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestBatchesValidationViewV6(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.recipe_type_1 = recipe_test_utils.create_recipe_type()
        self.batch_1 = batch_test_utils.create_batch(recipe_type=self.recipe_type_1, is_creation_done=False)

        self.recipe_type_2 = recipe_test_utils.create_recipe_type()
        self.batch_2 = batch_test_utils.create_batch(recipe_type=self.recipe_type_2, is_creation_done=True)

    def test_invalid_version(self):
        """Tests validating a new batch with an invalid REST API version"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True)
        json_data = {
            'recipe_type_id': self.recipe_type_1.id,
            'definition': {}
        }

        url = '/v1/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_create_invalid_recipe_type(self):
        """Tests validating a new batch with an invalid recipe type"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True)
        json_data = {
            'recipe_type_id': 999999,
            'definition': {
                'previous_batch': {
                    'root_batch_id': self.batch_1.root_batch_id
                }
            }
        }

        url = '/v6/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_invalid_definition(self):
        """Tests creating a new batch with an invalid definition"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True)
        json_data = {
            'recipe_type_id': self.recipe_type_1.id,
            'definition': {
                'previous_batch': {
                    'bad_definition': 'foo'
                }
            }
        }

        url = '/v6/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_invalid_configuration(self):
        """Tests creating a new batch with an invalid configuration"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True)
        json_data = {
            'recipe_type_id': self.recipe_type_1.id,
            'definition': {
                'previous_batch': {
                    'root_batch_id': self.batch_1.root_batch_id
                }
            },
            'configuration': {
                'bad-config': 'foo'
            }
        }

        url = '/v6/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_invalid_prev_batch(self):
        """Tests creating a new batch with an invalid previous batch"""

        json_data = {
            'recipe_type_id': self.recipe_type_2.id,
            'definition': {
                'previous_batch': {
                    'root_batch_id': 9999
                }
            },
            'configuration': {
                'priority': 100
            }
        }

        url = '/v6/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        expected_recipe_type = {'id': self.recipe_type_2.id, 'name': self.recipe_type_2.name,
                                'title': self.recipe_type_2.title, 'description': self.recipe_type_2.description,
                                'revision_num': self.recipe_type_2.revision_num}

        # Ensure the new batch is not valid
        self.assertFalse(result['is_valid'])
        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(result['errors'][0]['name'], 'PREV_BATCH_NOT_FOUND')
        self.assertListEqual(result['warnings'], [])
        # Check correct recipe estimation count
        self.assertEqual(result['recipes_estimated'], 0)
        # Check for correct recipe type
        self.assertDictEqual(result['recipe_type'], expected_recipe_type)
        # CHeck that there is no previous batch
        self.assertTrue('prev_batch' not in result)

    def test_create_mismatched_recipe_types(self):
        """Tests creating a new batch with a mismatched recipe type"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True, recipes_total=777)
        json_data = {
            'recipe_type_id': self.recipe_type_2.id,
            'definition': {
                'previous_batch': {
                    'root_batch_id': self.batch_1.root_batch_id
                }
            },
            'configuration': {
                'priority': 100
            }
        }

        url = '/v6/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        expected_recipe_type = {'id': self.recipe_type_2.id, 'name': self.recipe_type_2.name,
                                'title': self.recipe_type_2.title, 'description': self.recipe_type_2.description,
                                'revision_num': self.recipe_type_2.revision_num}
        expected_recipe_type_rev = {'id': self.batch_1.recipe_type_rev.id, 'recipe_type': {'id': self.recipe_type_1.id},
                                    'revision_num': self.batch_1.recipe_type_rev.revision_num}

        # Ensure the new batch is not valid
        self.assertFalse(result['is_valid'])
        self.assertEqual(len(result['errors']), 1)
        self.assertEqual(result['errors'][0]['name'], 'MISMATCHED_RECIPE_TYPE')
        self.assertListEqual(result['warnings'], [])
        # Check correct recipe estimation count
        self.assertEqual(result['recipes_estimated'], 0)
        # Check for correct recipe type/revisions
        self.assertDictEqual(result['recipe_type'], expected_recipe_type)
        self.assertDictEqual(result['prev_batch']['recipe_type_rev'], expected_recipe_type_rev)
        self.assertTrue('diff' not in result['prev_batch'])

    def test_create_successful(self):
        """Tests creating a new batch successfully"""

        Batch.objects.filter(id=self.batch_1.id).update(is_creation_done=True, recipes_total=777)
        json_data = {
            'recipe_type_id': self.recipe_type_1.id,
            'definition': {
                'previous_batch': {
                    'root_batch_id': self.batch_1.root_batch_id
                }
            },
            'configuration': {
                'priority': 100
            }
        }

        url = '/v6/batches/validation/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        expected_recipe_type = {'id': self.recipe_type_1.id, 'name': self.recipe_type_1.name,
                                'title': self.recipe_type_1.title, 'description': self.recipe_type_1.description,
                                'revision_num': self.recipe_type_1.revision_num}
        expected_recipe_type_rev = {'id': self.batch_1.recipe_type_rev.id, 'recipe_type': {'id': self.recipe_type_1.id},
                                    'revision_num': self.batch_1.recipe_type_rev.revision_num}

        # Ensure the new batch is valid
        self.assertTrue(result['is_valid'])
        self.assertListEqual(result['errors'], [])
        self.assertListEqual(result['warnings'], [])
        # Check correct recipe estimation count
        self.assertEqual(result['recipes_estimated'], 777)
        # Check for correct recipe type/revisions
        self.assertDictEqual(result['recipe_type'], expected_recipe_type)
        self.assertDictEqual(result['prev_batch']['recipe_type_rev'], expected_recipe_type_rev)
        self.assertIsNotNone(result['prev_batch']['diff'])
