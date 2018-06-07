from __future__ import unicode_literals

import datetime as dt
import json

import django
from django.test import TestCase
from django.utils.timezone import utc
from rest_framework import status

import job.test.utils as job_test_utils
import product.test.utils as product_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util
from storage.models import Workspace


class TestFilesViewV5(TestCase):

    api = 'v5'
    
    def setUp(self):
        django.setup()

        self.f1_file_name = 'foo.bar'
        self.f1_last_modified = dt.datetime(2016, 1, 2, tzinfo=utc)
        self.f1_source_started = dt.datetime(2016, 1, 1, tzinfo=utc)
        self.f1_source_ended = dt.datetime(2016, 1, 2, tzinfo=utc)
        self.file1 = storage_test_utils.create_file(file_name=self.f1_file_name, source_started=self.f1_source_started,
                                                    source_ended=self.f1_source_ended,
                                                    last_modified=self.f1_last_modified)

        self.f2_file_name = 'qaz.bar'
        self.f2_last_modified = dt.datetime(2016, 1, 3, tzinfo=utc)
        self.f2_source_started = dt.datetime(2016, 1, 2, tzinfo=utc)
        self.f2_source_ended = dt.datetime(2016, 1, 3, tzinfo=utc)
        self.file2 = storage_test_utils.create_file(file_name=self.f2_file_name, source_started=self.f2_source_started,
                                                    source_ended=self.f2_source_ended,
                                                    last_modified=self.f2_last_modified)

    def test_file_name_successful(self):
        """Tests successfully calling the get files by name view"""

        url = '/%s/files/?file_name=%s' % (self.api, self.f1_file_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        result = results['results']
        self.assertEqual(len(result), 1)

        self.assertEqual(self.f1_file_name, result[0]['file_name'])
        self.assertEqual('2016-01-01T00:00:00Z', result[0]['source_started'])
        self.assertEqual(self.file1.id, result[0]['id'])

    def test_bad_file_name(self):
        """Tests unsuccessfully calling the get files by name view"""

        url = '/%s/files/?file_name=%s' % (self.api, 'not_a.file')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        result = results['results']
        self.assertEqual(len(result), 0)

    def test_time_successful(self):
        """Tests unsuccessfully calling the get files by name view"""

        url = '/%s/files/?started=%s&ended=%s&time_field=%s' % ( self.api, 
                                                                 '2016-01-01T00:00:00Z',
                                                                 '2016-01-03T00:00:00Z',
                                                                 'source')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file1.id, self.file2.id])
            
class TestFilesViewV6(TestCase):
    api = 'v6'
    
    def setUp(self):
        django.setup()

        self.country = storage_test_utils.create_country()
        self.job_type1 = job_test_utils.create_job_type(name='test1', category='test-1', is_operational=True)
        self.job1 = job_test_utils.create_job(job_type=self.job_type1)
        self.job_exe1 = job_test_utils.create_job_exe(job=self.job1)
        self.product1 = product_test_utils.create_product(job_exe=self.job_exe1, has_been_published=True,
                                                          is_published=True, file_name='test.txt',
                                                          countries=[self.country])

        self.job_type2 = job_test_utils.create_job_type(name='test2', category='test-2', is_operational=False)
        self.job2 = job_test_utils.create_job(job_type=self.job_type2)
        self.job_exe2 = job_test_utils.create_job_exe(job=self.job2)
        self.product2a = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=False, countries=[self.country])


    def test_invalid_started(self):
        """Tests calling the files view when the started parameter is invalid."""

        url = '/%s/files/?started=hello'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the files view when the started parameter is missing timezone."""

        url = '/%s/files/?started=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the files view when the ended parameter is invalid."""

        url = '/%s/files/?started=1970-01-01T00:00:00Z&ended=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the files view when the ended parameter is missing timezone."""

        url = '/%s/files/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the files view with a negative time range."""

        url = '/%s/files/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_job_type_id(self):
        """Tests successfully calling the files view filtered by job type identifier."""

        url = '/%s/files/?job_type_id=%s' % (self.api, self.job_type1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job_type1.id)

    def test_job_type_name(self):
        """Tests successfully calling the files view filtered by job type name."""

        url = '/%s/files/?job_type_name=%s' % (self.api, self.job_type1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job_type1.name)

    def test_is_published(self):
        """Tests successfully calling the files view filtered by is_published flag."""

        url = '/%s/files/?is_published=false' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.product2a.id)
        self.assertFalse(result['results'][0]['is_published'])

    def test_file_name(self):
        """Tests successfully calling the files view filtered by file name."""

        url = '/%s/files/?file_name=test.txt' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.product1.file_name)

    def test_successful(self):
        """Tests successfully calling the files view."""

        url = '/%s/files/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

        for entry in result['results']:
            # Make sure country info is included
            self.assertEqual(entry['countries'][0], self.country.iso3)

