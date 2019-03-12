from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime
import json
import time

import django
from django.test import TestCase, TransactionTestCase
from django.utils.timezone import utc, now
from mock import patch
from rest_framework import status

import batch.test.utils as batch_test_utils
import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import node.test.utils as node_test_utils
import storage.test.utils as storage_test_utils
import recipe.test.utils as recipe_test_utils
import trigger.test.utils as trigger_test_utils
import source.test.utils as source_test_utils
from error.models import Error
from job.messages.cancel_jobs_bulk import CancelJobsBulk
from job.models import Job, JobType
from queue.messages.requeue_jobs_bulk import RequeueJobsBulk
from recipe.models import RecipeType
from util.parse import datetime_to_string
from vault.secrets_handler import SecretsHandler
import util.rest as rest_util


class TestJobsViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.date_1 = datetime.datetime(2016, 1, 1, tzinfo=utc)
        self.date_2 = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.date_3 = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.date_4 = datetime.datetime(2016, 1, 3, tzinfo=utc)
        self.s_class = 'A'
        self.s_sensor = '1'
        self.collection = '12345'
        self.task = 'abcd'
        self.s_class2 = 'B'
        self.s_sensor2 = '2'
        self.collection2 = '123456'
        self.task2 = 'abcde'

        self.workspace = storage_test_utils.create_workspace()
        self.file_1 = storage_test_utils.create_file(workspace=self.workspace, file_size=104857600.0,
                                                source_started=self.date_1, source_ended=self.date_2,
                                                source_sensor_class=self.s_class, source_sensor=self.s_sensor,
                                                source_collection=self.collection, source_task=self.task)
        self.file_2 = storage_test_utils.create_file(workspace=self.workspace, file_size=0.154,
                                                 source_started=self.date_3, source_ended=self.date_4,
                                                 source_sensor_class=self.s_class2, source_sensor=self.s_sensor2,
                                                 source_collection=self.collection2, source_task=self.task2)

        self.data_1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'INPUT_FILE',
                'file_id': self.file_1.id
            }],
            'output_data': [{
                'name': 'output_file_pngs',
                'workspace_id': self.workspace.id
            }]}
        self.data_2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'INPUT_FILE',
                'file_id': self.file_2.id
            }],
            'output_data': [{
                'name': 'output_file_pngs',
                'workspace_id': self.workspace.id
            }]}

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'scale-batch-creator'
        self.job_type1 = job_test_utils.create_seed_job_type(manifest=manifest)
        self.job1 = job_test_utils.create_job(job_type=self.job_type1, status='RUNNING', input=self.data_1, input_file_size=None)

        manifest2 = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest2['job']['name'] = 'test2'
        self.job_type2 = job_test_utils.create_seed_job_type(manifest=manifest2)
        self.job2 = job_test_utils.create_job(job_type=self.job_type2, status='PENDING', input=self.data_2, input_file_size=None)

        Job.objects.process_job_input(self.job1)
        Job.objects.process_job_input(self.job2)

        self.job3 = job_test_utils.create_job(is_superseded=True)

    def test_successful(self):
        """Tests successfully calling the jobs view."""

        url = '/%s/jobs/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.job1.id:
                expected = self.job1
            elif entry['id'] == self.job2.id:
                expected = self.job2
            elif entry['id'] == self.job3.id:
                expected = self.job3
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['job_type']['name'], expected.job_type.name)
            self.assertEqual(entry['job_type_rev']['job_type']['id'], expected.job_type.id)
            self.assertEqual(entry['is_superseded'], expected.is_superseded)

    def test_jobs_successful(self):
        """ Tests the v6/jobs/<job_id>/ api call for success
        """

        workspace = storage_test_utils.create_workspace()
        file1 = storage_test_utils.create_file()
        data_dict = {
            'version': '1.0',
            'input_data': [{
                'name': 'INPUT_IMAGE',
                'file_id': file1.id
            }],
            'output_data': [{
                'name': 'output_file_pngs',
                'workspace_id': workspace.id
        }]}
        seed_job_type = job_test_utils.create_seed_job_type()
        seed_job = job_test_utils.create_job(job_type=seed_job_type, status='RUNNING', input=data_dict)

        url = '/%s/jobs/%d/' % (self.api, seed_job.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_source_time_successful(self):
        """Tests successfully calling the get jobs by source time"""

        url = '/%s/jobs/?source_started=%s&source_ended=%s' % ( self.api,
                                                                 '2016-01-01T00:00:00Z',
                                                                 '2016-01-02T00:00:00Z')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 1)
        for result in results:
            self.assertTrue(result['id'] in [self.job1.id])

    def test_source_sensor_class(self):
        """Tests successfully calling the jobs view filtered by source sensor class."""

        url = '/%s/jobs/?source_sensor_class=%s' % (self.api, self.s_class)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_sensor_class'], self.s_class)

    def test_source_sensor(self):
        """Tests successfully calling the jobs view filtered by source sensor."""

        url = '/%s/jobs/?source_sensor=%s' % (self.api, self.s_sensor)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_sensor'], self.s_sensor)

    def test_source_collection(self):
        """Tests successfully calling the jobs view filtered by source collection."""

        url = '/%s/jobs/?source_collection=%s' % (self.api, self.collection)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_collection'], self.collection)

    def test_source_task(self):
        """Tests successfully calling the jobs view filtered by source task."""

        url = '/%s/jobs/?source_task=%s' % (self.api, self.task)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['source_task'], self.task)

    def test_status(self):
        """Tests successfully calling the jobs view filtered by status."""

        url = '/%s/jobs/?status=RUNNING' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job1.job_type.id)

    def test_job_id(self):
        """Tests successfully calling the jobs view filtered by job identifier."""

        url = '/%s/jobs/?job_id=%s' % (self.api, self.job1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job1.id)

    def test_job_type_id(self):
        """Tests successfully calling the jobs view filtered by job type identifier."""

        url = '/%s/jobs/?job_type_id=%s' % (self.api, self.job1.job_type.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job1.job_type.id)

    def test_job_type_name(self):
        """Tests successfully calling the jobs view filtered by job type name."""

        url = '/%s/jobs/?job_type_name=%s' % (self.api, self.job1.job_type.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job1.job_type.name)


    def test_error_category(self):
        """Tests successfully calling the jobs view filtered by error category."""

        error = error_test_utils.create_error(category='DATA')
        job = job_test_utils.create_job(error=error)

        url = '/%s/jobs/?error_category=%s' % (self.api, error.category)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], job.id)
        self.assertEqual(result['results'][0]['error']['category'], error.category)

    def test_error_id(self):
        """Tests successfully calling the jobs view filtered by error id."""

        error = error_test_utils.create_error(category='DATA')
        job = job_test_utils.create_job(error=error)

        url = '/%s/jobs/?error_id=%d' % (self.api, error.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], job.id)
        self.assertEqual(result['results'][0]['error']['id'], error.id)

    def test_superseded(self):
        """Tests getting superseded jobs."""

        url = '/%s/jobs/?is_superseded=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

    def test_batch(self):
        """Tests filtering jobs by batch"""
        batch = batch_test_utils.create_batch()
        self.job1.batch_id = batch.id
        self.job1.save()

        url = '/%s/jobs/?batch_id=%d' % (self.api, batch.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job1.id)

    def test_recipe(self):
        """Tests filtering jobs by recipe"""
        recipe = recipe_test_utils.create_recipe()
        self.job1.recipe_id = recipe.id
        self.job1.save()

        url = '/%s/jobs/?recipe_id=%d' % (self.api, recipe.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job1.id)

    def test_order_by(self):
        """Tests successfully calling the jobs view with sorting."""
        # May fail because of job_type name ordering
        job_type1b = job_test_utils.create_seed_job_type(job_version='2.0')
        job_test_utils.create_job(job_type=job_type1b, status='RUNNING')

        job_type1c = job_test_utils.create_seed_job_type(job_version='3.0')
        job_test_utils.create_job(job_type=job_type1c, status='RUNNING')

        url = '/%s/jobs/?is_superseded=false&order=job_type__name&order=-job_type__version' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)

        self.assertEqual(len(result['results']), 4)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job_type1.id)
        self.assertEqual(result['results'][1]['job_type']['id'], job_type1b.id)
        self.assertEqual(result['results'][2]['job_type']['id'], job_type1c.id)
        self.assertEqual(result['results'][3]['job_type']['id'], self.job_type2.id)


