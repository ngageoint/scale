from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from rest_framework import status

import recipe.test.utils as recipe_test_utils
import batch.test.utils as batch_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util
from batch.definition.definition import BatchDefinition
from batch.models import Batch


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

        recipe_type1b = recipe_test_utils.create_recipe_type(name='test1', version='2.0')
        batch_test_utils.create_batch_old(recipe_type=recipe_type1b)

        recipe_type1c = recipe_test_utils.create_recipe_type(name='test1', version='3.0')
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


class TestBatchesViewV6(TestCase):

    def setUp(self):
        django.setup()

        self.recipe_type_1 = recipe_test_utils.create_recipe_type()
        self.batch_1 = batch_test_utils.create_batch(recipe_type=self.recipe_type_1, is_creation_done=True)

        self.recipe_type_2 = recipe_test_utils.create_recipe_type()
        self.batch_2 = batch_test_utils.create_batch(recipe_type=self.recipe_type_2)

    def test_invalid_version(self):
        """Tests calling the batches view with an invalid version"""

        url = '/v1/batches/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful_get(self):
        """Tests successfully calling the batches view"""

        url = '/v6/batches/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.batch_1.id:
                expected = self.batch_1
            elif entry['id'] == self.batch_2.id:
                expected = self.batch_2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['recipe_type']['id'], expected.recipe_type.id)

    def test_recipe_type_id(self):
        """Tests successfully calling the batches view filtered by recipe type identifier"""

        url = '/v6/batches/?recipe_type_id=%s' % self.batch_1.recipe_type.id
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['recipe_type']['id'], self.batch_1.recipe_type.id)

    def test_is_creation_done(self):
        """Tests successfully calling the batches view filtered by is_creation_done"""

        url = '/v6/batches/?is_creation_done=true'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.batch_1.id)

    def test_root_batch_id(self):
        """Tests successfully calling the batches view filtered by root_batch_id"""

        url = '/v6/batches/?root_batch_id=%s' % self.batch_2.id
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.batch_2.id)

    def test_order_by(self):
        """Tests successfully calling the batches view with sorting"""

        url = '/v6/batches/?order=-id'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['id'], self.batch_2.id)
        self.assertEqual(result['results'][1]['id'], self.batch_1.id)


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

        definition = BatchDefinition()
        definition.prev_batch_id = 1
        definition.job_names = ['job_a', 'job_b']
        definition.all_jobs = True
        new_batch = batch_test_utils.create_batch(definition=definition)

        url = '/v5/batches/%d/' % new_batch.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], new_batch.id)
        self.assertEqual(result['title'], new_batch.title)
        self.assertEqual(result['description'], new_batch.description)
        self.assertDictEqual(result['definition'], {'version': '1.0', 'job_names': ['job_a', 'job_b'],
                                                    'all_jobs': True})


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

        batch = batch_test_utils.create_batch()

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


class TestBatchesValidationView(TestCase):

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

        url = rest_util.get_url('/batches/validation/')
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

        url = rest_util.get_url('/batches/validation/')
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

        url = rest_util.get_url('/batches/validation/')
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

        url = rest_util.get_url('/batches/validation/')
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

        url = rest_util.get_url('/batches/validation/')
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

        url = rest_util.get_url('/batches/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
