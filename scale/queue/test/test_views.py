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
from job.models import Job
from queue.models import Queue
from rest_framework.test import APITransactionTestCase, APITestCase
from util import rest


class TestJobLoadView(APITransactionTestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_seed_job_type(priority=1)
        queue_test_utils.create_job_load(job_type=self.job_type1, pending_count=1)
        # sleep's are needed because if the job load entries end up with the same timestamp, there will be fewer
        # entries in the GET then expected in the tests. sleep's ensure the timestamps will be different as they
        # maintain 3 sig figs in the decimal
        time.sleep(0.001)

        self.job_type2 = job_test_utils.create_seed_job_type(priority=2)
        queue_test_utils.create_job_load(job_type=self.job_type2, queued_count=1)
        time.sleep(0.001)

        self.job_type3 = job_test_utils.create_seed_job_type(priority=3)
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

    def test_max_duration(self):
        """Tests calling the job load view with time values that define a range greater than 31 days"""

        url = rest_util.get_url('/load/?started=2015-01-01T00:00:00Z&ended=2015-02-02T00:00:00Z')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestQueueStatusView(APITransactionTestCase):

    def setUp(self):
        django.setup()

        self.job_type = job_test_utils.create_seed_job_type()
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
