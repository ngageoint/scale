from __future__ import unicode_literals

import json

import django
from rest_framework import status

import util.rest as rest_util
from rest_framework.test import APITransactionTestCase
from util import rest


class TestGetUser(APITransactionTestCase):

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

    def test_get_current_user_unauthorized(self):
        """Tests calling the GetUser view without being authenticated."""

        json_data = {
            'num': 10
        }

        url = rest_util.get_url('/accounts/profile/')
        response = self.client.get(url, json.dumps(json_data), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_get_current_user(self):
        """Tests calling the view to create Scale Bake jobs."""

        json_data = {
            'num': 10
        }

        url = rest_util.get_url('/accounts/profile/')
        response = self.client.get(url, json.dumps(json_data), format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)


class TestIsOwnerOrAdmin(APITransactionTestCase):

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
        response = self.client.generic('POST', url, json.dumps(json_data),  format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the view to create Scale Casino recipes."""

        json_data = {
            'num': 10
        }

        url = rest_util.get_url('/diagnostics/recipe/casino/')
        response = self.client.generic('POST', url, json.dumps(json_data),  format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)

class TestUserList(APITransactionTestCase):

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
        response = self.client.generic('POST', url, json.dumps(json_data), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the view to create Scale Hello jobs."""

        json_data = {
            'num': 10
        }

        url = rest_util.get_url('/diagnostics/job/hello/')
        response = self.client.generic('POST', url, json.dumps(json_data), format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)


class TestUserDetail(APITransactionTestCase):

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
        response = self.client.generic('POST', url, json.dumps(json_data), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the view to create Scale Roulette jobs."""

        json_data = {
            'num': 10
        }

        url = rest_util.get_url('/diagnostics/job/roulette/')
        response = self.client.generic('POST', url, json.dumps(json_data), format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED, response.content)
