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

"""Tests the v6/datasets/ endpoint"""
class TestDatasetViews(TestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        self.date_1 = datetime.datetime(2016, 1, 1, tzinfo=utc)

        #self.datset = dataset_test_utils.create_dataset(name='test-dataset-1', version='1.0.0')
        self.dataset = None

    def test_successful(self):
        """Tests successfully calling the v6/datasets/ view.
        """

        url = '/%s/datasets/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Test response contains specific dataset 

    def test_dataset_created_time_successfull(self):
        """Tests successfully calling the v6/datsets/?created_time= api call
        """

        url = '/%s/datasets/?created_time=%s' % (self.api, self.date_1)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result

    def test_dataset_dataset_id_successfull(self):
        """Tests successfully calling the v6/datsets/?dataset_id= api call
        """

        url = '/%s/datasets/?dataset_id=%s' % (self.api, self.dataset.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result

    def test_dataset_dataset_name_successfull(self):
        """Tests successfully calling the v6/datsets/?dataset_name= api call
        """

        url = '/%s/datasets/?dataset_name=%s' % (self.api, self.dataset.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result

    def test_order_by(self):
        """Tests successfully calling the datasets view with sorting."""

        url = '/%s/datasets/?order=dataset__name' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify X results
        result = json.loads(response.content)

"""Tests the v6/datasets POST calls """
class TestDataSetsPostView(TestCase):
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
        
        url = '/%s/datasets' % self.api
        
        json_data = {
            'name': 'my-new-dataset',
            'version': '1.0.0',
            'title': 'My Dataset',
            'description': 'A test dataset',
            'definition': {
                
            },
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue('/%s/datasets/my-new-dataset/1.0.0/' % self.api in response['location'])
        
        dataset = DataSet.objects.filter(name='my-new-dataset').first()
        
        # check the dataset created
        results = json.loads(response.content)
        # self.assertEqual(results['id'], dataset.id)
        # self.assertEqual(results['version'], dataset.version)
        # self.assertEqual(results['title'], dataset.title)
        # self.assertEqual(results['revision_num'], dataset.revision_num)
        
"""Tests the v6/datasets/<dataset_id> and v6/datsets/<dataset_name> endpoints"""  
class TestDatasetDetailsView(TestCase):
    api = 'v6'

    def setUp(self):
        django.setup()
        
        self.dataset = None
        self.empty_dataset = None
        # Create dataset with basic values
        
    def test_successful_empty(self):
        """Tests successfully calling the dataset details view with no data or results"""

        url = '/%s/datasets/%s/' % (self.api, self.empty_dataset.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        
        # check response for stuff
        result = json.loads(response.content)
        # self.assertEqual(response[''], self.empty_dataset.)

    def test_datasets_id_successful(self):
        """Tests successfully calling the v6/datasets/<dataset_id>/ view.
        """

        url = '/%s/datasets/%d' % (self.api, self.dataset.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset details

    def test_datasets_name_successfull(self):
        """Tests successfully calling the v6/datsets/<dataset-name>/ view.
        """

        url = '/%s/datasets/%d' % (self.api, self.dataset.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        
        # Check response for dataset details
        