class TestJobsPostViewV6(TestCase):

    api = "v6"

    def setUp(self):
        django.setup()

        manifest = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'test-job',
                'jobVersion': '1.0.0',
                'packageVersion': '1.0.0',
                'title': 'Test Job',
                'description': 'This is a test job',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 10,
                'interface': {
                    'command': '',
                    'inputs': {
                        'files': [{'name': 'input_a'}]
                    },
                    'outputs': {
                        'files': [{'name': 'output_a', 'multiple': True, 'pattern': '*.png'}]
                    }
                }
            }
        }

        self.output_workspace = storage_test_utils.create_workspace()

        self.configuration = {
            'version': '6',
            'output_workspaces': {'default': self.output_workspace.name},
            'priority': 999
        }

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=manifest)
        self.workspace = storage_test_utils.create_workspace()
        self.source_file = source_test_utils.create_source(workspace=self.workspace)

    @patch('queue.models.CommandMessageManager')
    @patch('queue.models.create_process_job_input_messages')
    def test_successful(self, mock_create, mock_msg_mgr):
        """Tests successfully calling POST jobs view to queue a new job"""

        json_data = {
            "input" : {
                'version': '6',
                'files': {'input_a': [self.source_file.id]},
                'json': {}
            },
            "job_type_id" : self.job_type1.pk
        }

        url = '/%s/jobs/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)

        #Response should be new v6 job detail response
        self.assertEqual(result['execution'], None)
        self.assertTrue('/%s/jobs/' % self.api in response['location'])
        mock_create.assert_called_once()

    @patch('queue.models.CommandMessageManager')
    @patch('queue.models.create_process_job_input_messages')
    def test_successful_configuration(self, mock_create, mock_msg_mgr):
        """Tests successfully calling POST jobs view to queue a new job with a job type configuration"""

        json_data = {
            "input" : {
                'version': '6',
                'files': {'input_a': [self.source_file.id]},
                'json': {}
            },
            "job_type_id" : self.job_type1.pk,
            "configuration" : self.configuration
        }

        url = '/%s/jobs/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)

        #Response should be new v6 job detail response
        self.assertEqual(result['execution'], None)
        self.assertTrue('/%s/jobs/' % self.api in response['location'])
        mock_create.assert_called_once()

    def test_invalid_data(self):
        """Tests successfully calling POST jobs view to queue a new job with invalid input data"""

        json_data = {
            "input" : {
                'version': 'BAD',
                'files': {'input_a': [self.source_file.id]},
                'json': {}
            },
            "job_type_id" : self.job_type1.pk,
            "configuration" : self.configuration
        }

        url = '/%s/jobs/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests successfully calling POST jobs view to queue a new job with a job type configuration"""

        config = copy.deepcopy(self.configuration)
        config['version'] = 'BAD'
        json_data = {
            "input" : {
                'version': '6',
                'files': {'input_a': [self.source_file.id]},
                'json': {}
            },
            "job_type_id" : self.job_type1.pk,
            "configuration" : config
        }

        url = '/%s/jobs/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestJobDetailsViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.country = storage_test_utils.create_country()
        self.file = storage_test_utils.create_file(countries=[self.country])

        job_data = {
            'input_data': []
        }
        job_results = {
            'output_data': []
        }
        self.job_type = job_test_utils.create_seed_job_type()
        self.job = job_test_utils.create_job(job_type=self.job_type, input=job_data, output=job_results, status='RUNNING')

        # Attempt to stage related models
        self.job_exe = job_test_utils.create_job_exe(job=self.job)

        try:
            import recipe.test.utils as recipe_test_utils
            definition = {
                'version': '1.0',
                'input_data': [{
                    'name': 'Recipe Input',
                    'type': 'file',
                    'media_types': ['text/plain'],
                }],
                'jobs': [{
                    'name': 'Job 1',
                    'job_type': {
                        'name': self.job_type.name,
                        'version': self.job_type.version,
                    },
                    'recipe_inputs': [{
                        'recipe_input': 'Recipe Input',
                        'job_input': 'input_files',
                    }]
                }]
            }
            self.recipe_type = recipe_test_utils.create_recipe_type_v6(definition=definition)
            self.recipe = recipe_test_utils.create_recipe(recipe_type=self.recipe_type)
            self.recipe_job = recipe_test_utils.create_recipe_job(recipe=self.recipe, job=self.job, job_name='Job 1')
        except:
            self.recipe_type = None
            self.recipe = None
            self.recipe_job = None

        try:
            import product.test.utils as product_test_utils
            self.product = product_test_utils.create_product(job_exe=self.job_exe, countries=[self.country])
        except:
            self.product = None

    def test_successful_empty(self):
        """Tests successfully calling the job details view with no data or results."""

        url = '/%s/jobs/%i/' % (self.api, self.job.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['job_type']['name'], self.job.job_type.name)
        self.assertEqual(result['job_type_rev']['job_type']['name'], self.job.job_type.name)

        if self.recipe:
            self.assertEqual(result['recipe']['recipe_type']['name'], self.recipe.recipe_type.name)
        else:
            self.assertEqual(len(result['recipe']), 0)

    def test_successful_execution(self):
        """Tests successfully calling the job details view and checking the execution response."""

        url = '/%s/jobs/%i/' % (self.api, self.job.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)

        self.assertEqual(result['execution']['job']['id'], self.job.id)
        self.assertEqual(result['execution']['job_type']['id'], self.job_type.id)
        self.assertEqual(result['execution']['exe_num'], self.job_exe.exe_num)

    def test_successful_resources(self):
        """Tests successfully calling the job details view for resources."""

        url = '/%s/jobs/%i/' % (self.api, self.job.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)

        self.assertEqual(result['resources']['resources']['cpus'], 1.0)
        self.assertEqual(result['resources']['resources']['mem'], 128.0)
        self.assertEqual(result['resources']['resources']['disk'], 10.0)

    def test_superseded(self):
        """Tests successfully calling the job details view for superseded jobs."""

        job_data = {
            'input_data': []
        }
        job_results = {
            'output_data': []
        }
        new_job = job_test_utils.create_job(job_type=self.job_type, input=job_data, output=job_results,
                                            superseded_job=self.job)

        # Make sure the original job was updated
        url = '/%s/jobs/%i/' % (self.api, self.job.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(result['is_superseded'])
        self.assertIsNotNone(result['superseded_by_job'])
        self.assertEqual(result['superseded_by_job']['id'], new_job.id)
        self.assertIsNotNone(result['superseded'])

        # Make sure the new new job has the expected relations
        url = '/%s/jobs/%i/' % (self.api, new_job.id)
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertFalse(result['is_superseded'])
        self.assertIsNotNone(result['superseded_job'])
        self.assertEqual(result['superseded_job']['id'], self.job.id)
        self.assertIsNone(result['superseded'])

class TestJobTypesViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.error = error_test_utils.create_error()
        manifest4 = job_test_utils.create_seed_manifest(name="job-type-for-view-test", jobVersion="1.0.0")
        manifest5 = job_test_utils.create_seed_manifest(name="job-type-for-view-test", jobVersion="1.2.0")
        manifest6 = job_test_utils.create_seed_manifest(name="job-type-for-view-test", jobVersion="1.10.0")
        self.job_type1 = job_test_utils.create_seed_job_type(job_version="1.0.0", priority=2, max_scheduled=1)
        self.job_type2 = job_test_utils.create_seed_job_type(job_version="1.0.0", priority=1, is_system=True)
        self.job_type3 = job_test_utils.create_seed_job_type(job_version="1.0.0", priority=1, is_active=False)
        self.job_type4 = job_test_utils.create_seed_job_type(manifest=manifest4, is_active=False)
        self.job_type5 = job_test_utils.create_seed_job_type(manifest=manifest5, is_active=True)
        self.job_type6 = job_test_utils.create_seed_job_type(manifest=manifest6, is_active=True)

    def test_successful(self):
        """Tests successfully calling the get all job types view."""

        url = '/%s/job-types/' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)
        for entry in result['results']:
            expected = None
            if entry['name'] == self.job_type1.name:
                expected = self.job_type1
            elif entry['name'] == self.job_type2.name:
                expected = self.job_type2
            elif entry['name'] == self.job_type3.name:
                expected = self.job_type3
            elif entry['name'] == self.job_type6.name:
                expected = self.job_type6
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['name'], expected.name)
            self.assertEqual(entry['title'], expected.title)
            self.assertEqual(entry['description'], expected.description)
            if entry['name'] == 'job-type-for-view-test':
                self.assertItemsEqual(entry['versions'], ["1.0.0", "1.2.0", "1.10.0"])
            else:
                self.assertItemsEqual(entry['versions'], ["1.0.0"])
            self.assertEqual(entry['latest_version'], expected.version)

    def test_keyword(self):
        """Tests successfully calling the job types view filtered by keyword."""

        url = '/%s/job-types/?keyword=%s' % (self.api, self.job_type1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.job_type1.name)

        url = '/%s/job-types/?keyword=%s' % (self.api, 'job-type')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)

        url = '/%s/job-types/?keyword=%s' % (self.api, 'job-type-for-view-test')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['latest_version'], '1.10.0')

        url = '/%s/job-types/?keyword=%s&keyword=%s' % (self.api, 'job-type-for-view-test', self.job_type1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

    def test_id(self):
        """Tests successfully calling the job types view filtered by id."""

        url = '/%s/job-types/?id=%d' % (self.api, self.job_type1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.job_type1.name)

        url = '/%s/job-types/?id=%d&id=%d' % (self.api, self.job_type1.id, self.job_type2.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

        url = '/%s/job-types/?id=%d&id=%d' % (self.api, self.job_type4.id, self.job_type5.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

    def test_is_active(self):
        """Tests successfully calling the job types view filtered by inactive state."""

        url = '/%s/job-types/?is_active=false' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

    def test_is_system(self):
        """Tests successfully calling the job types view filtered by system status."""

        url = '/%s/job-types/?is_system=false' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

        url = '/%s/job-types/?is_system=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

    def test_version_successful(self):
        """Tests successfully calling the job type versions view."""

        url = '/%s/job-types/job-type-for-view-test/' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.job_type4.id:
                expected = self.job_type4
            elif entry['id'] == self.job_type5.id:
                expected = self.job_type5
            elif entry['id'] == self.job_type6.id:
                expected = self.job_type6
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['name'], expected.name)
            self.assertEqual(entry['version'], expected.version)
            self.assertEqual(entry['title'], expected.title)
            self.assertEqual(entry['description'], expected.description)
            self.assertEqual(entry['icon_code'], expected.icon_code)
            self.assertEqual(entry['is_published'], expected.is_published)
            self.assertEqual(entry['is_active'], expected.is_active)
            self.assertEqual(entry['is_paused'], expected.is_paused)
            self.assertEqual(entry['is_system'], expected.is_system)
            self.assertEqual(entry['max_scheduled'], expected.max_scheduled)
            self.assertEqual(entry['revision_num'], expected.revision_num)
            self.assertEqual(entry['docker_image'], expected.docker_image)

    def test_version_is_active(self):
        """Tests successfully calling the job type versions view filtered by inactive state."""

        url = '/%s/job-types/job-type-for-view-test/?is_active=false' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)


class TestJobTypesPostViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.manifest = job_test_utils.COMPLETE_MANIFEST

        self.interface = {
            'version': '1.4',
            'command': 'test_cmd',
            'command_arguments': 'test_arg',
            'env_vars': [],
            'mounts': [{
                'name': 'dted',
                'path': '/some/path',
                'required': True,
                'mode': 'ro'
            }],
            'settings': [{
                'name': 'DB_HOST',
                'required': True,
                'secret': False,
            }],
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }

        self.output_workspace = storage_test_utils.create_workspace()
        self.configuration = {
            'version': '6',
            'mounts': {
                'MOUNT_PATH': {
                    'type': 'host',
                    'host_path': '/path/to/dted',
                    },
            },
            'output_workspaces': {'default': self.output_workspace.name},
            'settings': {
                'DB_HOST': 'scale',
            },
        }

        self.workspace = storage_test_utils.create_workspace()
        self.trigger_config = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
            },
            'data': {
                'input_data_name': 'input_file',
                'workspace_name': self.workspace.name,
            }
        }
        # self.trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type='PARSE', is_active=True,
        #                                                           configuration=self.trigger_config)

        self.job_type = job_test_utils.create_seed_job_type(manifest=self.manifest, max_scheduled=2,
                                                            configuration=self.configuration)

        self.error = error_test_utils.create_error(category='ALGORITHM')
        self.error_mapping = {
            'version': '1.0',
            'exit_codes': {
                '1': self.error.name,
            }
        }

        self.job_type1 = job_test_utils.create_seed_job_type(manifest=job_test_utils.MINIMUM_MANIFEST)
        self.job_type2 = job_test_utils.create_seed_job_type()

        self.sub_definition = copy.deepcopy(recipe_test_utils.SUB_RECIPE_DEFINITION)
        self.sub_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type1.name
        self.sub_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type1.version
        self.sub_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type1.revision_num

        self.recipe_type1 = recipe_test_utils.create_recipe_type_v6(definition=self.sub_definition,
                                                                    description="A sub recipe",
                                                                    is_active=False,
                                                                    is_system=False)

        self.main_definition = copy.deepcopy(recipe_test_utils.RECIPE_DEFINITION)
        self.main_definition['nodes']['node_a']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_a']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_a']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_b']['node_type']['job_type_name'] = self.job_type2.name
        self.main_definition['nodes']['node_b']['node_type']['job_type_version'] = self.job_type2.version
        self.main_definition['nodes']['node_b']['node_type']['job_type_revision'] = self.job_type2.revision_num
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_name'] = self.recipe_type1.name
        self.main_definition['nodes']['node_c']['node_type']['recipe_type_revision'] = self.recipe_type1.revision_num

        self.recipe_type2 = recipe_test_utils.create_recipe_type_v6(definition=self.main_definition,
                                                                    title="My main recipe",
                                                                    is_active=True,
                                                                    is_system=True)

    def test_add_seed_job_type(self):
        """Tests adding a seed image."""

        url = '/%s/job-types/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'my-new-job'

        json_data = {
            'icon_code': 'BEEF',
            'is_published': True,
            'docker_image': 'my-new-job-1.0.0-seed:1.0.0',
            'manifest': manifest,
            'configuration': self.configuration
        }

        good_setting = {
            'DB_HOST': 'scale'
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue('/%s/job-types/my-new-job/1.0.0/' % self.api in response['location'])

        job_type = JobType.objects.filter(name='my-new-job').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], job_type.id)
        self.assertEqual(results['version'], job_type.version)
        self.assertEqual(results['title'], job_type.title)
        self.assertEqual(results['revision_num'], job_type.revision_num)
        self.assertEqual(results['revision_num'], 1)
        self.assertIsNone(results['max_scheduled'])
        self.assertEqual(results['configuration']['settings'], good_setting)

    def test_add_seed_job_type_minimum_manifest(self):
        """Tests adding a Seed image with a minimum Seed manifest"""

        url = '/%s/job-types/' % self.api
        manifest = copy.deepcopy(job_test_utils.MINIMUM_MANIFEST)
        manifest['job']['name'] = 'my-new-job'

        json_data = {
            'icon_code': 'BEEF',
            'is_published': False,
            'docker_image': 'my-new-job-1.0.0-seed:1.0.0',
            'manifest': manifest
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue('/%s/job-types/my-new-job/1.0.0/' % self.api in response['location'])

        job_type = JobType.objects.filter(name='my-new-job').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], job_type.id)
        self.assertEqual(results['version'], job_type.version)
        self.assertEqual(results['title'], job_type.title)
        self.assertEqual(results['revision_num'], job_type.revision_num)
        self.assertEqual(results['revision_num'], 1)
        self.assertEqual(results['is_published'], json_data['is_published'])

    def test_add_seed_version_job_type(self):
        """Tests adding a new version of a seed image."""

        url = '/%s/job-types/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['jobVersion'] = '1.1.0'

        json_data = {
            'icon_code': 'BEEF',
            'is_published': True,
            'max_scheduled': 1,
            'docker_image': 'my-job-1.1.0-seed:1.0.0',
            'manifest': manifest,
            'configuration': self.configuration
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue('/%s/job-types/my-job/1.1.0/' % self.api in response['location'])

        job_type = JobType.objects.filter(name='my-job', version='1.1.0').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], job_type.id)
        self.assertEqual(results['name'], job_type.name)
        self.assertEqual(results['version'], job_type.version)
        self.assertEqual(results['title'], job_type.title)
        self.assertEqual(results['is_published'], json_data['is_published'])
        self.assertIsNotNone(results['configuration']['mounts'])
        self.assertIsNotNone(results['configuration']['settings'])

    def test_edit_seed_job_type(self):
        """Tests editing an existing seed job type."""

        url = '/%s/job-types/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['packageVersion'] = '1.0.1'

        json_data = {
            'icon_code': 'BEEF',
            'is_published': True,
            'max_scheduled': 1,
            'docker_image': 'my-job-1.0.0-seed:1.0.1',
            'manifest': manifest,
            'configuration': self.configuration
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue('/%s/job-types/my-job/1.0.0/' % self.api in response['location'])

        job_type = JobType.objects.filter(name='my-job', version='1.0.0').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], job_type.id)
        self.assertEqual(results['name'], job_type.name)
        self.assertEqual(results['version'], job_type.version)
        self.assertEqual(results['title'], job_type.title)
        self.assertEqual(results['revision_num'], job_type.revision_num)
        self.assertEqual(results['revision_num'], 2)
        self.assertIsNotNone(results['configuration']['mounts'])
        self.assertIsNotNone(results['configuration']['settings'])

        manifest['job']['maintainer'].pop('url')

        json_data = {
            'icon_code': 'BEEF',
            'is_published': True,
            'max_scheduled': 1,
            'docker_image': 'my-job-1.0.0-seed:1.0.2',
            'manifest': manifest,
            'configuration': self.configuration
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue('/%s/job-types/my-job/1.0.0/' % self.api in response['location'])

        job_type = JobType.objects.filter(name='my-job', version='1.0.0').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], job_type.id)
        self.assertIsNone(results['manifest']['job']['maintainer'].get('url'))

    def test_create_seed_secrets(self):
        """Tests creating a new seed job type with secrets."""

        url = '/%s/job-types/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        name = 'job-type-post-test-secret'
        manifest['job']['name'] = name
        manifest['job']['interface']['settings'] = [
            {
              'name': 'VERSION',
              'secret': True
            },
            {
              'name': 'DB_HOST',
              'secret': True
            },
            {
              'name': 'DB_PASS',
              'secret': True
            }
          ]

        json_data = {
            'icon_code': 'BEEF',
            'is_published': False,
            'max_scheduled': 1,
            'docker_image': 'my-job-1.0.0-seed:1.0.0',
            'manifest': manifest,
            'configuration': self.configuration
        }

        with patch.object(SecretsHandler, '__init__', return_value=None), \
          patch.object(SecretsHandler, 'set_job_type_secrets', return_value=None) as mock_set_secret:
            response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        job_type = JobType.objects.filter(name=name).first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], job_type.id)

        # Secrets sent to Vault
        secrets_name = '-'.join([results['name'], results['version']]).replace('.', '_')
        secrets = json_data['configuration']['settings']
        mock_set_secret.assert_called_once_with(secrets_name, secrets)

        #Secrets scrubbed from configuration on return
        self.assertEqual(results['configuration']['settings'], {})

    def test_create_seed_missing_mount(self):
        """Tests creating a new seed job type with a mount referenced in configuration but not interface."""

        url = '/%s/job-types/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'my-job-no-mount'
        manifest['job']['interface']['mounts'] = []

        config = copy.deepcopy(self.configuration)
        #TODO investigate whether mounts in config but not manifest should be removed
        config['mounts'] = {}

        json_data = {
            'icon_code': 'BEEF',
            'is_published': True,
            'max_scheduled': 1,
            'docker_image': 'my-job-no-mount-1.0.0-seed:1.0.0',
            'manifest': manifest,
            'configuration': config
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        job_type = JobType.objects.filter(name='my-job-no-mount').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], job_type.id)
        self.assertEqual(results['configuration']['mounts'], {})

    def test_create_seed_missing_setting(self):
        """Tests creating a new seed job type with a setting referenced in configuration but not interface."""

        url = '/%s/job-types/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'my-job-no-setting'
        manifest['job']['interface']['settings'] = []
        config = copy.deepcopy(self.configuration)
        #TODO investigate whether settings in config but not manifest should be removed
        config['settings'] = {}

        json_data = {
            'icon_code': 'BEEF',
            'is_published': True,
            'max_scheduled': 1,
            'docker_image': 'my-job-no-setting-1.0.0-seed:1.0.0',
            'manifest': manifest,
            'configuration': config
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        job_type = JobType.objects.filter(name='my-job-no-setting').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], job_type.id)
        self.assertEqual(results['manifest']['job']['interface']['settings'], [])
        self.assertEqual(results['configuration']['settings'], {})

    def test_create_seed_missing_param(self):
        """Tests creating a seed job type with missing fields."""

        url = '/%s/job-types/' % self.api
        json_data = {
            'manifest': {
                'seedVersion': '1.0.0',
                'job': {
                    'name': 'my-job'
                }
            }
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_seed_bad_param(self):
        """Tests creating a job type with invalid type fields."""

        url = '/%s/job-types/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'my-job-bad-parameter'

        json_data = {
            'icon_code': 'BEEF',
            'is_published': True,
            'max_scheduled': 'BAD',
            'docker_image': '',
            'manifest': manifest,
            'configuration': self.configuration
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    @patch('job.models.CommandMessageManager')
    @patch('recipe.messages.update_recipe_definition.create_job_update_recipe_definition_message')
    def test_edit_seed_job_type_and_update(self, mock_create, mock_msg_mgr):
        """Tests editing an existing seed job type and automatically updating recipes."""

        url = '/%s/job-types/' % self.api
        manifest = copy.deepcopy(job_test_utils.MINIMUM_MANIFEST)
        manifest['job']['packageVersion'] = '1.0.1'

        json_data = {
            'icon_code': 'BEEF',
            'is_published': True,
            'max_scheduled': 1,
            'docker_image': 'my-job-1.0.0-seed:1.0.1',
            'manifest': manifest,
            'configuration': self.configuration,
            'auto_update': True
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue('/%s/job-types/my-minimum-job/1.0.0/' % self.api in response['location'])

        job_type = JobType.objects.filter(name='my-minimum-job', version='1.0.0').first()

        results = json.loads(response.content)
        self.assertEqual(results['id'], job_type.id)
        self.assertEqual(results['name'], job_type.name)
        self.assertEqual(results['version'], job_type.version)
        self.assertEqual(results['title'], job_type.title)
        self.assertEqual(results['is_published'], job_type.is_published)
        self.assertEqual(results['revision_num'], job_type.revision_num)
        self.assertEqual(results['revision_num'], 2)
        self.assertIsNotNone(results['configuration']['mounts'])
        self.assertIsNotNone(results['configuration']['settings'])

        recipe_type = RecipeType.objects.get(pk=self.recipe_type1.id)
        mock_create.assert_called_with(self.recipe_type1.id, job_type.id)


class TestJobTypeDetailsViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.manifest = job_test_utils.COMPLETE_MANIFEST

        self.output_workspace = storage_test_utils.create_workspace()
        self.configuration = {
            'version': '6',
            'mounts': {
                'MOUNT_PATH': {
                    'type': 'host',
                    'host_path': '/path/to/dted',
                    },
                'WRITE_PATH': {
                    'type': 'host',
                    'host_path': '/path/to/dted',
                    },
            },
            'output_workspaces': {'default': self.output_workspace.name},
            'settings': {
                'DB_HOST': 'scale',
            },
        }

        self.workspace = storage_test_utils.create_workspace()
        self.trigger_config = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
            },
            'data': {
                'input_data_name': 'input_file',
                'workspace_name': self.workspace.name,
            }
        }
        # self.trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type='PARSE', is_active=True,
        #                                                           configuration=self.trigger_config)

        self.job_type = job_test_utils.create_seed_job_type(manifest=self.manifest, max_scheduled=2,
                                                       configuration=self.configuration)

    def test_not_found(self):
        """Tests calling the get job type details view with a job name/version that does not exist."""

        url = '/%s/job-types/missing-job/1.0.0/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get job type details view."""

        url = '/%s/job-types/%s/%s/' % (self.api, self.job_type.name, self.job_type.version)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.job_type.id)
        self.assertEqual(result['name'], self.job_type.name)
        self.assertEqual(result['version'], self.job_type.version)

        self.assertIsNotNone(result['manifest'])
        self.assertIsNotNone(result['configuration'])
        self.assertEqual(result['max_scheduled'], 2)

    def test_edit_not_found(self):
        """Tests calling the get job type details view with a job name/version that does not exist."""

        url = '/%s/job-types/missing-job/1.0.0/' % self.api
        json_data = {
            'icon_code': 'BEEF',
            'is_active': False,
            'is_paused': True,
            'max_scheduled': 9
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_edit_simple(self):
        """Tests editing only the basic attributes of a job type"""

        url = '/%s/job-types/%s/%s/' % (self.api, self.job_type.name, self.job_type.version)
        json_data = {
            'icon_code': 'BEEF',
            'is_published': True,
            'is_active': False,
            'is_paused': True,
            'max_scheduled': 9
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_edit_configuration(self):
        """Tests editing the configuration of a job type"""
        configuration = copy.deepcopy(self.configuration)
        configuration['settings'] = {'DB_HOST': 'other_scale_db'}
        configuration['mounts'] = {
            'dted': {
                'type': 'host',
                'host_path': '/some/new/path'
                }
            }

        url = '/%s/job-types/%s/%s/' % (self.api, self.job_type.name, self.job_type.version)
        json_data = {
            'configuration': configuration,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_edit_bad_configuration(self):
        """Tests passing an invalid configuration of a job type to the patch interface"""
        configuration = copy.deepcopy(self.configuration)
        configuration['priority'] = 0

        url = '/%s/job-types/%s/%s/' % (self.api, self.job_type.name, self.job_type.version)
        json_data = {
            'configuration': configuration,
        }
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

class TestJobTypeRevisionsViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.manifest = job_test_utils.COMPLETE_MANIFEST

        self.output_workspace = storage_test_utils.create_workspace()
        self.configuration = {
            'version': '6',
            'mounts': {
                'dted': {
                    'type': 'host',
                    'host_path': '/path/to/dted',
                    },
            },
            'output_workspaces': {'default': self.output_workspace.name},
            'settings': {
                'DB_HOST': 'scale',
            },
        }

        self.workspace = storage_test_utils.create_workspace()
        self.trigger_config = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain',
            },
            'data': {
                'input_data_name': 'input_file',
                'workspace_name': self.workspace.name,
            }
        }
        # self.trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type='PARSE', is_active=True,
        #                                                           configuration=self.trigger_config)

        self.job_type = job_test_utils.create_seed_job_type(manifest=self.manifest, max_scheduled=2,
                                                            configuration=self.configuration)

        manifest2 = copy.deepcopy(self.manifest)
        manifest2['job']['packageVersion'] = '1.0.1'
        manifest2['job']['maintainer']['name'] = 'Jane Doe'
        self.job_type.manifest = manifest2
        job_test_utils.edit_job_type_v6(self.job_type, manifest2)

    def test_not_found(self):
        """Tests successfully calling the get job type revisions view with a job type that does not exist."""

        url = '/%s/job-types/missing-job/1.0.0/revisions/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

        # correct job type, bad version
        url = '/%s/job-types/my-job/9.9.9/revisions/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful_list(self):
        """Tests successfully calling the get job type revisions view."""

        url = '/%s/job-types/%s/%s/revisions/' % (self.api, self.job_type.name, self.job_type.version)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        result = result['results']
        self.assertEqual(len(result), 2)
        self.assertTrue(isinstance(result[0], dict), 'result  must be a dictionary')
        self.assertEqual(result[0]['job_type']['name'], self.job_type.name)
        self.assertEqual(result[0]['revision_num'], 2)
        self.assertEqual(result[0]['docker_image'], 'fake')

    def test_details_not_found(self):
        """Tests successfully calling the get job type revision details view with a job type revision that does not exist."""

        url = '/%s/job-types/missing-job/1.0.0/revisions/9/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful_details(self):
        """Tests successfully calling the get job type revision details view."""

        url = '/%s/job-types/%s/%s/revisions/1/' % (self.api, self.job_type.name, self.job_type.version)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['job_type']['name'], self.job_type.name)
        self.assertEqual(result['revision_num'], 1)
        self.assertEqual(result['docker_image'], 'fake')
        self.assertIsNotNone(result['manifest'])


