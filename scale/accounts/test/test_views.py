from __future__ import unicode_literals

import json

import django
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status

import util.rest as rest_util
from rest_framework.test import APITransactionTestCase, APITestCase
from util import rest


class TestGetUser(APITestCase):

    def setUp(self):
        django.setup()

    def test_get_current_user_unauthorized(self):
        """Tests calling the GetUser view without being authenticated."""

        url = rest_util.get_url('/accounts/profile/')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_current_user(self):
        """Tests calling the GetUser view when authenticated as a basic user."""

        url = rest_util.get_url('/accounts/profile/')
        rest.login_client(self.client, is_staff=False)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_get_current_user_staff(self):
        """Tests calling the GetUser view when authenticated as a staff user."""

        url = rest_util.get_url('/accounts/profile/')
        rest.login_client(self.client, is_staff=True)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)


class TestUserList(APITransactionTestCase):

    def setUp(self):
        django.setup()

    def test_get_user_list_unauthorized(self):
        url = rest_util.get_url('/accounts/users/')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_create_user_unauthorized(self):
        user = {
            'username': 'test',
            'password': 'nope',
            'email': 'test@example.org'
        }

        url = rest_util.get_url('/accounts/users/')
        response = self.client.post(url, data=user, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_user_list_regular_user_unauthorized(self):
        url = rest_util.get_url('/accounts/users/')
        rest.login_client(self.client, is_staff=False)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_create_user_by_id_regular_user_unauthorized(self):
        user = {
            'username': 'test',
            'password': 'nope',
            'email': 'test@example.org'
        }

        url = rest_util.get_url('/accounts/users/')
        rest.login_client(self.client, is_staff=False)
        response = self.client.post(url, data=user, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_user_list_from_staff_user_successful(self):
        url = rest_util.get_url('/accounts/users/')
        rest.login_client(self.client, is_staff=True)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(json.loads(response.content)['results']), 1)

    def test_create_user_from_staff_user_successful(self):
        user = {
            'username': 'sample',
            'password': 'nope',
            'email': 'sample@example.org'
        }

        url = rest_util.get_url('/accounts/users/')
        rest.login_client(self.client, is_staff=True)
        response = self.client.post(url, data=user, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)


class TestUserDetail(APITransactionTestCase):

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