class TestFileDetailsViewV6(TestCase):
    api = 'v6'
    
    def setUp(self):
        django.setup()

        self.country = storage_test_utils.create_country()
        self.job_type1 = job_test_utils.create_job_type(name='test1', category='test-1', is_operational=True)
        self.job1 = job_test_utils.create_job(job_type=self.job_type1)
        self.job_exe1 = job_test_utils.create_job_exe(job=self.job1)
        self.file = storage_test_utils.create_file(job_exe=self.job_exe1, file_name='test.txt', countries=[self.country])

    def test_id(self):
        """Tests successfully calling the files detail view by id"""
        
        url = '/%s/files/%i/' % (self.api, self.file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.file.id)
        self.assertEqual(result['file_name'], self.file.file_name)
        self.assertFalse('ancestors' in result)
        self.assertFalse('descendants' in result)
        self.assertFalse('sources' in result)
        self.assertEqual(result['countries'][0], self.country.iso3)
        self.assertEqual(result['file_type'], self.file.file_type)
        self.assertEqual(result['file_path'], self.file.file_path)

    def test_missing(self):
        """Tests calling the file details view with an invalid id"""

        url = '/%s/files/12345/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)



class TestWorkspacesView(TestCase):

    def setUp(self):
        django.setup()

        self.workspace1 = storage_test_utils.create_workspace(name='ws1')
        self.workspace2 = storage_test_utils.create_workspace(name='ws2')

    def test_successful(self):
        """Tests successfully calling the get all workspaces view."""

        url = rest_util.get_url('/workspaces/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.workspace1.id:
                expected = self.workspace1
            elif entry['id'] == self.workspace2.id:
                expected = self.workspace2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['name'], expected.name)
            self.assertEqual(entry['title'], expected.title)

    def test_name(self):
        """Tests successfully calling the workspaces view filtered by workspace name."""

        url = rest_util.get_url('/workspaces/?name=%s' % self.workspace1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)

    def test_sorting(self):
        """Tests custom sorting."""

        url = rest_util.get_url('/workspaces/?order=name')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)
        self.assertEqual(result['results'][0]['title'], self.workspace1.title)

    def test_reverse_sorting(self):
        """Tests custom sorting in reverse."""

        url = rest_util.get_url('/workspaces/?order=-name')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace2.name)
        self.assertEqual(result['results'][0]['title'], self.workspace2.title)


