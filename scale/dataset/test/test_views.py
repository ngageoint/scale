""" Tests dataset views methods """
from __future__ import unicode_literals
from __future__ import absolute_import

import datetime
import json
import time

import django
from django.test import TestCase, TransactionTestCase
from django.utils.timezone import utc, now
from mock import patch
from rest_framework import status

from dataset.models import DataSet
import dataset.test.utils as dataset_test_utils

"""Tests the v6/datasets/ endpoint"""
class TestDatasetViews(TestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        self.dataset = dataset_test_utils.create_dataset(name='test-dataset-1',
            title="Test Dataset 1", description="Test Dataset Number 1", version='1.0.0')
        self.dataset2 = dataset_test_utils.create_dataset(name='test-dataset-2',
            title="Test Dataset 2", description="Test Dataset Number 2", version='1.0.0')

    def test_successful(self):
        """Tests successfully calling the v6/datasets/ view.
        """

        url = '/%s/datasets/' % self.api
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

        url = '/%s/datasets/?created=%s' % (self.api, '2016-01-01T00:00:00Z')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result

    def test_dataset_id_successful(self):
        """Tests successfully calling the v6/datsets/?id= api call
        """

        url = '/%s/datasets/?id=%s' % (self.api, self.dataset.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result

    def test_dataset_name_successful(self):
        """Tests successfully calling the v6/datsets/?name= api call
        """

        url = '/%s/datasets/?name=%s' % (self.api, self.dataset.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result

    def test_order_by(self):
        """Tests successfully calling the datasets view with sorting."""

        url = '/%s/datasets/?order=name' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify 2 results
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

"""Tests the v6/datasets POST calls """
class TestDataSetPostView(TestCase):
    """Tests the v6/dataset/ POST API call"""
    api = 'v6'

    def setUp(self):
        django.setup()

    def test_invalid_definition(self):
        """Tests successfully calling POST with an invalid definition."""
        json_data = {}

        url = '/%s/datasets/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_add_dataset(self):
        """Tests adding a new dataset"""

        url = '/%s/datasets/' % self.api

        json_data = {
            'name': 'my-new-dataset',
            'version': '1.0.0',
            'title': 'My Dataset',
            'description': 'A test dataset',
            'definition': {
                'name': 'my-new-dataset',
            },
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue('/%s/datasets/my-new-dataset/1.0.0/' % self.api in response['location'])

        dataset = DataSet.objects.filter(name='my-new-dataset').first()
        self.assertEqual(dataset.name, json_data['name'])
        self.assertEqual(dataset.title, json_data['title'])
        self.assertEqual(dataset.version, json_data['version'])

        # update the dataset
        json_data_2 = {
            'name': 'my-new-dataset',
            'version': '1.0.0',
            'title': 'My Dataset',
            'description': 'An updated test dataset',
            'definition': {
                'name': 'my-new-dataset',
            },
        }
        response = self.client.generic('POST', url, json.dumps(json_data_2), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue('/%s/datasets/my-new-dataset/1.0.0/' % self.api in response['location'])

        # check the dataset was updated
        dataset = DataSet.objects.filter(name='my-new-dataset').first()
        self.assertEqual(dataset.description, json_data_2['description'])


"""Tests the v6/datasets/<dataset_id> and v6/datsets/<dataset_name> endpoints"""
class TestDatasetDetailsView(TestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        # Create dataset with basic values
        self.dataset = dataset_test_utils.create_dataset(name='test-dataset-1',
            title="Test Dataset 1", description="Test Dataset Number 1", version='1.0.0')
        self.dataset2 = dataset_test_utils.create_dataset(name='test-dataset-1',
            title="Test Dataset 1", description="Updated Test Dataset Number 1", version='1.1.1')

    # def test_successful_empty(self):
    #     """Tests successfully calling the dataset details view with no data or results"""

    #     url = '/%s/datasets/%s/' % (self.api, 'empty-dataset')
    #     response = self.client.generic('GET', url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # check response for stuff
        # result = json.loads(response.content)
        # self.assertEqual(response[''], self.empty_dataset.)

    def test_datasets_id_successful(self):
        """Tests successfully calling the v6/datasets/<dataset_id>/ view.
        """

        url = '/%s/datasets/%d/' % (self.api, self.dataset.id)
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

    def test_datasets_name_successful(self):
        """Tests successfully calling the v6/datsets/<dataset-name>/ view.
        """

        url = '/%s/datasets/%s/' % (self.api, self.dataset.name)
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
        """Tests successfully calling the v6/datasets/<dataset-name>/<version> view.
        """

        url = '/%s/datasets/%s/%s/' % (self.api, self.dataset.name, self.dataset.version)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # check response for details
        result = json.loads(response.content)
        self.assertEqual(result['title'], self.dataset.title)
        self.assertEqual(result['description'], self.dataset.description)

        url = '/%s/datasets/%s/%s/' % (self.api, self.dataset2.name, self.dataset2.version)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # check response for details
        result = json.loads(response.content)
        self.assertEqual(result['title'], self.dataset2.title)
        self.assertEqual(result['description'], self.dataset2.description)


class TestDataSetValidationView(TestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

    def test_validate_successful(self):
        url = '/%s/datasets/validation/' % self.api

        json_data = {
            'name': 'test-dataset',
            'title': 'Test Dataset',
            'description': 'My Test Dataset',
            'version': '1.0.0',
            'definition': {
                'name': 'test-dataset',
                'parameters': [
                    {
                        'name': 'parameter-1',
                        'filter': {

                        }
                    }
                ],
            }
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['warnings']), 0)
        self.assertEqual(len(results['errors']), 0)

    def test_validate_missing_definition(self):
        url = '/%s/datasets/validation/' % self.api

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

    def test_validate_invalid_definition(self):
        """Validates an invalid dataset definition

        Will complete when dataset definition is defined.
        """
        pass
