from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from mock import patch
from rest_framework import status

from mesos_api.api import HardwareResources, MesosError, SchedulerInfo
from scheduler.models import Scheduler


class TestSchedulerView(TestCase):

    def setUp(self):
        django.setup()
        Scheduler.objects.create(id=1)

    def test_get_scheduler_success(self):
        """Test successfully calling the Get Scheduler method."""

        url = '/scheduler/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertIn('is_paused', data)
        self.assertEqual(data['is_paused'], False)

    def test_get_scheduler_not_found(self):
        """Test calling the Get Scheduler method when the database entry is missing."""

        Scheduler.objects.get_master().delete()
        url = '/scheduler/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_scheduler_success(self):
        """Test successfully calling the Update Scheduler method."""

        url = '/scheduler/'
        data = {'is_paused': True}
        response = self.client.patch(url, json.dumps(data), "application/json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)
        self.assertEqual(data['is_paused'], True)

    def test_update_scheduler_no_fields(self):
        """Test calling the Update Scheduler method with no fields."""

        url = '/scheduler/'
        data = {}
        response = self.client.patch(url, json.dumps(data), "application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, '"No fields specified for update."')

    def test_update_scheduler_extra_fields(self):
        """Test calling the Update Scheduler method with extra fields."""

        url = '/scheduler/'
        data = {'foo': 'bar'}
        response = self.client.patch(url, json.dumps(data), "application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, '"Unexpected fields: foo"')


class TestStatusView(TestCase):

    def setUp(self):
        django.setup()
        Scheduler.objects.create(id=1, master_hostname='master', master_port=5050)

    @patch('mesos_api.api.get_scheduler')
    def test_status_success(self, mock_get_scheduler):
        """Test getting overall scheduler status information successfully"""
        mock_get_scheduler.return_value = SchedulerInfo('scheduler', True, HardwareResources(5, 10, 20),
                                                        HardwareResources(1, 2, 3),  HardwareResources())

        url = '/status/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = json.loads(response.content)
        self.assertEqual(results['master']['hostname'], 'master')
        self.assertEqual(results['master']['port'], 5050)
        self.assertTrue(results['master']['is_online'])
        self.assertEqual(results['scheduler']['hostname'], 'scheduler')
        self.assertTrue(results['scheduler']['is_online'])
        self.assertFalse(results['scheduler']['is_paused'])
        self.assertEqual(results['queue_depth'], 0)
        self.assertEqual(results['resources']['total']['cpus'], 5)
        self.assertEqual(results['resources']['scheduled']['cpus'], 1)
        self.assertEqual(results['resources']['used']['cpus'], 0)

    @patch('mesos_api.api.get_scheduler')
    def test_status_no_scheduler(self, mock_get_scheduler):
        """Test getting overall scheduler status information"""
        Scheduler.objects.all().delete()

        url = '/status/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = json.loads(response.content)
        self.assertFalse(results['master']['is_online'])

    @patch('mesos_api.api.get_scheduler')
    def test_status_no_master(self, mock_get_scheduler):
        """Test getting overall scheduler status information"""
        mock_get_scheduler.side_effect = MesosError()

        url = '/status/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = json.loads(response.content)
        self.assertFalse(results['master']['is_online'])


class TestVersionView(TestCase):

    def setUp(self):
        django.setup()

    def test_success(self):
        """Test getting overall version/build information successfully"""
        url = '/version/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(results['version'])