class TestJobTypesValidationViewV6(TransactionTestCase):
    """Tests related to the job-types validation endpoint"""

    api = 'v6'

    def setUp(self):
        django.setup()

        self.configuration = {
            'version': '6',
            'output_workspaces': {
              'default': 'workspace_1',
              'outputs': {'output_file_pngs': 'workspace_2'}
            },
            'mounts': {
                'MOUNT_PATH': {
                    'type': 'host',
                    'host_path': '/path/to/mount',
                    },
                'WRITE_PATH': {
                    'type': 'host',
                    'host_path': '/path/to/mount',
                    },
            },
            'settings': {
                'VERSION': '1.0.0',
                'DB_HOST': 'scale',
                'DB_PASS': 'password',
            },
        }

        self.workspace1 = storage_test_utils.create_workspace(name='workspace_1')
        self.workspace2 = storage_test_utils.create_workspace(name='workspace_2')
        self.inactivews = storage_test_utils.create_workspace(name='inactive', is_active=False)

    def test_successful(self):
        """Tests validating a new job type."""

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)

        json_data = {
            'manifest': manifest,
            'configuration': self.configuration
        }

        url = '/%s/job-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertDictEqual(results, {u'errors': [], u'is_valid': True, u'warnings': []})

    def test_successful_configuration(self):
        """Tests validating a new job type with a valid configuration."""
        url = '/%s/job-types/validation/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        json_data = {
            'manifest': manifest,
            'configuration': self.configuration
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertDictEqual(results, {u'errors': [], u'is_valid': True, u'warnings': []})

    def test_missing_mount(self):
        """Tests validating a new job type with a mount referenced in manifest but not configuration."""
        url = '/%s/job-types/validation/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        config = copy.deepcopy(self.configuration)
        config['mounts'] = {}
        json_data = {
            'manifest': manifest,
            'configuration': config
        }


        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['warnings']), 2)
        self.assertEqual(results['warnings'][0]['name'], 'MISSING_MOUNT')
        self.assertEqual(results['warnings'][1]['name'], 'MISSING_MOUNT')

    def test_unknown_mount(self):
        """Tests validating a new job type with a mount referenced in configuration but not manifest."""
        url = '/%s/job-types/validation/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'my-job-no-mount'
        manifest['job']['interface']['mounts'] = []
        json_data = {
            'manifest': manifest,
            'configuration': self.configuration
        }


        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['warnings']), 2)
        self.assertEqual(results['warnings'][0]['name'], 'UNKNOWN_MOUNT')
        self.assertEqual(results['warnings'][1]['name'], 'UNKNOWN_MOUNT')

    def test_missing_setting(self):
        """Tests validating a new job type with a setting referenced in manifest but not configuration."""
        url = '/%s/job-types/validation/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        config = copy.deepcopy(self.configuration)
        config['settings'] = {}
        json_data = {
            'manifest': manifest,
            'configuration': config
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['warnings']), 3)
        self.assertEqual(results['warnings'][0]['name'], 'MISSING_SETTING')

    def test_unknown_setting(self):
        """Tests validating a new job type with a setting referenced in configuration but not manifest."""
        url = '/%s/job-types/validation/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        config = copy.deepcopy(self.configuration)
        config['settings'] = {
                'VERSION': '1.0.0',
                'DB_HOST': 'scale',
                'DB_PASS': 'password',
                'setting': 'extra'
        }

        json_data = {
            'manifest': manifest,
            'configuration': config
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0]['name'], 'UNKNOWN_SETTING')

    def test_secret_setting(self):
        """Tests validating a new job type with a secret setting."""
        url = '/%s/job-types/validation/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        config = copy.deepcopy(self.configuration)

        json_data = {
            'manifest': manifest,
            'configuration': config
        }


        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['warnings']), 0)

    def test_bad_param(self):
        """Tests validating a new job type with missing fields."""
        url = '/%s/job-types/validation/' % self.api
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['name'] = None
        json_data = {
            'manifest': manifest,
            'configuration': self.configuration
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertFalse(results['is_valid'])
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['name'], 'JSON_VALIDATION_ERROR')

    def test_bad_error(self):
        """Tests validating a new job type with an invalid error relationship."""
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['errors'] = [
          {
            'code': '1',
            'name': 'error-name-one',
            'title': 'Error Name',
            'description': 'Error Description',
            'category': 'data'
          }
        ]
        json_data = {
            'manifest': manifest,
            'configuration': self.configuration
        }

        url = '/%s/job-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertFalse(results['is_valid'])
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['name'], 'JSON_VALIDATION_ERROR')

    def test_invalid_output_workspace(self):
        """Tests validating a new job type with an invalid output workspace."""
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        config = copy.deepcopy(self.configuration)
        config['output_workspaces'] = {
            'default': 'bad_name'
        }
        json_data = {
            'manifest': manifest,
            'configuration': config
        }

        url = '/%s/job-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertFalse(results['is_valid'])
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['name'], 'INVALID_WORKSPACE')

    def test_deprecated_output_workspace(self):
        """Tests validating a new job type with an inactive output workspace."""
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        config = copy.deepcopy(self.configuration)
        config['output_workspaces'] = {
            'default': 'inactive'
        }
        json_data = {
            'manifest': manifest,
            'configuration': config
        }

        url = '/%s/job-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0]['name'], 'DEPRECATED_WORKSPACE')

    def test_missing_output_workspace(self):
        """Tests validating a new job type with a missing output workspace."""
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        config = copy.deepcopy(self.configuration)
        config['output_workspaces'] = {}
        json_data = {
            'manifest': manifest,
            'configuration': config
        }

        url = '/%s/job-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertFalse(results['is_valid'])
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['name'], 'MISSING_WORKSPACE')

    def test_nonstandard_resource(self):
        """Tests validating a new job type with a nonstandard resource."""
        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['resources']['scalar'].append({'name': 'chocolate', 'value': 1.0 })
        config = copy.deepcopy(self.configuration)
        json_data = {
            'manifest': manifest,
            'configuration': config
        }

        url = '/%s/job-types/validation/' % self.api
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertTrue(results['is_valid'])
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0]['name'], 'NONSTANDARD_RESOURCE')

