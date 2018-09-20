from __future__ import unicode_literals

import datetime as dt
import json

import django
from django.test import TestCase
from django.utils.timezone import utc
from rest_framework import status

import batch.test.utils as batch_test_utils
import job.test.utils as job_test_utils
import product.test.utils as product_test_utils
import recipe.test.utils as recipe_test_utils
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
        """Tests successfully calling the get files by time"""

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
        self.f1_source_started = dt.datetime(2016, 1, 1, tzinfo=utc)
        self.f1_source_ended = dt.datetime(2016, 1, 2, tzinfo=utc)
        self.source_sensor_class = 'classA'
        self.source_sensor = '1'
        self.source_collection = '12345'
        self.source_task = 'test-task'
        self.file1 = storage_test_utils.create_file(job_exe=self.job_exe1, job_output='out_name',
                                                          file_name='test.txt', countries=[self.country],
                                                          recipe_node='test-recipe-node',
                                                          source_started=self.f1_source_started,
                                                          source_ended=self.f1_source_ended,
                                                          source_sensor_class=self.source_sensor_class,
                                                          source_sensor=self.source_sensor,
                                                          source_collection=self.source_collection,
                                                          source_task=self.source_task)

        self.job_type2 = job_test_utils.create_job_type(name='test2', category='test-2', is_operational=False)
        self.job2 = job_test_utils.create_job(job_type=self.job_type2)
        self.job_exe2 = job_test_utils.create_job_exe(job=self.job2)
        self.f2_source_started = dt.datetime(2016, 1, 2, tzinfo=utc)
        self.f2_source_ended = dt.datetime(2016, 1, 3, tzinfo=utc)
        self.file2 = storage_test_utils.create_file(job_exe=self.job_exe2, countries=[self.country],
                                                          source_started=self.f2_source_started,
                                                          source_ended=self.f2_source_ended)


    def test_invalid_started(self):
        """Tests calling the files view when the started parameter is invalid."""

        url = '/%s/files/?data_started=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the files view when the started parameter is missing timezone."""

        url = '/%s/files/?data_started=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the files view when the ended parameter is invalid."""

        url = '/%s/files/?started=1970-01-01T00:00:00Z&data_ended=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the files view when the ended parameter is missing timezone."""

        url = '/%s/files/?data_started=1970-01-01T00:00:00Z&data_ended=1970-01-02T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the files view with a negative time range."""

        url = '/%s/files/?data_started=1970-01-02T00:00:00Z&data_ended=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        
    def test_source_time_successful(self):
        """Tests successfully calling the get files by source time"""

        url = '/%s/files/?source_started=%s&source_ended=%s' % ( self.api, 
                                                                 '2016-01-01T00:00:00Z',
                                                                 '2016-01-03T00:00:00Z')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file1.id, self.file2.id])

    def test_source_sensor_class(self):
        """Tests successfully calling the files view filtered by source sensor class."""

        url = '/%s/files/?source_sensor_class=%s' % (self.api, self.source_sensor_class)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_sensor_class'], self.source_sensor_class)
        
    def test_source_sensor(self):
        """Tests successfully calling the files view filtered by source sensor."""

        url = '/%s/files/?source_sensor=%s' % (self.api, self.source_sensor)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_sensor'], self.source_sensor)
        
    def test_source_collection(self):
        """Tests successfully calling the files view filtered by source collection."""

        url = '/%s/files/?source_collection=%s' % (self.api, self.source_collection)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_collection'], self.source_collection)
        
    def test_source_task(self):
        """Tests successfully calling the files view filtered by source task."""

        url = '/%s/files/?source_task=%s' % (self.api, self.source_task)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_task'], self.source_task)
        
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

    def test_file_name(self):
        """Tests successfully calling the files view filtered by file name."""

        url = '/%s/files/?file_name=test.txt' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.file1.file_name)
        
    def test_job_output(self):
        """Tests successfully calling the files view filtered by job output."""

        url = '/%s/files/?job_output=out_name' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_output'], self.file1.job_output)
        
    def test_recipe_node(self):
        """Tests successfully calling the files view filtered by recipe job."""

        url = '/%s/files/?recipe_node=test-recipe-node' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['recipe_node'], self.file1.recipe_node)

    def test_successful(self):
        """Tests successfully calling the files view."""

        url = '/%s/files/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

        for entry in result['results']:
            # Make sure country info is included
            self.assertEqual(entry['countries'][0], self.country.iso3)

