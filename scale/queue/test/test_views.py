##PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import json

import django
import django.utils.timezone as timezone
from django.test import TestCase
from mock import patch
from rest_framework import status
import time

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import queue.test.utils as queue_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
from job.configuration.data.exceptions import InvalidData
from job.models import Job
from queue.models import Queue


class TestJobLoadView(TestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_job_type(name='test1', version='1.0', category='test-1', priority=1)
        queue_test_utils.create_job_load(job_type=self.job_type1, pending_count=1)
        # sleep's are needed because if the job load entries end up with the same timestamp, there will be fewer
        # entries in the GET then expected in the tests. sleep's ensure the timestamps will be different as they
        # maintain 3 sig figs in the decimal
        time.sleep(0.001)

        self.job_type2 = job_test_utils.create_job_type(name='test2', version='1.0', category='test-2', priority=2)
        queue_test_utils.create_job_load(job_type=self.job_type2, queued_count=1)
        time.sleep(0.001)

        self.job_type3 = job_test_utils.create_job_type(name='test3', version='1.0', category='test-3', priority=3)
        queue_test_utils.create_job_load(job_type=self.job_type3, running_count=1)

    def test_successful(self):
        '''Tests successfully calling the job load view.'''

        url = '/load/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 3)

    def test_job_type_id(self):
        '''Tests successfully calling the job laod view filtered by job type identifier.'''

        url = '/load/?job_type_id=%s' % self.job_type1.id
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['pending_count'], 1)

    def test_job_type_name(self):
        '''Tests successfully calling the job load view filtered by job type name.'''

        url = '/load/?job_type_name=%s' % self.job_type2.name
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['queued_count'], 1)

    def test_job_type_category(self):
        '''Tests successfully calling the job load view filtered by job type category.'''

        url = '/load/?job_type_category=%s' % self.job_type3.category
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['running_count'], 1)

    def test_job_type_priority(self):
        '''Tests successfully calling the job load view filtered by job type priority.'''

        url = '/load/?job_type_priority=%s' % self.job_type1.priority
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['pending_count'], 1)

    def test_max_duration(self):
        '''Tests calling the job load view with time values that define a range greater than 31 days'''

        url = '/load/?started=2015-01-01T00:00:00Z&ended=2015-02-02T00:00:00Z'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# TODO: Remove this once the UI migrates to /load
class TestQueueDepthView(TestCase):

    def setUp(self):
        django.setup()

    def test_missing_both_params(self):
        '''Tests calling the queue depth view with no parameter values.'''

        url = '/queue/depth/'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_started(self):
        '''Tests calling the queue depth view with no started value.'''

        url = '/queue/depth/?ended=2015-01-01T00:00:00Z'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_ended(self):
        '''Tests calling the queue depth view with no ended value.'''

        url = '/queue/depth/?ended=2015-01-01T00:00:00Z'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_timezone(self):
        '''Tests calling the queue depth view with time values that lack a timezone'''

        url = '/queue/depth/?started=2015-01-01T00:00:00&ended=2015-01-02T00:00:00'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_over_31_days(self):
        '''Tests calling the queue depth view with time values that define a range greater than 31 days'''

        url = '/queue/depth/?started=2015-01-01T00:00:00Z&ended=2015-02-02T00:00:00Z'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_time_range(self):
        '''Tests calling the queue depth view with time values that define a negative time range'''

        url = '/queue/depth/?ended=2015-01-01T00:00:00Z&started=2015-01-02T00:00:00Z'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful(self):
        '''Tests calling the queue depth view successfully.'''

        url = '/queue/depth/?started=2015-01-01T00:00:00Z&ended=2015-01-02T00:00:00Z'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(result, {'job_types': [], 'priorities': [], 'queue_depths': []})


class TestQueueNewJobView(TestCase):

    def setUp(self):
        django.setup()

    def test_bad_job_type_id(self):
        '''Tests calling the queue status view with an invalid job type ID.'''

        json_data = {
            'job_type_id': -1234,
            'job_data': {},
        }

        url = '/queue/new-job/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bad_type_job_type_id(self):
        '''Tests calling the queue status view with a string job type ID (which is invalid).'''

        json_data = {
            'job_type_id': 'BAD',
            'job_data': {},
        }

        url = '/queue/new-job/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_job_type_id(self):
        '''Tests calling the queue status view without the required job type ID.'''

        json_data = {
            'job_data': {},
        }

        url = '/queue/new-job/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('queue.views.JobType.objects.get', lambda pk: job_test_utils.create_job_type())
    def test_bad_type_args(self):
        '''Tests calling the queue status view with a string job_data value (which is invalid).'''

        json_data = {
            'job_type_id': 123,
            'job_data': 'BAD',
        }

        url = '/queue/new-job/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('queue.views.JobType.objects.get', lambda pk: job_test_utils.create_job_type())
    @patch('queue.views.Queue.objects.queue_new_job_for_user')
    def test_invalid_args(self, mock_queue):
        '''Tests calling the queue status view with invalid job_data for the job.'''
        mock_queue.side_effect = InvalidData('Invalid args')

        json_data = {
            'job_type_id': 123,
            'job_data': {},
        }

        url = '/queue/new-job/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('queue.views.JobType.objects.get', lambda pk: job_test_utils.create_job_type())
    @patch('queue.views.Queue.objects.queue_new_job_for_user')
    def test_successful(self, mock_queue):
        '''Tests calling the queue status view successfully.'''
        job1 = job_test_utils.create_job()
        job2 = job_test_utils.create_job()

        def new_queue(job_type, data):
            return job1.id, job2.id
        mock_queue.side_effect = new_queue

        json_data = {
            'job_type_id': job1.id,
            'job_data': {
                'version': '1.0',
            }
        }
        url = '/queue/new-job/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response['Location'])
        self.assertEqual(result['id'], job1.id)


