""" Tests dataset views methods """
from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime
import json
import time

import django
from django.utils.timezone import utc, now
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase
from util import rest

from dataset.models import DataSet
import dataset.test.utils as dataset_test_utils
import storage.test.utils as storage_utils
from storage.models import ScaleFile, Workspace

"""Tests the v6/data-sets/ endpoint"""
class TestDatasetViews(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        self.dataset = dataset_test_utils.create_dataset(name='test-dataset-1',
            title="Test Dataset 1", description="Test Dataset Number 1", version='1.0.0')
        self.dataset2 = dataset_test_utils.create_dataset(name='test-dataset-2',
            title="Test Dataset 2", description="Test Dataset Number 2", version='2.0.0')

    def test_successful(self):
        """Tests successfully calling the v6/data-sets/ view.
        """

        url = '/%s/data-sets/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Test response contains specific dataset
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.dataset.id:
                expected = self.dataset
            elif entry['id'] == self.dataset2.id:
                expected = self.dataset2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['name'], expected.name)
            self.assertEqual(entry['version'], expected.version)
            self.assertEqual(entry['title'], expected.title)

    def test_dataset_created_time_successful(self):
        """Tests successfully calling the v6/datsets/?created_time= api call
        """

        url = '/%s/data-sets/?created=%s' % (self.api, '2016-01-01T00:00:00Z')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result

    def test_dataset_id_successful(self):
        """Tests successfully calling the v6/datsets/?id= api call
        """

        url = '/%s/data-sets/?id=%s' % (self.api, self.dataset.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result

    def test_dataset_name_successful(self):
        """Tests successfully calling the v6/datsets/?name= api call
        """

        url = '/%s/data-sets/?name=%s' % (self.api, self.dataset.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result

    def test_order_by(self):
        """Tests successfully calling the datasets view with sorting."""

        url = '/%s/data-sets/?order=name' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify 2 results
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

"""Tests the v6/data-sets POST calls """
class TestDataSetPostView(APITestCase):
    """Tests the v6/dataset/ POST API call"""
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

    def test_invalid_definition(self):
        """Tests successfully calling POST with an invalid definition."""
        json_data = {}

        url = '/%s/data-sets/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_add_dataset(self):
        """Tests adding a new dataset"""

        url = '/%s/data-sets/' % self.api

        json_data = {
            'title': 'My Dataset',
            'description': 'A test dataset',
            'definition': copy.deepcopy(dataset_test_utils.DATASET_DEFINITION),
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        result = json.loads(response.content)
        new_dataset_id = result['id']
        self.assertTrue('/%s/data-sets/%d/' % (self.api, new_dataset_id) in response['location'])

        self.assertEqual(result['title'], json_data['title'])
        self.assertEqual(result['description'], json_data['description'])

        # create another dataset
        json_data_2 = {
            'title': 'My Dataset 2',
            'description': 'Another test dataset',
            'definition': copy.deepcopy(dataset_test_utils.DATASET_DEFINITION),
        }
        response = self.client.generic('POST', url, json.dumps(json_data_2), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        result = json.loads(response.content)
        new_dataset_id = result['id']
        self.assertTrue('/%s/data-sets/%d/' % (self.api, new_dataset_id) in response['location'])

        self.assertEqual(result['title'], json_data_2['title'])
        self.assertEqual(result['description'], json_data_2['description'])


"""Tests the v6/data-sets/<dataset_id> and v6/datsets/<dataset_name> endpoints"""
class TestDatasetDetailsView(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        # Create workspace
        self.workspace = Workspace.objects.create(name='Test Workspace', is_active=True, created=now(),
                                                  last_modified=now())
        # Create files
        self.src_file_a = storage_utils.create_file(file_name='input_a.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.src_file_b = storage_utils.create_file(file_name='input_b.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.src_file_c = storage_utils.create_file(file_name='input_c.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.src_file_b2 = storage_utils.create_file(file_name='input_b2.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.src_file_e = storage_utils.create_file(file_name='input_e.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.src_file_f = storage_utils.create_file(file_name='input_f.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)

        # Create datasets
        parameters = {'version': '6',
                      'files': [
                          {'name': 'input_a',
                           'media_types': ['application/json'],
                           'required': True,
                           'partial': False}
                      ],
                      'json': []}
        definition = {'version': '6', 'parameters': parameters}
        self.dataset = dataset_test_utils.create_dataset(name='test-dataset-1',
            title="Test Dataset 1", description="Test Dataset Number 1", definition=definition)

        parameters2 = {'version': '6',
                      'files': [
                          {'name': 'input_b',
                           'media_types': ['application/json'],
                           'required': True,
                           'multiple': True},
                          {'name': 'input_c',
                           'media_types': ['application/json'],
                           'required': False,
                           'partial': False}
                      ],
                      'json': []}
        definition2 = {'version': '6', 'parameters': parameters2}
        self.dataset2 = dataset_test_utils.create_dataset(name='test-dataset-2',
            title="Test Dataset 2", description="Test Dataset Number 2",
            definition=definition2)

        # Create members
        file = storage_utils.create_file(file_name="test.json", media_type='application/json')
        data = {
            'version': '6',
            'files': {'input_a': [self.src_file_a.id]},
            'json': {}
        }
        self.member_a = dataset_test_utils.create_dataset_member(dataset=self.dataset,
            data=data)

        data2 = {
            'version': '6',
            'files': {'input_b': [self.src_file_b.id, self.src_file_b2.id]},
            'json': {}
        }
        self.mamber_b = dataset_test_utils.create_dataset_member(dataset=self.dataset2,
            data=data2)

        data3 = {
            'version': '6',
            'files': {'input_b': [self.src_file_b.id, self.src_file_b2.id], 'input_c': [self.src_file_c.id]},
            'json': {}
        }
        self.member_bc = dataset_test_utils.create_dataset_member(dataset=self.dataset2,
            data=data3)

    def test_datasets_id_successful(self):
        """Tests successfully calling the v6/data-sets/<dataset_id>/ view.
        """

        url = '/%s/data-sets/%d/' % (self.api, self.dataset.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset details
        result = json.loads(response.content)
        self.assertEqual(result['id'], self.dataset.id)
        self.assertEqual(result['name'], self.dataset.name)
        self.assertEqual(result['title'], self.dataset.title)
        self.assertEqual(result['description'], self.dataset.description)
        self.assertEqual(result['version'], self.dataset.version)
        self.assertDictEqual(result['definition'], self.dataset.definition)
        self.assertEqual(len(result['files']), 3)

        url = '/%s/data-sets/%d/' % (self.api, self.dataset2.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset details
        result = json.loads(response.content)
        self.assertEqual(result['id'], self.dataset2.id)
        self.assertEqual(result['name'], self.dataset2.name)
        self.assertEqual(result['title'], self.dataset2.title)
        self.assertEqual(result['description'], self.dataset2.description)
        self.assertEqual(result['version'], self.dataset2.version)
        self.assertDictEqual(result['definition'], self.dataset2.definition)
        self.assertEqual(len(result['files']), 3)


    def test_datasets_name_successful(self):
        """Tests successfully calling the v6/datsets/<dataset-name>/ view.
        """

        url = '/%s/data-sets/%s/' % (self.api, self.dataset.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset details
        results = json.loads(response.content)
        self.assertEqual(len(results['results']), 2)
        for entry in results['results']:
            expected = None
            if entry['id'] == self.dataset.id:
                expected = self.dataset
            elif entry['id'] == self.dataset2.id:
                expected = self.dataset2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])

            self.assertEqual(entry['name'], expected.name)
            self.assertEqual(entry['title'], expected.title)
            self.assertEqual(entry['version'], expected.version)
            # self.assertEqual(entry['versions'], ['1.0.0', '1.1.1'])

    def test_datasets_name_version_successful(self):
        """Tests successfully calling the v6/data-sets/<dataset-name>/<version> view.
        """

        url = '/%s/data-sets/%s/%s/' % (self.api, self.dataset.name, self.dataset.version)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # check response for details
        result = json.loads(response.content)
        self.assertEqual(result['title'], self.dataset.title)
        self.assertEqual(result['description'], self.dataset.description)

        url = '/%s/data-sets/%s/%s/' % (self.api, self.dataset2.name, self.dataset2.version)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # check response for details
        result = json.loads(response.content)
        self.assertEqual(result['title'], self.dataset2.title)
        self.assertEqual(result['description'], self.dataset2.description)


class TestDataSetValidationView(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

    def test_validate_successful(self):
        """Tests successfully validating a new dataset using the v6/data-sets/validation API
        """

        url = '/%s/data-sets/validation/' % self.api

        json_data = {
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'description': 'My Test Dataset',
            'version': '1.0.0',
            'definition': {
                'version': '6',
                'parameters': [
                    {
                        'name': 'global-param',
                        'param_type': 'global',
                    },
                    {
                        'name': 'member-param',
                        'param_type': 'member',
                    },
                ],
            },
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['warnings']), 0)
        self.assertEqual(len(results['errors']), 0)

    def test_validate_missing_definition(self):
        url = '/%s/data-sets/validation/' % self.api

        json_data = {
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'description': 'My Test Dataset',
            'version': '1.0.0',
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['detail'], "Missing required parameter: \"definition\"")

    def test_invalid_definition(self):
        """Validates an invalid dataset definition

        Will complete when dataset definition is fully defined.
        """

        url = '/%s/data-sets/validation/' % self.api

        json_data = {
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'description': 'My Test Dataset',
            'version': '1.0.0',
            'definition': {
                'version': '6',
                'parameters': [
                    {
                        'name': 'global-param',
                    },
                    {
                        'name': 'member-param',
                    },
                ],
            },
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertFalse(results['is_valid'])
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['name'], 'INVALID_DATASET_DEFINITION')