class TestFileDetailsViewV6(TestCase):
    api = 'v6'
    
    def setUp(self):
        django.setup()

        self.workspace1 = storage_test_utils.create_workspace(name='ws1')
        self.country = storage_test_utils.create_country()
        self.job_type1 = job_test_utils.create_job_type(name='test1', category='test-1', is_operational=True)
        self.job1 = job_test_utils.create_job(job_type=self.job_type1)
        self.job_exe1 = job_test_utils.create_job_exe(job=self.job1)
        self.recipe_type1 = recipe_test_utils.create_recipe_type()
        self.recipe1 = recipe_test_utils.create_recipe(recipe_type=self.recipe_type1)
        self.batch1 = batch_test_utils.create_batch(recipe_type=self.recipe_type1, is_creation_done=True)
        self.file = storage_test_utils.create_file( file_name='test.txt', file_type='SOURCE', media_type='image/png', 
                                                    file_size=1000, data_type='png',  file_path='/test/path', 
                                                    workspace=self.workspace1, is_deleted=False, last_modified='', 
                                                    data_started='2017-01-01T00:00:00Z', data_ended='2017-01-01T00:00:00Z', 
                                                    source_started='2017-01-01T00:00:00Z', source_ended='2017-01-01T00:00:00Z', 
                                                    geometry='', center_point='', meta_data='', countries=[self.country], 
                                                    job_exe=self.job_exe1, job_output='output_name_1', recipe=self.recipe1, 
                                                    recipe_node='my-recipe', batch=self.batch1, 
                                                    is_superseded=True, superseded='2017-01-01T00:00:00Z')

    def test_id(self):
        """Tests successfully calling the files detail view by id"""
        
        url = '/%s/files/%i/' % (self.api, self.file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertFalse('ancestors' in result)
        self.assertFalse('descendants' in result)
        self.assertFalse('sources' in result)
        self.assertEqual(result['id'], self.file.id)
        self.assertEqual(result['file_name'], self.file.file_name)
        self.assertEqual(result['file_type'], self.file.file_type)
        self.assertEqual(result['media_type'], self.file.media_type)
        self.assertEqual(result['file_size'], self.file.file_size)
        self.assertEqual(result['file_path'], self.file.file_path)
        self.assertEqual(result['workspace']['id'], self.file.workspace.id)
        self.assertFalse(result['is_deleted'])
        self.assertEqual(result['data_started'], '2017-01-01T00:00:00Z')
        self.assertEqual(result['data_ended'], '2017-01-01T00:00:00Z')
        self.assertEqual(result['source_started'], '2017-01-01T00:00:00Z')
        self.assertEqual(result['source_ended'], '2017-01-01T00:00:00Z')
        self.assertEqual(result['countries'][0], self.country.iso3)
        self.assertEqual(result['job']['id'], self.job1.id)
        self.assertEqual(result['job_exe']['id'], self.job_exe1.id)
        self.assertEqual(result['job_output'], self.file.job_output)
        self.assertEqual(result['recipe']['id'], self.recipe1.id)
        self.assertEqual(result['recipe_node'], self.file.recipe_node)
        self.assertEqual(result['recipe_type']['id'], self.recipe_type1.id)
        self.assertEqual(result['batch']['title'], self.batch1.title)
        self.assertTrue(result['is_superseded'])
        self.assertEqual(result['superseded'], '2017-01-01T00:00:00Z')

    def test_missing(self):
        """Tests calling the file details view with an invalid id"""

        url = '/%s/files/12345/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)



class TestWorkspacesViewV5(TestCase):

    api = 'v5'

    def setUp(self):
        django.setup()

        self.workspace1 = storage_test_utils.create_workspace(name='ws1')
        self.workspace2 = storage_test_utils.create_workspace(name='ws2')

    def test_successful(self):
        """Tests successfully calling the get all workspaces view."""

        url = '/%s/workspaces/' % self.api
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

        url = '/%s/workspaces/?name=%s' % (self.api, self.workspace1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)

    def test_sorting(self):
        """Tests custom sorting."""

        url = '/%s/workspaces/?order=name' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)
        self.assertEqual(result['results'][0]['title'], self.workspace1.title)

    def test_reverse_sorting(self):
        """Tests custom sorting in reverse."""

        url = '/%s/workspaces/?order=-name' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace2.name)
        self.assertEqual(result['results'][0]['title'], self.workspace2.title)


class TestWorkspacesViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.workspace1 = storage_test_utils.create_workspace(name='ws1')
        self.workspace2 = storage_test_utils.create_workspace(name='ws2')

    def test_successful(self):
        """Tests successfully calling the get all workspaces view."""

        url = '/%s/workspaces/' % self.api
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
            self.assertNotIn('total_size', entry)
            self.assertNotIn('used_size', entry)

    def test_name(self):
        """Tests successfully calling the workspaces view filtered by workspace name."""

        url = '/%s/workspaces/?name=%s' % (self.api, self.workspace1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)

    def test_sorting(self):
        """Tests custom sorting."""

        url = '/%s/workspaces/?order=name' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)
        self.assertEqual(result['results'][0]['title'], self.workspace1.title)
        self.assertNotIn('total_size', result['results'][0])
        self.assertNotIn('used_size', result['results'][0])

    def test_reverse_sorting(self):
        """Tests custom sorting in reverse."""

        url = '/%s/workspaces/?order=-name' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace2.name)
        self.assertEqual(result['results'][0]['title'], self.workspace2.title)
        self.assertNotIn('total_size', result['results'][0])
        self.assertNotIn('used_size', result['results'][0])


class TestWorkspaceCreateViewV5(TestCase):
    api = 'v5'

    def setUp(self):
        django.setup()

    def test_missing_configuration(self):
        """Tests calling the create Workspace view with missing configuration."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
        }

        url = '/%s/workspaces/' % self.api
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

        url = '/%s/workspaces/' % self.api
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

        url = '/%s/workspaces/' % self.api
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

        url = '/%s/workspaces/' % self.api
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


class TestWorkspaceCreateViewV6(TestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

    def test_missing_configuration(self):
        """Tests calling the create Workspace view with missing configuration."""

        json_data = {
            'title': 'Workspace Title',
            'description': 'Workspace description',
        }

        url = '/%s/workspaces/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests calling the create Workspace view with configuration that is not a dict."""

        json_data = {
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': 123,
        }

        url = '/%s/workspaces/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests calling the create Workspace view with invalid configuration."""

        json_data = {
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': {
                'broker': 123,
            }
        }

        url = '/%s/workspaces/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the create Workspace view successfully."""

        json_data = {
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'base_url': 'http://host/my/path/',
            'is_active': False,
            'configuration': {
                'broker': {
                    'type': 'host',
                    'host_path': '/host/path',
                },
            },
        }

        url = '/%s/workspaces/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        workspaces = Workspace.objects.filter(name='workspace-title')
        self.assertEqual(len(workspaces), 1)

        result = json.loads(response.content)
        self.assertEqual(result['name'], 'workspace-title')
        self.assertEqual(result['title'], workspaces[0].title)
        self.assertEqual(result['description'], workspaces[0].description)
        self.assertDictEqual(result['configuration'], workspaces[0].get_v6_configuration_json())
        self.assertEqual(result['base_url'], workspaces[0].base_url)
        self.assertEqual(result['is_active'], workspaces[0].is_active)
        self.assertFalse(workspaces[0].is_active)


