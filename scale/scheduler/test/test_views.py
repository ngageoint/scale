from __future__ import unicode_literals

import datetime
import json

import django
from django.utils.timezone import now
from rest_framework import status

from rest_framework.test import APITestCase
from scheduler.models import Scheduler
from scheduler.threads.scheduler_status import SchedulerStatusThread
from util import rest
from util.parse import datetime_to_string


class TestSchedulerViewV6(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        Scheduler.objects.create(id=1)

    def test_invalid_version(self):
        """Tests calling the scheduler view with an invalid REST API version"""

        url = '/v1/scheduler/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_get_scheduler_success(self):
        """Test successfully calling the Get Scheduler method."""

        url = '/%s/scheduler/' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertIn('is_paused', result)
        self.assertEqual(result['is_paused'], False)

    def test_get_scheduler_not_found(self):
        """Test calling the Get Scheduler method when the database entry is missing."""

        Scheduler.objects.get_master().delete()

        url = '/%s/scheduler/' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_update_scheduler_success(self):
        """Test successfully calling the Update Scheduler method."""

        json_data = {
            'is_paused': True,
            'num_message_handlers': 10
        }

        url = '/%s/scheduler/' % self.api
        response = self.client.patch(url, json_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_update_scheduler_no_fields(self):
        """Test calling the Update Scheduler method with no fields."""

        json_data = {}

        url = '/%s/scheduler/' % self.api
        response = self.client.patch(url, json_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_update_scheduler_invalid_fields(self):
        """Test calling the Update Scheduler method with invalid fields."""

        json_data = {
            'system_logging_level ': 'BAD'
        }

        url = '/%s/scheduler/' % self.api
        response = self.client.patch(url, json_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_update_scheduler_extra_fields(self):
        """Test calling the Update Scheduler method with extra fields."""

        json_data = {
            'foo': 'bar',
        }

        url = '/%s/scheduler/' % self.api
        response = self.client.patch(url, json_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestStatusView(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()
        Scheduler.objects.create(id=1)

        rest.login_client(self.client)

    def test_status_empty_dict(self):
        """Test getting scheduler status with empty initialization"""

        url = '/%s/status/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_status_old(self):
        """Test getting scheduler status with old data"""

        when = now() - datetime.timedelta(hours=1)
        status_thread = SchedulerStatusThread()
        status_thread._generate_status_json(when)

        url = '/%s/status/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_status_successful(self):
        """Test getting scheduler status successfully"""

        when = now()
        status_thread = SchedulerStatusThread()
        status_thread._generate_status_json(when)

        url = '/%s/status/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        result = json.loads(response.content)
        self.assertEqual(result['timestamp'], datetime_to_string(when))
        self.assertDictEqual(result['vault'], {u'status': u'Secrets Not Configured', u'message': u'', u'sealed': False})


class TestVersionView(APITestCase):
    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client)

    def test_success(self):
        """Test getting overall version/build information successfully"""

        url = '/%s/version/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertIsNotNone(result['version'])
