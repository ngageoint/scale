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
        """Tests successfully calling the job load view."""

        url = '/load/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 3)

    def test_job_type_id(self):
        """Tests successfully calling the job laod view filtered by job type identifier."""

        url = '/load/?job_type_id=%s' % self.job_type1.id
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['pending_count'], 1)

    def test_job_type_name(self):
        """Tests successfully calling the job load view filtered by job type name."""

        url = '/load/?job_type_name=%s' % self.job_type2.name
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['queued_count'], 1)

    def test_job_type_category(self):
        """Tests successfully calling the job load view filtered by job type category."""

        url = '/load/?job_type_category=%s' % self.job_type3.category
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['running_count'], 1)

    def test_job_type_priority(self):
        """Tests successfully calling the job load view filtered by job type priority."""

        url = '/load/?job_type_priority=%s' % self.job_type1.priority
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['pending_count'], 1)

    def test_max_duration(self):
        """Tests calling the job load view with time values that define a range greater than 31 days"""

        url = '/load/?started=2015-01-01T00:00:00Z&ended=2015-02-02T00:00:00Z'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestQueueNewJobView(TestCase):

    def setUp(self):
        django.setup()

    def test_bad_job_type_id(self):
        """Tests calling the queue status view with an invalid job type ID."""

        json_data = {
            'job_type_id': -1234,
            'job_data': {},
        }

        url = '/queue/new-job/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bad_type_job_type_id(self):
        """Tests calling the queue status view with a string job type ID (which is invalid)."""

        json_data = {
            'job_type_id': 'BAD',
            'job_data': {},
        }

        url = '/queue/new-job/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_job_type_id(self):
        """Tests calling the queue status view without the required job type ID."""

        json_data = {
            'job_data': {},
        }

        url = '/queue/new-job/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('queue.views.JobType.objects.get', lambda pk: job_test_utils.create_job_type())
    def test_bad_type_args(self):
        """Tests calling the queue status view with a string job_data value (which is invalid)."""

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
        """Tests calling the queue status view with invalid job_data for the job."""
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
        """Tests calling the queue status view successfully."""
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
        """Tests calling the queue recipe view with an invalid recipe ID."""

        json_data = {
            'recipe_type_id': -1234,
            'recipe_data': {},
        }

        url = '/queue/new-recipe/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bad_type_recipe_id(self):
        """Tests calling the queue recipe view with a string recipe ID (which is invalid)."""

        json_data = {
            'recipe_id': 'BAD',
            'recipe_data': {},
        }

        url = '/queue/new-recipe/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_recipe_id(self):
        """Tests calling the queue recipe view without the required job type."""

        json_data = {
            'recipe_data': {},
        }

        url = '/queue/new-recipe/'
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful(self):
        """Tests calling the queue recipe view successfully."""

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
        """Tests successfully calling the queue status view."""

        url = '/queue/status/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('queue_status' in result, 'Result is missing queue_status field')
        self.assertTrue(isinstance(result['queue_status'], list), 'queue_status must be a list')


