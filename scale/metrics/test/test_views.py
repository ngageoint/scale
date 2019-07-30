from __future__ import unicode_literals
from __future__ import absolute_import

import json

import django
import django.utils.timezone as timezone
import datetime
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase

import job.test.utils as job_test_utils
import metrics.test.utils as metrics_test_utils
from util import rest


class TestMetricsViewV6(APITestCase):

    def setUp(self):
        django.setup()

        rest.login_client(self.client)

    def test_successful(self):
        """Tests successfully calling the metrics view."""

        url = '/v6/metrics/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertGreaterEqual(len(result['results']), 1)
        for entry in result['results']:
            if entry['name'] == 'job-types':
                self.assertGreaterEqual(len(entry['groups']), 1)
                self.assertGreaterEqual(len(entry['columns']), 1)
                self.assertFalse('choices' in entry)


class TestMetricsViewV6(APITestCase):

    def setUp(self):
        django.setup()

        rest.login_client(self.client)

    def test_successful(self):
        """Tests successfully calling the metrics view."""

        url = '/v6/metrics/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertGreaterEqual(len(result['results']), 1)
        for entry in result['results']:
            if entry['name'] == 'job-types':
                self.assertGreaterEqual(len(entry['groups']), 1)
                self.assertGreaterEqual(len(entry['columns']), 1)
                self.assertFalse('choices' in entry)


class TestMetricDetailsViewV6(APITransactionTestCase):

    def setUp(self):
        django.setup()

        rest.login_client(self.client)

        job_test_utils.create_seed_job_type()

    def test_successful(self):
        """Tests successfully calling the metric details view."""

        url = '/v6/metrics/job-types/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['name'], 'job-types')
        self.assertGreaterEqual(len(result['groups']), 1)
        self.assertGreaterEqual(len(result['columns']), 1)
        self.assertEqual(len(result['choices']), 1)


class TestMetricPlotViewV6(APITransactionTestCase):

    def setUp(self):
        django.setup()

        rest.login_client(self.client)

        self.job_type1 = job_test_utils.create_seed_job_type()
        metrics_test_utils.create_job_type(job_type=self.job_type1, completed_count=8, failed_count=2, total_count=10)

        self.job_type2 = job_test_utils.create_seed_job_type()
        metrics_test_utils.create_job_type(job_type=self.job_type2, job_time_sum=220, job_time_min=20, job_time_max=200,
                                           job_time_avg=110)

        self.job_type3 = job_test_utils.create_seed_job_type()
        metrics_test_utils.create_job_type(job_type=self.job_type3, job_time_sum=1100, job_time_min=100,
                                           job_time_max=1000, job_time_avg=550)

    def test_successful(self):
        """Tests successfully calling the metric plot view."""

        url = '/v6/metrics/job-types/plot-data/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertGreaterEqual(len(result['results']), 1)

        for entry in result['results']:
            self.assertIsNotNone(entry['values'])
            if entry['values']:
                self.assertIsNotNone(entry['column'])
                self.assertIsNotNone(entry['min_x'])
                self.assertIsNotNone(entry['max_x'])
                self.assertIsNotNone(entry['min_y'])
                self.assertIsNotNone(entry['max_y'])
                self.assertFalse('id' in entry['values'][0])

    def test_choices(self):
        """Tests successfully calling the metric plot view with choice filters."""

        url = '/v6/metrics/job-types/plot-data/?choice_id=%s&choice_id=%s' % (self.job_type1.id, self.job_type2.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertGreaterEqual(len(result['results']), 1)

        job_type_ids = [self.job_type1.id, self.job_type2.id]
        for entry in result['results']:
            self.assertIsNotNone(entry['values'])
            if entry['values']:
                self.assertIsNotNone(entry['column'])
                self.assertIsNotNone(entry['min_x'])
                self.assertIsNotNone(entry['max_x'])
                self.assertIsNotNone(entry['min_y'])
                self.assertIsNotNone(entry['max_y'])
                self.assertIn(entry['values'][0]['id'], job_type_ids)

    def test_columns(self):
        """Tests successfully calling the metric plot view with column filters."""

        url = '/v6/metrics/job-types/plot-data/?column=completed_count&column=failed_count'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

    def test_groups(self):
        """Tests successfully calling the metric plot view with group filters."""

        url = '/v6/metrics/job-types/plot-data/?group=overview'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)

    def test_aggregate_sum(self):
        """Tests successfully calling the metric plot view using a sum aggregate."""

        url = '/v6/metrics/job-types/plot-data/?column=job_time_sum'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['values'][0]['value'], 1320)

    def test_aggregate_min(self):
        """Tests successfully calling the metric plot view using a minimum aggregate."""

        url = '/v6/metrics/job-types/plot-data/?column=job_time_min'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['values'][0]['value'], 20)

    def test_aggregate_max(self):
        """Tests successfully calling the metric plot view using a maximum aggregate."""

        url = '/v6/metrics/job-types/plot-data/?column=job_time_max'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['values'][0]['value'], 1000)

    def test_aggregate_avg(self):
        """Tests successfully calling the metric plot view using an average aggregate."""

        url = '/v6/metrics/job-types/plot-data/?column=job_time_avg'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['values'][0]['value'], 330)

    def test_by_hour(self):
        """Tests successfully binning the metric plot view by hour."""
        
        # Create job type for two hours prior
        job_type4 = job_test_utils.create_seed_job_type()
        occurred = timezone.now() - datetime.timedelta(hours=2)
        metrics_test_utils.create_job_type(job_type=job_type4, occurred=occurred, job_time_sum=2200, job_time_min=200,
                                           job_time_max=2000, job_time_avg=200)
        
        # Create job type for one hour prior
        job_type5 = job_test_utils.create_seed_job_type()
        occurred = timezone.now() - datetime.timedelta(hours=1)
        metrics_test_utils.create_job_type(job_type=job_type5, occurred=occurred, job_time_sum=1100, job_time_min=100,
                                           job_time_max=1000, job_time_avg=100)

        url = '/v6/metrics/job-types/plot-data/?column=job_time_avg'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(len(result['results'][0]['values']), 3)
        