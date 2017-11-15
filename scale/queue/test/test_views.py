from __future__ import unicode_literals

import json
import time

import django
import django.utils.timezone as timezone
from django.test import TestCase, TransactionTestCase
from rest_framework import status

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import queue.test.utils as queue_test_utils
import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util
from job.configuration.data.job_data import JobData
from job.models import Job
from queue.models import Queue


class TestJobLoadView(TransactionTestCase):

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

        url = rest_util.get_url('/load/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

    def test_job_type_id(self):
        """Tests successfully calling the job laod view filtered by job type identifier."""

        url = rest_util.get_url('/load/?job_type_id=%s' % self.job_type1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['pending_count'], 1)

    def test_job_type_name(self):
        """Tests successfully calling the job load view filtered by job type name."""

        url = rest_util.get_url('/load/?job_type_name=%s' % self.job_type2.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['queued_count'], 1)

    def test_job_type_category(self):
        """Tests successfully calling the job load view filtered by job type category."""

        url = rest_util.get_url('/load/?job_type_category=%s' % self.job_type3.category)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['running_count'], 1)

    def test_job_type_priority(self):
        """Tests successfully calling the job load view filtered by job type priority."""

        url = rest_util.get_url('/load/?job_type_priority=%s' % self.job_type1.priority)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['pending_count'], 1)

    def test_max_duration(self):
        """Tests calling the job load view with time values that define a range greater than 31 days"""

        url = rest_util.get_url('/load/?started=2015-01-01T00:00:00Z&ended=2015-02-02T00:00:00Z')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestQueueNewJobView(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.interface = {
            'version': '1.1',
            'command': 'test_cmd',
            'command_arguments': 'test_arg',
            'input_data': [{
                'media_types': ['image/png'],
                'type': 'file',
                'name': 'input_file',
            }],
            'output_data': [{
                'name': 'output_file',
                'type': 'file',
                'media_type': 'image/png',
            }],
            'shared_resources': [],
        }
        self.job_type = job_test_utils.create_job_type(interface=self.interface)
        self.workspace = storage_test_utils.create_workspace()
        self.file1 = storage_test_utils.create_file(workspace=self.workspace)

    def test_bad_job_type_id(self):
        """Tests calling the queue new job view with an invalid job type ID."""

        json_data = {
            'job_type_id': -1234,
            'job_data': {},
        }

        url = rest_util.get_url('/queue/new-job/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_bad_type_job_type_id(self):
        """Tests calling the queue new job view with a string job type ID (which is invalid)."""

        json_data = {
            'job_type_id': 'BAD',
            'job_data': {},
        }

        url = rest_util.get_url('/queue/new-job/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_job_type_id(self):
        """Tests calling the queue new job view without the required job type ID."""

        json_data = {
            'job_data': {},
        }

        url = rest_util.get_url('/queue/new-job/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_bad_type_args(self):
        """Tests calling the queue new job view with a string job_data value (which is invalid)."""

        json_data = {
            'job_type_id': self.job_type.id,
            'job_data': 'BAD',
        }

        url = rest_util.get_url('/queue/new-job/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_args(self):
        """Tests calling the queue new job view with invalid job_data for the job."""

        json_data = {
            'job_type_id': self.job_type.id,
            'job_data': {},
        }

        url = rest_util.get_url('/queue/new-job/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the queue new job view successfully."""

        json_data = {
            'job_type_id': self.job_type.id,
            'job_data': {
                'version': '1.0',
                'input_data': [{
                    'name': 'input_file',
                    'file_id': self.file1.id,
                }],
                'output_data': [{
                    'name': 'output_file',
                    'workspace_id': self.workspace.id,
                }],
            },
        }
        url = rest_util.get_url('/queue/new-job/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertTrue(response['Location'])
        self.assertEqual(result['job_type']['id'], self.job_type.id)
        self.assertEqual(result['status'], 'QUEUED')
        self.assertEqual(len(result['inputs']), 1)
        self.assertEqual(len(result['outputs']), 1)


class TestQueueNewRecipeView(TestCase):

    def setUp(self):
        django.setup()

    def test_bad_recipe_id(self):
        """Tests calling the queue recipe view with an invalid recipe ID."""

        json_data = {
            'recipe_type_id': -1234,
            'recipe_data': {},
        }

        url = rest_util.get_url('/queue/new-recipe/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_bad_type_recipe_id(self):
        """Tests calling the queue recipe view with a string recipe ID (which is invalid)."""

        json_data = {
            'recipe_id': 'BAD',
            'recipe_data': {},
        }

        url = rest_util.get_url('/queue/new-recipe/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_recipe_id(self):
        """Tests calling the queue recipe view without the required job type."""

        json_data = {
            'recipe_data': {},
        }

        url = rest_util.get_url('/queue/new-recipe/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

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

        url = rest_util.get_url('/queue/new-recipe/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertTrue(response['Location'])
        self.assertEqual(result['recipe_type']['id'], recipe_type.id)


class TestQueueStatusView(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.job_type = job_test_utils.create_job_type()
        self.queue = queue_test_utils.create_queue(job_type=self.job_type, priority=123)

    def test_successful(self):
        """Tests successfully calling the queue status view."""

        url = rest_util.get_url('/queue/status/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job_type.id)
        self.assertEqual(result['results'][0]['count'], 1)
        self.assertEqual(result['results'][0]['highest_priority'], 123)
        self.assertIsNotNone(result['results'][0]['longest_queued'])


class TestRequeueJobsView(TestCase):

    def setUp(self):
        django.setup()

        self.job_1 = job_test_utils.create_job(status='RUNNING', num_exes=1)
        self.job_2 = job_test_utils.create_job(data={}, num_exes=0)
        self.job_3 = job_test_utils.create_job(status='FAILED', num_exes=1)

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

    def test_no_match(self):
        """Tests calling the requeue view where there are no matching jobs to schedule."""
        json_data = {
            'job_ids': [1000],
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 0)

    def test_requeue_canceled(self,):
        """Tests calling the requeue view successfully for a job that was never queued."""

        # make sure the job is in the right state despite not actually having been run
        Job.objects.update_status([self.job_2], 'CANCELED', timezone.now())
        base_count = Queue.objects.count()
        json_data = {
            'job_ids': [self.job_2.id],
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        result = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

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
        self.job_2.data = JobData().get_dict()
        self.job_2.num_exes = 2
        self.job_2.save()

        base_count = Queue.objects.count()
        json_data = {
            'job_ids': [self.job_2.id],
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
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

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_2.id)
        self.assertEqual(result['results'][0]['status'], 'COMPLETED')

    def test_status(self):
        """Tests successfully calling the requeue view filtered by status."""

        json_data = {
            'status': self.job_3.status,
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_3.id)

    def test_job_ids(self):
        """Tests successfully calling the requeue view filtered by job identifier."""

        json_data = {
            'job_ids': [self.job_3.id],
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_3.id)

    def test_job_type_ids(self):
        """Tests successfully calling the requeue view filtered by job type identifier."""

        json_data = {
            'job_type_ids': [self.job_3.job_type.id],
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job_3.job_type.id)

    def test_job_type_names(self):
        """Tests successfully calling the requeue view filtered by job type name."""

        json_data = {
            'job_type_names': [self.job_3.job_type.name],
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job_3.job_type.name)

    def test_job_type_categories(self):
        """Tests successfully calling the requeue view filtered by job type category."""

        json_data = {
            'job_type_categories': [self.job_3.job_type.category],
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['category'], self.job_3.job_type.category)

    def test_error_categories(self):
        """Tests successfully calling the requeue view filtered by job error category."""

        error = error_test_utils.create_error(category='DATA')
        job = job_test_utils.create_job(error=error)

        json_data = {
            'error_categories': [error.category],
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], job.id)
        self.assertEqual(result['results'][0]['error']['category'], error.category)

    def test_priority(self):
        """Tests successfully calling the requeue view changing the queue priority."""

        job_test_utils.create_job_exe(job=self.job_2, status='FAILED')
        job_test_utils.create_job_exe(job=self.job_2, status='FAILED')

        # make sure the job is in the right state despite not actually having been run
        Job.objects.update_status([self.job_2], 'FAILED', timezone.now(), error_test_utils.create_error())
        self.job_2.data = JobData().get_dict()
        self.job_2.num_exes = 2
        self.job_2.save()

        json_data = {
            'job_ids': [self.job_2.id],
            'priority': 123,
        }

        url = rest_util.get_url('/queue/requeue-jobs/')
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job_2.id)
        self.assertEqual(result['results'][0]['status'], 'QUEUED')
        queue = Queue.objects.get(job_id=self.job_2.id)
        self.assertEqual(queue.priority, 123)