class TestQueueNewRecipeView(TestCase):

    def setUp(self):
        django.setup()

    def test_bad_recipe_id(self):
        '''Tests calling the queue recipe view with an invalid recipe ID.'''

        json_data = {
            'recipe_type_id': -1234,
            'recipe_data': {},
        }

        url = '/queue/new-recipe/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bad_type_recipe_id(self):
        '''Tests calling the queue recipe view with a string recipe ID (which is invalid).'''

        json_data = {
            'recipe_id': 'BAD',
            'recipe_data': {},
        }

        url = '/queue/new-recipe/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_recipe_id(self):
        '''Tests calling the queue recipe view without the required job type.'''

        json_data = {
            'recipe_data': {},
        }

        url = '/queue/new-recipe/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful(self):
        '''Tests calling the queue recipe view successfully.'''

        recipe_type = recipe_test_utils.create_recipe_type()
        workspace = storage_test_utils.create_workspace()

        recipe_data = {
            'version': '1.0',
            'input_data': [],
            'workspace_id': workspace.id,
        }

        json_data = {
            'recipe_type_id': recipe_type.id,
            'recipe_data': recipe_data,
        }

        url = '/queue/new-recipe/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestQueueStatusView(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        '''Tests successfully calling the queue status view.'''

        url = '/queue/status/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('queue_status' in result, 'Result is missing queue_status field')
        self.assertTrue(isinstance(result['queue_status'], list), 'queue_status must be a list')


class TestRequeueExistingJobView(TestCase):

    def setUp(self):
        django.setup()

        self.job_type = job_test_utils.create_job_type(max_tries=2)
        self.job = job_test_utils.create_job(job_type=self.job_type, data={})

    def test_bad_job_id(self):
        '''Tests calling the requeue view with an invalid job type ID.'''
        json_data = {
            'job_id': 1000,
        }

        url = '/queue/requeue-job/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requeue_canceled(self,):
        '''Tests calling the requeue view successfully for a job that was never queued.'''

        # make sure the job is in the right state despite not actually having been run
        Job.objects.update_status(self.job, 'CANCELED', timezone.now())
        base_count = Queue.objects.count()
        json_data = {
            'job_id': self.job.id,
        }

        url = '/queue/requeue-job/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job.id)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(len(result['job_exes']), 0)

        job = Job.objects.get(id=self.job.id)
        self.assertEqual(job.max_tries, 2)
        self.assertEqual(Queue.objects.count() - base_count, 0)

    def test_requeue_failed(self,):
        '''Tests calling the requeue view successfully for a job that was previously queued.'''

        job_test_utils.create_job_exe(job=self.job, status='FAILED')
        job_test_utils.create_job_exe(job=self.job, status='FAILED')

        # make sure the job is in the right state despite not actually having been run
        Job.objects.update_status(self.job, 'FAILED', timezone.now(), error_test_utils.create_error())
        self.job.num_exes = 2
        self.job.save()

        base_count = Queue.objects.count()
        json_data = {
            'job_id': self.job.id,
        }

        url = '/queue/requeue-job/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job.id)
        self.assertEqual(result['status'], 'QUEUED')
        self.assertEqual(len(result['job_exes']), 3)

        job = Job.objects.get(id=self.job.id)
        self.assertEqual(job.max_tries, 4)
        self.assertEqual(Queue.objects.count() - base_count, 1)

    def test_wrong_status(self,):
        '''Tests calling the requeue view when the job hasn't failed.'''

        job_test_utils.create_job_exe(job=self.job, status='COMPLETED')
        Job.objects.update_status(self.job, 'COMPLETED', timezone.now())

        json_data = {
            'job_id': self.job.id,
        }

        url = '/queue/requeue-job/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        job = Job.objects.get(id=self.job.id)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(job.max_tries, 2)
