""" Tests dataset views methods """
from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime
import json

import django
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase

from data.data.json.data_v6 import DataV6
from data.dataset.json.dataset_v6 import DataSetDefinitionV6
from util import rest

from data.models import DataSet
import data.test.utils as dataset_test_utils
import storage.test.utils as storage_utils
from storage.models import Workspace

"""Tests the v6/datasets/ endpoint"""
class TestDatasetViews(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)
        
        # create a workspace and files
        self.workspace = storage_utils.create_workspace(name='Test Workspace', is_active=True)
                                                  
        self.file1 = storage_utils.create_file(file_name='input_e.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file2 = storage_utils.create_file(file_name='input_f.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file3 = storage_utils.create_file(file_name='input_f2.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file4 = storage_utils.create_file(file_name='input_eb.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file5 = storage_utils.create_file(file_name='input_fb.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)
        self.file6 = storage_utils.create_file(file_name='input_fb2.json', file_type='SOURCE', media_type='application/json',
                                              file_size=10, data_type_tags=['type'], file_path='the_path',
                                              workspace=self.workspace)

        today = now()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)
        
        self.dataset = dataset_test_utils.create_dataset(definition=copy.deepcopy(dataset_test_utils.DATASET_DEFINITION),
            title="Test Dataset 1", description="Key Test Dataset Number one")
        DataSet.objects.filter(pk=self.dataset.pk).update(created=yesterday)
        self.dataset2 = dataset_test_utils.create_dataset(title="Test Dataset 2", description="Test Dataset Number two")
        DataSet.objects.filter(pk=self.dataset2.pk).update(created=tomorrow)
            
        # create dataset members
        data1 = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)
        data1['files']['input_e'] = [self.file1.id]
        data1['files']['input_f'] = [self.file2.id, self.file3.id]

        self.member1_1 = dataset_test_utils.create_dataset_members(dataset=self.dataset, data_list=[data1])[0]

        data2 = copy.deepcopy(dataset_test_utils.DATA_DEFINITION)
        data2['files']['input_e'] = [self.file4.id]
        data2['files']['input_f'] = [self.file5.id, self.file6.id]
        
        self.member1_1_2 = dataset_test_utils.create_dataset_members(dataset=self.dataset, data_list=[data2])
        
        self.member2_1 = dataset_test_utils.create_dataset_members(dataset=self.dataset2)[0]
        self.member2_2 = dataset_test_utils.create_dataset_members(dataset=self.dataset2)[0]

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
            expectedFiles = 0
            if entry['id'] == self.dataset.id:
                expected = self.dataset
                expectedFiles = 6
            elif entry['id'] == self.dataset2.id:
                expected = self.dataset2
                expectedFiles = 0
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['title'], expected.title)
            self.assertEqual(entry['files'], expectedFiles)

    def test_dataset_time_successful(self):
        """Tests successfully calling the v6/datasets api with time filters
        """
        yesterday = now().date() - datetime.timedelta(days=1)
        yesterday = yesterday.isoformat() + 'T00:00:00Z'
        today = now().date()
        today = today.isoformat() + 'T00:00:00Z'
        tomorrow = now().date() + datetime.timedelta(days=1)
        tomorrow = tomorrow.isoformat() + 'T00:00:00Z'
        
        url = '/%s/datasets/?started=%s' % (self.api, today)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        
        url = '/%s/datasets/?ended=%s' % (self.api, today)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        
    def test_dataset_id_successful(self):
        """Tests successfully calling the v6/datasets/?id= api call
        """

        url = '/%s/datasets/?id=%s' % (self.api, self.dataset.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        
        url = '/%s/datasets/?id=%s&id=%s' % (self.api, self.dataset.id, self.dataset2.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify two results
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

    def test_dataset_keyword_successful(self):
        """Tests successfully calling the v6/datasets/?keyword= api call
        """

        url = '/%s/datasets/?keyword=%s' % (self.api, 'key')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify one result
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        
        url = '/%s/datasets/?keyword=%s&keyword=%s' % (self.api, 'one', 'two')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify 2 results
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

    def test_order_by(self):
        """Tests successfully calling the datasets view with sorting."""

        url = '/%s/datasets/?order=-id' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Verify 2 results
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['id'], self.dataset2.id)


"""Tests the v6/datasets POST calls """
class TestDataSetPostView(APITestCase):
    """Tests the v6/dataset/ POST API call"""
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

    def test_invalid_definition(self):
        """Tests successfully calling POST with an invalid definition."""

        json_data = {}
        
        url = '/%s/datasets/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        
        definition = copy.deepcopy(dataset_test_utils.DATASET_DEFINITION)
        del definition['global_data']['json']['input_c']
        json_data = {
            'title': 'My Dataset',
            'description': 'A test dataset',
            'definition': definition,
        }

        url = '/%s/datasets/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_add_dataset(self):
        """Tests adding a new dataset"""

        url = '/%s/datasets/' % self.api

        json_data = {
            'title': 'My Dataset',
            'description': 'A test dataset',
            'definition': copy.deepcopy(dataset_test_utils.DATASET_DEFINITION),
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        result = json.loads(response.content)
        new_dataset_id = result['id']
        self.assertTrue('/%s/datasets/%d/' % (self.api, new_dataset_id) in response['location'])

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
        self.assertTrue('/%s/datasets/%d/' % (self.api, new_dataset_id) in response['location'])

        self.assertEqual(result['title'], json_data_2['title'])
        self.assertEqual(result['description'], json_data_2['description'])

    def test_create_dataset_with_members(self):
        """Tests creating a dataset along with a bunch of members"""

        title = 'Test Dataset'
        description = 'Test DataSet description'

        file1 = storage_utils.create_file()
        file2 = storage_utils.create_file()
        file3 = storage_utils.create_file()
        file4 = storage_utils.create_file()

        # call test
        parameters = {'version': '6',
                      'files': [
                          {'name': 'input_a',
                           'media_types': ['application/json'],
                           'required': True},
                          {'name': 'input_b',
                           'media_types': ['application/json'],
                           'multiple': True,
                           'required': True},
                          {'name': 'input_c',
                           'media_types': ['application/json'],
                           'required': True}
                      ],
                      'json': []}
        definition = {'version': '6', 'parameters': parameters}

        json_data = {
            'title': title,
            'description': description,
            'definition': definition,
            'data': {
                'version': '7',
                'files': {
                    'input_a': [file1.id],
                    'input_b': [file2.id, file3.id],
                    'input_c': [file4.id],
                },
                'json': {}
            },
        }
        url = '/%s/datasets/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        result = json.loads(response.content)
        new_dataset_id = result['id']
        self.assertTrue('/%s/datasets/%d/' % (self.api, new_dataset_id) in response['location'])
        self.assertTrue(len(result['definition']['parameters']['files']), 3)
        self.assertTrue(len(result['files']), 4)

"""Tests the v6/datasets/<dataset_id> endpoint"""
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
                                              
        for i in range(0,500):
            storage_utils.create_file(source_collection='12345')
            
        for i in range(0,500):
            storage_utils.create_file(source_collection='123456')

        # Create datasets
        parameters = {'version': '6',
                      'files': [
                          {'name': 'input_a',
                           'media_types': ['application/json'],
                           'required': True}
                      ],
                      'json': []}
        definition = {'version': '6', 'parameters': parameters}
        self.dataset = dataset_test_utils.create_dataset( title="Test Dataset 1",
                                                          description="Test Dataset Number 1",
                                                          definition=definition)

        parameters2 = {'version': '6',
                      'files': [
                          {'name': 'input_b',
                           'media_types': ['application/json'],
                           'required': True,
                           'multiple': True},
                          {'name': 'input_c',
                           'media_types': ['application/json'],
                           'required': False}
                      ],
                      'json': []}
        definition2 = {'version': '6', 'parameters': parameters2}
        self.dataset2 = dataset_test_utils.create_dataset(title="Test Dataset 2",
                                                          description="Test Dataset Number 2",
                                                          definition=definition2)

        # Create members
        data_dict = {
            'version': '6',
            'files': {'input_a': [self.src_file_a.id]},
            'json': {}
        }
        data = DataV6(data=data_dict).get_dict()
        self.member_a = dataset_test_utils.create_dataset_members(dataset=self.dataset,
            data_list=[data])[0]

        data_dict = {
            'version': '6',
            'files': {'input_b': [self.src_file_b.id, self.src_file_b2.id]},
            'json': {}
        }
        data2 = DataV6(data=data_dict).get_dict()
        self.member_b = dataset_test_utils.create_dataset_members(dataset=self.dataset2,
            data_list=[data2])[0]

        data_dict = {
            'version': '6',
            'files': {'input_b': [self.src_file_b.id, self.src_file_b2.id], 'input_c': [self.src_file_c.id]},
            'json': {}
        }
        data3 = DataV6(data=data_dict).get_dict()
        self.member_bc = dataset_test_utils.create_dataset_members(dataset=self.dataset2,
            data_list=[data3])[0]

    def test_dataset_details_successful(self):
        """Tests successfully calling the v6/datasets/<dataset_id>/ view.
        """

        url = '/%s/datasets/%d/' % (self.api, self.dataset.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset details
        result = json.loads(response.content)
        self.assertEqual(result['id'], self.dataset.id)
        self.assertEqual(result['title'], self.dataset.title)
        self.assertEqual(result['description'], self.dataset.description)
        dsdict = DataSetDefinitionV6(definition=self.dataset.definition).get_dict()
        del dsdict['version']
        self.assertDictEqual(result['definition'], dsdict)
        self.assertEqual(len(result['files']), 1)

        url = '/%s/datasets/%d/' % (self.api, self.dataset2.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset details
        result = json.loads(response.content)
        self.assertEqual(result['id'], self.dataset2.id)
        self.assertEqual(result['title'], self.dataset2.title)
        self.assertEqual(result['description'], self.dataset2.description)
        self.maxDiff = None
        dsdict = DataSetDefinitionV6(definition=self.dataset2.definition).get_dict()
        del dsdict['version']
        self.assertDictEqual(result['definition'], self.dataset2.definition)
        self.assertEqual(len(result['files']), 3)

    def test_add_dataset_member(self):
        """Tests adding a new dataset member"""

        url = '/%s/datasets/%d/' % (self.api, self.dataset.id)
        
        data_dict = {
            'version': '6',
            'files': {'input_a': [self.src_file_a.id]},
            'json': {}
        }

        json_data = {
            'data': [data_dict],
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result), 1)

    def test_add_filter_dataset_members(self):
        """Tests adding new dataset members based on a filter"""

        url = '/%s/datasets/%d/' % (self.api, self.dataset.id)
        
        template = {
            'version': '6',
            'files': {'input_a': 'FILE_VALUE'},
            'json': {}
        }

        json_data = {
            'data_template': template,
            'source_collection': '12345'
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result), 500)
        
        json_data = {
            'data_template': template,
            'source_collection': ['12345', '123456']
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result), 1000)
        
    def test_add_filter_dataset_members_dry_run(self):
        """Tests adding new dataset members based on a filter"""

        url = '/%s/datasets/%d/' % (self.api, self.dataset.id)
        
        template = {
            'version': '6',
            'files': {'input_a': 'FILE_VALUE'},
            'json': {}
        }

        json_data = {
            'data_template': template,
            'source_collection': '12345',
            'dry_run': True
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result), 500)
        
    def test_add_invalid_dataset_member(self):
        """Tests adding an invalid new dataset member"""

        url = '/%s/datasets/%d/' % (self.api, self.dataset.id)
        
        data_dict = {
            'version': '6',
            'files': {'input_b': [self.src_file_a.id]},
            'json': {}
        }

        json_data = {
            'data': [data_dict],
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        
class TestDataSetValidationView(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

    def test_validate_successful(self):
        """Tests successfully validating a new dataset using the v6/datasets/validation API
        """

        url = '/%s/datasets/validation/' % self.api

        json_data = {
            'title': 'Test Dataset',
            'description': 'My Test Dataset',
            'definition': dataset_test_utils.DATASET_DEFINITION,
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
            'title': 'Test Dataset',
            'description': 'My Test Dataset',
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['detail'], "Missing required parameter: \"definition\"")

    def test_invalid_definition(self):
        """Validates an invalid dataset definition
        """

        url = '/%s/datasets/validation/' % self.api

        json_data = {
            'title': 'Test Dataset',
            'description': 'My Test Dataset',
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

"""Tests the v6/datasets/%d/members/ endpoint"""
class TestDatasetMembersView(APITestCase):
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
                           'required': True}
                      ],
                      'json': []}
        definition = {'version': '6', 'parameters': parameters}
        self.dataset = dataset_test_utils.create_dataset( title="Test Dataset 1",
                                                          description="Test Dataset Number 1",
                                                          definition=definition)

        parameters2 = {'version': '6',
                      'files': [
                          {'name': 'input_b',
                           'media_types': ['application/json'],
                           'required': True,
                           'multiple': True},
                          {'name': 'input_c',
                           'media_types': ['application/json'],
                           'required': False}
                      ],
                      'json': []}
        definition2 = {'version': '6', 'parameters': parameters2}
        self.dataset2 = dataset_test_utils.create_dataset(title="Test Dataset 2",
                                                          description="Test Dataset Number 2",
                                                          definition=definition2)

        # Create members
        data_dict = {
            'version': '6',
            'files': {'input_a': [self.src_file_a.id]},
            'json': {}
        }
        data = DataV6(data=data_dict).get_dict()
        self.member_a = dataset_test_utils.create_dataset_members(dataset=self.dataset,
            data_list=[data])[0]

        data_dict = {
            'version': '6',
            'files': {'input_b': [self.src_file_b.id, self.src_file_b2.id]},
            'json': {}
        }
        data2 = DataV6(data=data_dict).get_dict()
        self.member_b = dataset_test_utils.create_dataset_members(dataset=self.dataset2,
            data_list=[data2])[0]

        data_dict = {
            'version': '6',
            'files': {'input_b': [self.src_file_b.id, self.src_file_b2.id], 'input_c': [self.src_file_c.id]},
            'json': {}
        }
        data3 = DataV6(data=data_dict).get_dict()
        self.member_bc = dataset_test_utils.create_dataset_members(dataset=self.dataset2,
            data_list=[data3])[0]

    def test_dataset_members_successful(self):
        """Tests successfully calling the v6/datasets/members/<id>/ view.
        """

        url = '/%s/datasets/%d/members/' % (self.api, self.dataset.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset members
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        url = '/%s/datasets/%d/members/' % (self.api, self.dataset2.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset members
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)


"""Tests the v6/datasets/members/<datasetmember_id> endpoint"""
class TestDatasetMemberDetailsView(APITestCase):
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
                           'required': True}
                      ],
                      'json': []}
        definition = {'version': '6', 'parameters': parameters}
        self.dataset = dataset_test_utils.create_dataset( title="Test Dataset 1",
                                                          description="Test Dataset Number 1",
                                                          definition=definition)

        parameters2 = {'version': '6',
                      'files': [
                          {'name': 'input_b',
                           'media_types': ['application/json'],
                           'required': True,
                           'multiple': True},
                          {'name': 'input_c',
                           'media_types': ['application/json'],
                           'required': False}
                      ],
                      'json': []}
        definition2 = {'version': '6', 'parameters': parameters2}
        self.dataset2 = dataset_test_utils.create_dataset(title="Test Dataset 2",
                                                          description="Test Dataset Number 2",
                                                          definition=definition2)

        # Create members
        data_dict = {
            'version': '6',
            'files': {'input_a': [self.src_file_a.id]},
            'json': {}
        }
        data = DataV6(data=data_dict).get_dict()
        self.member_a = dataset_test_utils.create_dataset_members(dataset=self.dataset,
            data_list=[data])[0]

        data_dict = {
            'version': '6',
            'files': {'input_b': [self.src_file_b.id, self.src_file_b2.id]},
            'json': {}
        }
        data2 = DataV6(data=data_dict).get_dict()
        self.member_b = dataset_test_utils.create_dataset_members(dataset=self.dataset2,
            data_list=[data2])[0]

        data_dict = {
            'version': '6',
            'files': {'input_b': [self.src_file_b.id, self.src_file_b2.id], 'input_c': [self.src_file_c.id]},
            'json': {}
        }
        data3 = DataV6(data=data_dict).get_dict()
        self.member_bc = dataset_test_utils.create_dataset_members(dataset=self.dataset2,
            data_list=[data3])[0]

    def test_dataset_member_details_successful(self):
        """Tests successfully calling the v6/datasets/members/<id>/ view.
        """

        url = '/%s/datasets/members/%d/' % (self.api, self.member_a.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset details
        result = json.loads(response.content)
        self.assertEqual(result['id'], self.member_a.id)
        self.assertEqual(result['dataset']['id'], self.dataset.id)
        versionless = copy.deepcopy(self.member_a.data)
        del versionless['version']
        self.assertDictEqual(result['data'], versionless)

        url = '/%s/datasets/members/%d/' % (self.api, self.member_b.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset details
        result = json.loads(response.content)
        self.assertEqual(result['id'], self.member_b.id)
        self.assertEqual(result['dataset']['id'], self.dataset2.id)
        versionless = copy.deepcopy(self.member_b.data)
        del versionless['version']
        self.assertDictEqual(result['data'], versionless)

        url = '/%s/datasets/members/%d/' % (self.api, self.member_bc.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        # Check response for dataset details
        result = json.loads(response.content)
        self.assertEqual(result['id'], self.member_bc.id)
        self.assertEqual(result['dataset']['id'], self.dataset2.id)
        versionless = copy.deepcopy(self.member_bc.data)
        del versionless['version']
        self.assertDictEqual(result['data'], versionless)