class TestRequeueJobsView(TestCase):

    def setUp(self):
        django.setup()

        self.job_1 = job_test_utils.create_job(status='RUNNING')
        self.job_2 = job_test_utils.create_job(data={})
        self.job_3 = job_test_utils.create_job(status='FAILED')

        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_1.job_type.name,
                    'version': self.job_1.job_type.version,
                }
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_2.job_type.name,
                    'version': self.job_2.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job 1'
                }],
            }],
        }
        self.recipe_type = recipe_test_utils.create_recipe_type(definition=definition)
        self.recipe = recipe_test_utils.create_recipe(recipe_type=self.recipe_type)
        self.recipe_job = recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='Job 1', job=self.job_1)
        self.recipe_job = recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='Job 2', job=self.job_2)

    def test_bad_job_id(self):
        """Tests calling the requeue view with an invalid job type ID."""
        json_data = {
            'job_ids': [1000],
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requeue_canceled(self,):
        """Tests calling the requeue view successfully for a job that was never queued."""

        # make sure the job is in the right state despite not actually having been run
        Job.objects.update_status([self.job_2], 'CANCELED', timezone.now())
        base_count = Queue.objects.count()
        json_data = {
            'job_ids': [self.job_2.id],
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        result = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_2.id)
        self.assertEqual(result['results'][0]['status'], 'PENDING')

        self.assertEqual(Queue.objects.count() - base_count, 0)

    def test_requeue_failed(self,):
        """Tests calling the requeue view successfully for a job that was previously queued."""

        job_test_utils.create_job_exe(job=self.job_2, status='FAILED')
        job_test_utils.create_job_exe(job=self.job_2, status='FAILED')

        # make sure the job is in the right state despite not actually having been run
        Job.objects.update_status([self.job_2], 'FAILED', timezone.now(), error_test_utils.create_error())
        self.job_2.num_exes = 2
        self.job_2.save()

        base_count = Queue.objects.count()
        json_data = {
            'job_ids': [self.job_2.id],
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_2.id)
        self.assertEqual(result['results'][0]['status'], 'QUEUED')

        self.assertEqual(Queue.objects.count() - base_count, 1)

    def test_requeue_ignored(self,):
        """Tests calling the requeue view when the job has already completed."""

        job_test_utils.create_job_exe(job=self.job_2, status='COMPLETED')
        Job.objects.update_status([self.job_2], 'COMPLETED', timezone.now())

        json_data = {
            'job_ids': [self.job_2.id],
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_2.id)
        self.assertEqual(result['results'][0]['status'], 'COMPLETED')

    def test_status(self):
        """Tests successfully calling the requeue view filtered by status."""

        json_data = {
            'status': self.job_3.status,
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_3.id)
        self.assertEqual(result['results'][0]['status'], 'BLOCKED')

    def test_job_ids(self):
        """Tests successfully calling the requeue view filtered by job identifier."""

        json_data = {
            'job_ids': [self.job_3.id],
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_3.id)

    def test_job_type_ids(self):
        """Tests successfully calling the requeue view filtered by job type identifier."""

        json_data = {
            'job_type_ids': [self.job_3.job_type.id],
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job_3.job_type.id)

    def test_job_type_names(self):
        """Tests successfully calling the requeue view filtered by job type name."""

        json_data = {
            'job_type_names': [self.job_3.job_type.name],
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job_3.job_type.name)

    def test_job_type_categories(self):
        """Tests successfully calling the requeue view filtered by job type category."""

        json_data = {
            'job_type_categories': [self.job_3.job_type.category],
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['category'], self.job_3.job_type.category)

    def test_priority(self):
        """Tests successfully calling the requeue view changing the job priority."""

        job_test_utils.create_job_exe(job=self.job_2, status='FAILED')
        job_test_utils.create_job_exe(job=self.job_2, status='FAILED')

        # make sure the job is in the right state despite not actually having been run
        Job.objects.update_status([self.job_2], 'FAILED', timezone.now(), error_test_utils.create_error())
        self.job_2.num_exes = 2
        self.job_2.save()

        json_data = {
            'job_ids': [self.job_2.id],
            'priority': 123,
        }

        url = '/queue/requeue-jobs/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_2.id)
        self.assertEqual(result['results'][0]['status'], 'QUEUED')
        self.assertEqual(result['results'][0]['priority'], 123)


# TODO: Remove this once the UI migrates to /queue/requeue-jobs/
class TestRequeueExistingJobView(TestCase):

    def setUp(self):
        django.setup()

        self.job_1 = job_test_utils.create_job(status='RUNNING')
        self.job_2 = job_test_utils.create_job(data={})

        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [{
                'name': 'Job 1',
                'job_type': {
                    'name': self.job_1.job_type.name,
                    'version': self.job_1.job_type.version,
                }
            }, {
                'name': 'Job 2',
                'job_type': {
                    'name': self.job_2.job_type.name,
                    'version': self.job_2.job_type.version,
                },
                'dependencies': [{
                    'name': 'Job 1'
                }],
            }],
        }
        self.recipe_type = recipe_test_utils.create_recipe_type(definition=definition)
        self.recipe = recipe_test_utils.create_recipe(recipe_type=self.recipe_type)
        self.recipe_job = recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='Job 1', job=self.job_1)
        self.recipe_job = recipe_test_utils.create_recipe_job(recipe=self.recipe, job_name='Job 2', job=self.job_2)

    def test_bad_job_id(self):
        """Tests calling the requeue view with an invalid job type ID."""
        json_data = {
            'job_id': 1000,
        }

        url = '/queue/requeue-job/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_requeue_canceled(self,):
        """Tests calling the requeue view successfully for a job that was never queued."""

        # make sure the job is in the right state despite not actually having been run
        Job.objects.update_status([self.job_2], 'CANCELED', timezone.now())
        base_count = Queue.objects.count()
        json_data = {
            'job_id': self.job_2.id,
        }

        url = '/queue/requeue-job/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job_2.id)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(len(result['job_exes']), 0)

        job = Job.objects.get(id=self.job_2.id)
        self.assertEqual(Queue.objects.count() - base_count, 0)

    def test_requeue_failed(self,):
        """Tests calling the requeue view successfully for a job that was previously queued."""

        job_test_utils.create_job_exe(job=self.job_2, status='FAILED')
        job_test_utils.create_job_exe(job=self.job_2, status='FAILED')

        # make sure the job is in the right state despite not actually having been run
        Job.objects.update_status([self.job_2], 'FAILED', timezone.now(), error_test_utils.create_error())
        self.job_2.num_exes = 2
        self.job_2.save()

        base_count = Queue.objects.count()
        json_data = {
            'job_id': self.job_2.id,
        }

        url = '/queue/requeue-job/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(result['id'], self.job_2.id)
        self.assertEqual(result['status'], 'QUEUED')
        self.assertEqual(len(result['job_exes']), 3)

        job = Job.objects.get(id=self.job_2.id)
        self.assertEqual(Queue.objects.count() - base_count, 1)

    def test_wrong_status(self,):
        """Tests calling the requeue view when the job hasn't failed."""

        job_test_utils.create_job_exe(job=self.job_2, status='COMPLETED')
        Job.objects.update_status([self.job_2], 'COMPLETED', timezone.now())

        json_data = {
            'job_id': self.job_2.id,
        }

        url = '/queue/requeue-job/'
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        job = Job.objects.get(id=self.job_2.id)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