class TestJobTypesPendingView(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.job = job_test_utils.create_job(status='PENDING')

    def test_successful(self):
        """Tests successfully calling the pending status view."""

        url = '/%s/job-types/pending/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job.job_type.name)
        self.assertEqual(result['results'][0]['count'], 1)
        self.assertIsNotNone(result['results'][0]['longest_pending'])


class TestJobTypesRunningView(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.job = job_test_utils.create_job(status='RUNNING')

    def test_successful(self):
        """Tests successfully calling the running status view."""

        url = '/%s/job-types/running/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job.job_type.name)
        self.assertEqual(result['results'][0]['count'], 1)
        self.assertIsNotNone(result['results'][0]['longest_running'])


class TestJobTypesSystemFailuresView(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.error = Error(name='Test Error', description='test')
        self.error.save()
        self.job = job_test_utils.create_job(status='FAILED', error=self.error)

    def test_successful(self):
        """Tests successfully calling the system failures view."""

        url = '/%s/job-types/system-failures/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job.job_type.name)
        self.assertEqual(result['results'][0]['count'], 1)


class TestJobExecutionsViewV6(TransactionTestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_seed_job_type()
        self.error = error_test_utils.create_error()
        self.job_1 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED', error=self.error)
        self.node_1 = node_test_utils.create_node()
        self.node_2 = node_test_utils.create_node()
        self.job_exe_1a = job_test_utils.create_job_exe(job=self.job_1, exe_num=1, status='FAILED', node=self.node_1,
                                                        started='2017-01-02T00:00:00Z', ended='2017-01-02T01:00:00Z',
                                                        error=self.error)
        self.job_exe_1b = job_test_utils.create_job_exe(job=self.job_1, exe_num=2, status='COMPLETED', node=self.node_2,
                                                        started='2017-01-01T00:00:00Z', ended='2017-01-01T01:00:00Z')
        self.job_exe_1c = job_test_utils.create_job_exe(job=self.job_1, exe_num=3, status='COMPLETED', node=self.node_2,
                                                        started='2017-01-01T00:00:00Z', ended='2017-01-01T01:00:00Z')
        self.last_exe_1 = job_test_utils.create_job_exe(job=self.job_1, exe_num=4, status='RUNNING', node=self.node_2,
                                                        started='2017-01-03T00:00:00Z', ended='2017-01-03T01:00:00Z')

    def test_get_job_executions(self):
        """This test checks to make sure there are 4 job executions."""
        url = '/%s/jobs/%d/executions/' % (self.api, self.job_1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        job_exe_count = results['count']
        self.assertEqual(job_exe_count, 4)
        #check that we order by descending exe_num
        self.assertEqual(results['results'][0]['exe_num'], 4)

    def test_get_job_execution_bad_id(self):
        url = '/%s/jobs/999999999/executions/' % self.api
        response = self.client.generic('GET', url)
        result = json.loads(response.content)
        self.assertEqual(result['results'], [])

    def test_get_job_execution_filter_node(self):
        url = '/%s/jobs/%d/executions/?node_id=%d' % (self.api, self.job_1.id, self.node_1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        job_exe_count = results['count']
        self.assertEqual(job_exe_count, 1)

    def test_get_job_execution_filter_status(self):
        url = '/%s/jobs/%d/executions/?status=COMPLETED' % (self.api, self.job_1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        job_exe_count = results['count']
        self.assertEqual(job_exe_count, 2)

    def test_get_job_execution_filter_error(self):
        url = '/%s/jobs/%d/executions/?error_id=%d' % (self.api, self.job_1.id, self.error.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        job_exe_count = results['count']
        self.assertEqual(job_exe_count, 1)

        url = '/%s/jobs/%d/executions/?error_category=%s' % (self.api, self.job_1.id, self.error.category)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        job_exe_count = results['count']
        self.assertEqual(job_exe_count, 1)


class TestJobExecutionDetailsViewV6(TransactionTestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_seed_job_type()
        self.job_1 = job_test_utils.create_job(job_type=self.job_type_1, status='COMPLETED')

        self.job_exe_1a = job_test_utils.create_job_exe(job=self.job_1, exe_num=9999, status='COMPLETED')

    def test_get_job_execution_for_job_exe_id(self):
        url = '/%s/jobs/%d/executions/%d/' % (self.api, self.job_1.id, self.job_exe_1a.exe_num)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['id'], self.job_exe_1a.id)
        self.assertIn('task_results', results)
        self.assertIn('resources', results)
        self.assertIn('configuration', results)
        self.assertIn('output', results)

    def test_get_job_execution_bad_exe_num(self):
        url = '/%s/jobs/%d/executions/%d/' % (self.api, self.job_1.id, 999999999)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)


class TestJobExecutionSpecificLogViewV6(TestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

    def test_bad_job_exe_id(self):
        url = '/%s/job-executions/999999/logs/combined/' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    @patch('job.views.JobExecution.objects.get_logs')
    def test_combined_log_json_no_time(self, mock_get_logs):
        def new_get_log_json(include_stdout, include_stderr, since):
            self.assertTrue(include_stdout)
            self.assertTrue(include_stderr)
            self.assertIsNone(since)
            return {}, now()

        mock_get_logs.return_value.get_log_json.side_effect = new_get_log_json

        url = '/%s/job-executions/999999/logs/combined/?format=json' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(response.accepted_media_type, 'application/json')

    @patch('job.views.JobExecution.objects.get_logs')
    def test_combined_log_text_no_time(self, mock_get_logs):
        def new_get_log_text(include_stdout, include_stderr, since, html):
            self.assertTrue(include_stdout)
            self.assertTrue(include_stderr)
            self.assertIsNone(since)
            self.assertFalse(html)
            return 'hello', now()

        mock_get_logs.return_value.get_log_text.side_effect = new_get_log_text

        url = '/%s/job-executions/999999/logs/combined/?format=txt' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(response.accepted_media_type, 'text/plain')

    @patch('job.views.JobExecution.objects.get_logs')
    def test_combined_log_html_no_time(self, mock_get_logs):
        def new_get_log_text(include_stdout, include_stderr, since, html):
            self.assertTrue(include_stdout)
            self.assertTrue(include_stderr)
            self.assertIsNone(since)
            self.assertTrue(html)
            return '<html>hello</html>', now()

        mock_get_logs.return_value.get_log_text.side_effect = new_get_log_text

        url = '/%s/job-executions/999999/logs/combined/?format=html' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(response.accepted_media_type, 'text/html')

    @patch('job.views.JobExecution.objects.get_logs')
    def test_combined_log_json_no_content(self, mock_get_logs):
        def new_get_log_json(include_stdout, include_stderr, since):
            self.assertTrue(include_stdout)
            self.assertTrue(include_stderr)
            self.assertIsNone(since)
            return None, now()

        mock_get_logs.return_value.get_log_json.side_effect = new_get_log_json

        url = '/%s/job-executions/999999/logs/combined/?format=json' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    @patch('job.views.JobExecution.objects.get_logs')
    def test_stdout_log_html_no_time(self, mock_get_logs):
        def new_get_log_text(include_stdout, include_stderr, since, html):
            self.assertTrue(include_stdout)
            self.assertFalse(include_stderr)
            self.assertIsNone(since)
            self.assertTrue(html)
            return '<html>hello</html>', now()

        mock_get_logs.return_value.get_log_text.side_effect = new_get_log_text

        url = '/%s/job-executions/999999/logs/stdout/?format=html' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(response.accepted_media_type, 'text/html')

    @patch('job.views.JobExecution.objects.get_logs')
    def test_stderr_log_html_no_time(self, mock_get_logs):
        def new_get_log_text(include_stdout, include_stderr, since, html):
            self.assertFalse(include_stdout)
            self.assertTrue(include_stderr)
            self.assertIsNone(since)
            self.assertTrue(html)
            return '<html>hello</html>', now()

        mock_get_logs.return_value.get_log_text.side_effect = new_get_log_text

        url = '/%s/job-executions/999999/logs/stderr/?format=html' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(response.accepted_media_type, 'text/html')

    @patch('job.views.JobExecution.objects.get_logs')
    def test_combined_log_json_with_time(self, mock_get_logs):
        started = datetime.datetime(2016, 1, 1, tzinfo=utc)

        def new_get_log_json(include_stdout, include_stderr, since):
            self.assertTrue(include_stdout)
            self.assertTrue(include_stderr)
            self.assertEqual(since, started)
            return {}, now()

        mock_get_logs.return_value.get_log_json.side_effect = new_get_log_json

        url = '/%s/job-executions/999999/logs/combined/?started=2016-01-01T00:00:00Z&format=json' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(response.accepted_media_type, 'application/json')


class TestJobInputFilesViewV6(TestCase):
    api = 'v6'

    def setUp(self):

        # Create legacy test files
        self.f1_file_name = 'legacy_foo.bar'
        self.f1_last_modified = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.f1_source_started = datetime.datetime(2016, 1, 1, tzinfo=utc)
        self.f1_source_ended = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.file1 = storage_test_utils.create_file(file_name=self.f1_file_name, source_started=self.f1_source_started,
                                                    source_ended=self.f1_source_ended,
                                                    last_modified=self.f1_last_modified)

        self.f2_file_name = 'legacy_qaz.bar'
        self.f2_job_input = 'legacy_input_1'
        self.f2_last_modified = datetime.datetime(2016, 1, 3, tzinfo=utc)
        self.f2_source_started = datetime.datetime(2016, 1, 2, tzinfo=utc)
        self.f2_source_ended = datetime.datetime(2016, 1, 3, tzinfo=utc)
        self.file2 = storage_test_utils.create_file(file_name=self.f2_file_name, source_started=self.f2_source_started,
                                                    source_ended=self.f2_source_ended,
                                                    last_modified=self.f2_last_modified)

        job_interface = {
            'version': '1.0',
            'command': 'test_cmd',
            'command_arguments': 'test_arg',
            'input_data': [{
                'type': 'property',
                'name': 'input_field',
            }, {
                'type': 'file',
                'name': 'input_file',
            }, {
                'type': 'file',
                'name': 'other_input_file',
            }],
            'output_data': [{
                'type': 'file',
                'name': 'output_file',
            }, {
                'type': 'files',
                'name': 'output_files',
            }],
            'shared_resources': [],
        }

        self.manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)

        self.manifest['job']['interface']['inputs']['files'] = [{'name': 'input_file'},{'name': 'other_input_file'}]

        self.manifest['job']['interface']['inputs']['json'] =  [{'name': 'input_field', 'type': 'string'}]

        self.manifest['job']['interface']['outputs']['files'] = [{'name': 'output_file'},{'name': 'output_files', 'multiple': True}]

        job_data = {
            'input_data': [{
                'name': 'input_file',
                'file_id': self.file1.id,
            }, {
                'name': self.f2_job_input,
                'file_id': self.file2.id,
            }]
        }
        job_results = {
            'output_data': []
        }
        self.job_type = job_test_utils.create_seed_job_type(manifest=self.manifest)
        self.job = job_test_utils.create_job(job_type=self.job_type)

        # Create JobInputFile entry files
        self.f3_file_name = 'foo.bar'
        self.f3_last_modified = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.f3_source_started = datetime.datetime(2016, 1, 10, tzinfo=utc)
        self.f3_source_ended = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.file3 = job_test_utils.create_input_file(file_name=self.f3_file_name,
                                                      source_started=self.f3_source_started,
                                                      source_ended=self.f3_source_ended, job=self.job,
                                                      last_modified=self.f3_last_modified)

        self.f4_file_name = 'qaz.bar'
        self.f4_job_input = 'input_1'
        self.f4_last_modified = datetime.datetime(2016, 1, 12, tzinfo=utc)
        self.f4_source_started = datetime.datetime(2016, 1, 11, tzinfo=utc)
        self.f4_source_ended = datetime.datetime(2016, 1, 12, tzinfo=utc)
        self.file4 = job_test_utils.create_input_file(file_name=self.f4_file_name,
                                                      source_started=self.f4_source_started,
                                                      source_ended=self.f4_source_ended, job=self.job,
                                                      last_modified=self.f4_last_modified, job_input=self.f4_job_input)

    def test_successful_file(self):
        """Tests successfully calling the job input files view"""

        url = '/%s/jobs/%i/input_files/' % (self.api, self.job.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file3.id, self.file4.id])
            self.assertIn('file_name', result)
            self.assertIn('workspace', result)
            self.assertIn('media_type', result)
            self.assertIn('file_type', result)
            self.assertIn('file_size', result)
            self.assertIn('file_path', result)
            self.assertIn('is_deleted', result)
            self.assertIn('url', result)
            self.assertIn('created', result)
            self.assertIn('deleted', result)
            self.assertIn('data_started', result)
            self.assertIn('data_ended', result)
            self.assertIn('source_started', result)
            self.assertIn('source_ended', result)
            self.assertIn('last_modified', result)
            self.assertIn('geometry', result)
            self.assertIn('center_point', result)
            self.assertIn('countries', result)
            self.assertIn('job_type', result)
            self.assertIn('job', result)
            self.assertIn('job_exe', result)
            self.assertIn('job_output', result)
            self.assertIn('recipe_type', result)
            self.assertIn('recipe', result)
            self.assertIn('recipe_node', result)
            self.assertIn('batch', result)
            self.assertFalse(result['is_superseded'])
            self.assertIn('superseded', result)


    def test_filter_job_input(self):
        """Tests successfully calling the job inputs files view with job_input string filtering"""

        url = '/%s/jobs/%i/input_files/?job_input=%s' % (self.api, self.job.id, self.f4_job_input)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.file4.id)

    def test_file_name_successful(self):
        """Tests successfully calling the get files by name view"""

        url = '/%s/jobs/%i/input_files/?file_name=%s' % (self.api, self.job.id, self.f3_file_name)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        result = results['results']
        self.assertEqual(len(result), 1)

        self.assertEqual(self.f3_file_name, result[0]['file_name'])
        self.assertEqual('2016-01-10T00:00:00Z', result[0]['source_started'])
        self.assertEqual(self.file3.id, result[0]['id'])

    def test_bad_file_name(self):
        """Tests unsuccessfully calling the get files by name view"""

        url = '/%s/jobs/%i/input_files/?file_name=%s' % (self.api, self.job.id, 'not_a.file')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        result = results['results']
        self.assertEqual(len(result), 0)

    def test_time_successful(self):
        """Tests unsuccessfully calling the get files by name view"""

        url = '/%s/jobs/%i/input_files/?started=%s&ended=%s&time_field=%s' % (self.api, self.job.id,
                                                                              '2016-01-10T00:00:00Z',
                                                                              '2016-01-13T00:00:00Z',
                                                                              'source')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        results = result['results']
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['id'] in [self.file3.id, self.file4.id])


class TestCancelJobsViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'my-job-type'
        self.job_type1 = job_test_utils.create_seed_job_type(manifest=manifest)
        manifest['job']['jobVersion'] = '1.0.1'
        self.job_type2 = job_test_utils.create_seed_job_type(manifest=manifest)

    @patch('job.views.CommandMessageManager')
    @patch('job.views.create_cancel_jobs_bulk_message')
    def test_cancel(self, mock_create, mock_msg_mgr):
        """Tests calling the job cancel view successfully"""

        msg = CancelJobsBulk()
        mock_create.return_value = msg

        started = now()
        ended = started + datetime.timedelta(minutes=1)
        error_categories = ['SYSTEM']
        error_ids = [1, 2]
        job_ids = [3, 4]
        job_status = 'FAILED'
        job_type_ids = [5, 6]
        job_types = [{'name': 'my-job-type', 'version': '1.0.0'},
                     {'name': 'my-job-type', 'version': '1.0.1'}]
        job_type_names = ['name']
        batch_ids = [7, 8]
        recipe_ids = [9, 10]
        is_superseded = False
        json_data = {
            'started': datetime_to_string(started),
            'ended': datetime_to_string(ended),
            'status': job_status,
            'job_ids': job_ids,
            'job_type_ids': job_type_ids,
            'job_types': job_types,
            'job_type_names': job_type_names,
            'batch_ids': batch_ids,
            'recipe_ids': recipe_ids,
            'error_categories': error_categories,
            'error_ids': error_ids,
            'is_superseded': is_superseded
        }

        url = '/%s/jobs/cancel/' % self.api
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        job_type_ids.append(self.job_type1.id)
        job_type_ids.append(self.job_type2.id)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)
        mock_create.assert_called_with(started=started, ended=ended, error_categories=error_categories,
                                       error_ids=error_ids, job_ids=job_ids, job_type_ids=job_type_ids,
                                       status=job_status, job_type_names=job_type_names,
                                       batch_ids=batch_ids, recipe_ids=recipe_ids, is_superseded=is_superseded)

    @patch('job.views.CommandMessageManager')
    @patch('job.views.create_cancel_jobs_bulk_message')
    def test_cancel_invalid(self, mock_create, mock_msg_mgr):
        """Tests calling the job cancel view with an invalid jobtype name/version"""

        job_types = [{'name': 'bad', 'version': '1.0.0'}]

        json_data = {
            'job_types': job_types
        }

        url = '/%s/jobs/cancel/' % self.api
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestRequeueJobsViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        manifest = copy.deepcopy(job_test_utils.COMPLETE_MANIFEST)
        manifest['job']['name'] = 'my-job-type'
        self.job_type1 = job_test_utils.create_seed_job_type(manifest=manifest)
        manifest['job']['jobVersion'] = '1.0.1'
        self.job_type2 = job_test_utils.create_seed_job_type(manifest=manifest)


    @patch('job.views.CommandMessageManager')
    @patch('job.views.create_requeue_jobs_bulk_message')
    def test_requeue(self, mock_create, mock_msg_mgr):
        """Tests calling the requeue view successfully"""

        msg = RequeueJobsBulk()
        mock_create.return_value = msg

        started = now()
        ended = started + datetime.timedelta(minutes=1)
        error_categories = ['SYSTEM']
        error_ids = [1, 2]
        job_ids = [3, 4]
        job_status = 'FAILED'
        job_type_ids = [5, 6]
        job_types = [{'name': 'my-job-type', 'version': '1.0.0'},
                     {'name': 'my-job-type', 'version': '1.0.1'}]
        job_type_names = ['name']
        batch_ids = [7, 8]
        recipe_ids = [9, 10]
        is_superseded = False
        priority = 101
        json_data = {
            'started': datetime_to_string(started),
            'ended': datetime_to_string(ended),
            'status': job_status,
            'job_ids': job_ids,
            'job_type_ids': job_type_ids,
            'job_types': job_types,
            'job_type_names': job_type_names,
            'batch_ids': batch_ids,
            'recipe_ids': recipe_ids,
            'error_categories': error_categories,
            'error_ids': error_ids,
            'is_superseded': is_superseded,
            'priority': priority
        }

        url = '/%s/jobs/requeue/' % self.api
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        job_type_ids.append(self.job_type1.id)
        job_type_ids.append(self.job_type2.id)

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)
        mock_create.assert_called_with(started=started, ended=ended, error_categories=error_categories,
                                       error_ids=error_ids, job_ids=job_ids, job_type_ids=job_type_ids,
                                       priority=priority, status=job_status,
                                       job_type_names=job_type_names, batch_ids=batch_ids,
                                       recipe_ids=recipe_ids, is_superseded=is_superseded)

    @patch('job.views.CommandMessageManager')
    @patch('job.views.create_requeue_jobs_bulk_message')
    def test_requeue_invalid(self, mock_create, mock_msg_mgr):
        """Tests calling the job requeue view with an invalid jobtype name/version"""

        job_types = [{'name': 'bad', 'version': '1.0.0'}]

        json_data = {
            'job_types': job_types
        }

        url = '/%s/jobs/requeue/' % self.api
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)