class TestWorkspaceDetailsViewV5(TestCase):
    api = 'v5'

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

        url = '/%s/workspaces/999999/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get workspace details view."""

        url = '/%s/workspaces/%d/' % (self.api, self.workspace.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.workspace.id)
        self.assertEqual(result['name'], self.workspace.name)
        self.assertEqual(result['title'], self.workspace.title)
        self.assertIn('archived', result)
        self.assertEqual(result['total_size'], 0)
        self.assertEqual(result['used_size'], 0)

    def test_edit_simple(self):
        """Tests editing only the basic attributes of a workspace"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
            'is_active': False,
        }

        url = '/%s/workspaces/%d/' % (self.api, self.workspace.id)
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

        url = '/%s/workspaces/%d/' % (self.api, self.workspace.id)
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

        url = '/%s/workspaces/%d/' % (self.api, self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestWorkspaceDetailsViewV6(TestCase):
    api = 'v6'

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

        url = '/%s/workspaces/999999/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get workspace details view."""

        url = '/%s/workspaces/%d/' % (self.api, self.workspace.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.workspace.id)
        self.assertEqual(result['name'], self.workspace.name)
        self.assertEqual(result['title'], self.workspace.title)
        self.assertIn('deprecated', result)

    def test_edit_simple(self):
        """Tests editing only the basic attributes of a workspace"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
            'is_active': False,
        }

        url = '/%s/workspaces/%d/' % (self.api, self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)


    def test_edit_config(self):
        """Tests editing the configuration of a workspace"""

        config = {
            'version': '6',
            'broker': {
                'type': 'nfs',
                'nfs_path': 'host:/dir',
            },
        }

        json_data = {
            'configuration': config,
        }

        url = '/%s/workspaces/%d/' % (self.api, self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)


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
            'configuration': config,
        }

        url = '/%s/workspaces/%d/' % (self.api, self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

class TestWorkspacesValidationViewV5(TestCase):
    """Tests related to the workspaces validation endpoint"""

    api = 'v5'

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

        url = '/%s/workspaces/validation/' % self.api
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

        url = '/%s/workspaces/validation/' % self.api
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

        url = '/%s/workspaces/validation/' % self.api
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

        url = '/%s/workspaces/validation/' % self.api
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

        url = '/%s/workspaces/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0]['id'], 'broker_type')


class TestWorkspacesValidationViewV6(TestCase):
    """Tests related to the workspaces validation endpoint"""

    api = 'v6'

    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests validating a new workspace."""
        json_data = {
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'base_url': 'http://host/my/path/',
            'is_active': False,
            'configuration': {
                'broker': {
                    'type': 'host',
                    'host_path': '/host/path',
                },
            },
        }

        url = '/%s/workspaces/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {u'errors': [], u'is_valid': True, u'warnings': []})

    def test_missing_configuration(self):
        """Tests validating a new workspace with missing configuration."""

        json_data = {
            'title': 'Workspace Title',
            'description': 'Workspace description',
        }

        url = '/%s/workspaces/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests validating a new workspace with configuration that is not a dict."""

        json_data = {
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'configuration': 123,
        }

        url = '/%s/workspaces/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests validating a new workspace with invalid configuration."""

        json_data = {
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'configuration': {
                'broker': 123,
            },
        }

        url = '/%s/workspaces/validation/' % self.api
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
            'title': 'ws test',
            'configuration': {
                'broker': {
                    'type': 'nfs',
                    'nfs_path': 'host:/dir',
                },
            },
        }

        url = '/%s/workspaces/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0]['name'], 'broker_type')