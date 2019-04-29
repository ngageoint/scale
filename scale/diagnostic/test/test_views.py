from __future__ import unicode_literals

import json

import django
from django.test import TransactionTestCase
from rest_framework import status
from mock import patch

import util.rest as rest_util
from rest_framework.test import APITransactionTestCase
from util import rest


class TestQueueScaleBakeView(APITransactionTestCase):

    fixtures = ['diagnostic_job_types.json']

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

    def test_bad_num(self):
        """Tests calling the view with a num of 0 (which is invalid)."""

        json_data = {
            'num': 0
        }

        url = rest_util.get_url('/diagnostics/job/bake/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    @patch('queue.models.CommandMessageManager')
    def test_successful(self, mock_msg_mgr):
        """Tests calling the view to create Scale Bake jobs."""

        json_data = {
            'num': 10
        }

        url = rest_util.get_url('/diagnostics/job/bake/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)


class TestQueueScaleCasinoView(APITransactionTestCase):

    fixtures = ['diagnostic_job_types.json', 'diagnostic_recipe_types.json']

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

    def test_bad_num(self):
        """Tests calling the view with a num of 0 (which is invalid)."""

        json_data = {
            'num': 0
        }

        url = rest_util.get_url('/diagnostics/recipe/casino/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    @patch('queue.models.CommandMessageManager')
    def test_successful(self, mock_msg_mgr):
        """Tests calling the view to create Scale Casino recipes."""

        json_data = {
            'num': 10
        }

        url = rest_util.get_url('/diagnostics/recipe/casino/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)

class TestQueueScaleHelloView(APITransactionTestCase):

    fixtures = ['diagnostic_job_types.json']

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

    def test_bad_num(self):
        """Tests calling the view with a num of 0 (which is invalid)."""

        json_data = {
            'num': 0
        }

        url = rest_util.get_url('/diagnostics/job/hello/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    @patch('queue.models.CommandMessageManager')
    def test_successful(self, mock_msg_mgr):
        """Tests calling the view to create Scale Hello jobs."""

        json_data = {
            'num': 10
        }

        url = rest_util.get_url('/diagnostics/job/hello/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)


class TestQueueScaleRouletteView(APITransactionTestCase):

    fixtures = ['diagnostic_job_types.json']

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

    def test_bad_num(self):
        """Tests calling the view with a num of 0 (which is invalid)."""

        json_data = {
            'num': 0
        }

        url = rest_util.get_url('/diagnostics/job/roulette/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    @patch('queue.models.CommandMessageManager')
    def test_successful(self, mock_msg_mgr):
        """Tests calling the view to create Scale Roulette jobs."""

        json_data = {
            'num': 10
        }

        url = rest_util.get_url('/diagnostics/job/roulette/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)
