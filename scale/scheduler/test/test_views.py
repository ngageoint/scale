from __future__ import unicode_literals

import datetime
import json

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import patch
from rest_framework import status

import util.rest as rest_util
from mesos_api.api import HardwareResources, MesosError, SchedulerInfo
from scheduler.models import Scheduler
from scheduler.threads.scheduler_status import SchedulerStatusThread
from util.parse import datetime_to_string


class TestSchedulerView(TestCase):

    def setUp(self):
        django.setup()
        Scheduler.objects.create(id=1)

    def test_get_scheduler_success(self):
        """Test successfully calling the Get Scheduler method."""

        url = rest_util.get_url('/scheduler/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertIn('is_paused', result)
        self.assertEqual(result['is_paused'], False)

    def test_get_scheduler_not_found(self):
        """Test calling the Get Scheduler method when the database entry is missing."""

        Scheduler.objects.get_master().delete()

        url = rest_util.get_url('/scheduler/')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_update_scheduler_success(self):
        """Test successfully calling the Update Scheduler method."""

        json_data = {
            'is_paused': True,
            'num_message_handlers': 10
        }

        url = rest_util.get_url('/scheduler/')
        response = self.client.patch(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['is_paused'], True)
        self.assertEqual(result['num_message_handlers'], 10)

    def test_update_scheduler_no_fields(self):
        """Test calling the Update Scheduler method with no fields."""

        json_data = {}

        url = rest_util.get_url('/scheduler/')
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_update_scheduler_extra_fields(self):
        """Test calling the Update Scheduler method with extra fields."""

        json_data = {
            'foo': 'bar',
        }

        url = rest_util.get_url('/scheduler/')
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestStatusView(TestCase):

    def setUp(self):
        django.setup()
        Scheduler.objects.create(id=1, master_hostname='master', master_port=5050)

    def test_status_empty_dict(self):
        """Test getting scheduler status with empty initialization"""

        # url = rest_util.get_url('/status/')
        url = '/v5/status/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
        
        url = '/v6/status/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_status_old(self):
        """Test getting scheduler status with old data"""

        when = now() - datetime.timedelta(hours=1)
        status_thread = SchedulerStatusThread()
        status_thread._generate_status_json(when)

        # url = rest_util.get_url('/status/')
        url = '/v5/status/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
        
        url = '/v6/status/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_status_successful(self):
        """Test getting scheduler status successfully"""

        when = now()
        status_thread = SchedulerStatusThread()
        status_thread._generate_status_json(when)

        # url = rest_util.get_url('/status/')
        url = '/v5/status/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(result['timestamp'], datetime_to_string(when))
        
        url = '/v6/status/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(result['timestamp'], datetime_to_string(when))

    # TODO: remove when REST API v4 is removed
    @patch('mesos_api.api.get_scheduler')
    def test_status_success_v4(self, mock_get_scheduler):
        """Test getting overall scheduler status information successfully"""
        mock_get_scheduler.return_value = SchedulerInfo('scheduler', True, HardwareResources(5, 10, 20),
                                                        HardwareResources(1, 2, 3),  HardwareResources())

        response = self.client.generic('GET', '/v4/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['master']['hostname'], 'master')
        self.assertEqual(result['master']['port'], 5050)
        self.assertTrue(result['master']['is_online'])
        self.assertEqual(result['scheduler']['hostname'], 'scheduler')
        self.assertTrue(result['scheduler']['is_online'])
        self.assertFalse(result['scheduler']['is_paused'])
        self.assertEqual(result['queue_depth'], 0)
        self.assertEqual(result['resources']['total']['cpus'], 5)
        self.assertEqual(result['resources']['scheduled']['cpus'], 1)
        self.assertEqual(result['resources']['used']['cpus'], 0)

    # TODO: remove when REST API v4 is removed
    @patch('mesos_api.api.get_scheduler')
    def test_status_no_scheduler_v4(self, mock_get_scheduler):
        """Test getting overall scheduler status information"""
        Scheduler.objects.all().delete()

        response = self.client.generic('GET', '/v4/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertFalse(result['master']['is_online'])

    # TODO: remove when REST API v4 is removed
    @patch('mesos_api.api.get_scheduler')
    def test_status_no_master_v4(self, mock_get_scheduler):
        """Test getting overall scheduler status information"""
        mock_get_scheduler.side_effect = MesosError()

        response = self.client.generic('GET', '/v4/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertFalse(result['master']['is_online'])


class TestVersionView(TestCase):

    def setUp(self):
        django.setup()

    def test_success(self):
        """Test getting overall version/build information successfully"""
        
        # TODO: remove when REST API v4 is removed
        url = '/v4/version/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertIsNotNone(result['version'])
        
        url = '/v5/version/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertIsNotNone(result['version'])
        
        url = '/v6/version/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertIsNotNone(result['version'])