class TestWorkspaceCreateView(TestCase):

    def setUp(self):
        django.setup()

    def test_missing_configuration(self):
        """Tests calling the create Workspace view with missing configuration."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
        }

        url = rest_util.get_url('/workspaces/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests calling the create Workspace view with configuration that is not a dict."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': 123,
        }

        url = rest_util.get_url('/workspaces/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests calling the create Workspace view with invalid configuration."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': {
                'broker': 123,
            }
        }

        url = rest_util.get_url('/workspaces/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the create Workspace view successfully."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'base_url': 'http://host/my/path/',
            'is_active': False,
            'json_config': {
                'broker': {
                    'type': 'host',
                    'host_path': '/host/path',
                },
            },
        }

        url = rest_util.get_url('/workspaces/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        workspaces = Workspace.objects.filter(name='ws-name')
        self.assertEqual(len(workspaces), 1)

        result = json.loads(response.content)
        self.assertEqual(result['title'], workspaces[0].title)
        self.assertEqual(result['description'], workspaces[0].description)
        self.assertDictEqual(result['json_config'], workspaces[0].json_config)
        self.assertEqual(result['base_url'], workspaces[0].base_url)
        self.assertEqual(result['is_active'], workspaces[0].is_active)
        self.assertFalse(workspaces[0].is_active)


class TestWorkspaceDetailsView(TestCase):

    def setUp(self):
        django.setup()

        self.config = {
            'broker': {
                'type': 'host',
                'host_path': '/host/path',
            },
        }

        self.workspace = storage_test_utils.create_workspace(json_config=self.config)

    def test_not_found(self):
        """Tests successfully calling the get workspace details view with a workspace id that does not exist."""

        url = rest_util.get_url('/workspaces/999999/')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get workspace details view."""

        url = rest_util.get_url('/workspaces/%d/' % self.workspace.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.workspace.id)
        self.assertEqual(result['name'], self.workspace.name)
        self.assertEqual(result['title'], self.workspace.title)

    def test_edit_simple(self):
        """Tests editing only the basic attributes of a workspace"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
            'is_active': False,
        }

        url = rest_util.get_url('/workspaces/%d/' % self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.workspace.id)
        self.assertEqual(result['title'], 'Title EDIT')
        self.assertEqual(result['description'], 'Description EDIT')
        self.assertDictEqual(result['json_config'], self.workspace.json_config)
        self.assertFalse(result['is_active'])

        workspace = Workspace.objects.get(pk=self.workspace.id)
        self.assertEqual(workspace.title, 'Title EDIT')
        self.assertEqual(workspace.description, 'Description EDIT')
        self.assertFalse(result['is_active'])

    def test_edit_config(self):
        """Tests editing the configuration of a workspace"""

        config = {
            'version': '1.0',
            'broker': {
                'type': 'nfs',
                'nfs_path': 'host:/dir',
            },
        }

        json_data = {
            'json_config': config,
        }

        url = rest_util.get_url('/workspaces/%d/' % self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.workspace.id)
        self.assertEqual(result['title'], self.workspace.title)
        self.assertDictEqual(result['json_config'], config)

        workspace = Workspace.objects.get(pk=self.workspace.id)
        self.assertEqual(workspace.title, self.workspace.title)
        self.assertDictEqual(workspace.json_config, config)

    def test_edit_bad_config(self):
        """Tests attempting to edit a workspace using an invalid configuration"""

        config = {
            'version': 'BAD',
            'broker': {
                'type': 'nfs',
                'host_path': 'host:/dir',
            },
        }

        json_data = {
            'json_config': config,
        }

        url = rest_util.get_url('/workspaces/%d/' % self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestWorkspacesValidationView(TestCase):
    """Tests related to the workspaces validation endpoint"""

    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests validating a new workspace."""
        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'base_url': 'http://host/my/path/',
            'is_active': False,
            'json_config': {
                'broker': {
                    'type': 'host',
                    'host_path': '/host/path',
                },
            },
        }

        url = rest_util.get_url('/workspaces/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_missing_configuration(self):
        """Tests validating a new workspace with missing configuration."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
        }

        url = rest_util.get_url('/workspaces/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests validating a new workspace with configuration that is not a dict."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': 123,
        }

        url = rest_util.get_url('/workspaces/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests validating a new workspace with invalid configuration."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': {
                'broker': 123,
            },
        }

        url = rest_util.get_url('/workspaces/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_warnings(self):
        """Tests validating a new workspace where the broker type is changed."""

        json_config = {
            'broker': {
                'type': 'host',
                'host_path': '/host/path',
            },
        }
        storage_test_utils.create_workspace(name='ws-test', json_config=json_config)

        json_data = {
            'name': 'ws-test',
            'json_config': {
                'broker': {
                    'type': 'nfs',
                    'nfs_path': 'host:/dir',
                },
            },
        }

        url = rest_util.get_url('/workspaces/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0]['id'], 'broker_type')
