from __future__ import unicode_literals

import json

import django
from django.contrib.auth.models import User
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

        self.user = {
            'username': 'sample',
            'password': 'user',
            'email': 'sample@empty.com'
        }

        user = User.objects.create_user(username='sample', password='user')
        self.client.login(username='sample', password='user')
        self.user_id = user.id

    def test_get_user_unauthorized(self):
        self.client.logout()
        url = rest_util.get_url('/accounts/users/%i/' % (self.user_id,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_edit_user_unauthorized(self):
        self.client.logout()
        url = rest_util.get_url('/accounts/users/%i/' % (self.user_id,))
        response = self.client.patch(url, data=self.user, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_user_unauthorized(self):
        self.client.logout()
        url = rest_util.get_url('/accounts/users/%i/' % (self.user_id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_get_user_self(self):
        url = rest_util.get_url('/accounts/users/%i/' % (self.user_id,))
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_edit_user_self_details(self):
        url = rest_util.get_url('/accounts/users/%i/' % (self.user_id,))
        response = self.client.put(url, data=self.user, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_edit_user_regular_set_staff_unauthorized(self):
        """Validate a regular user cannot promote themselves to staff user"""
        self.user['is_staff'] = True

        url = rest_util.get_url('/accounts/users/%i/' % (self.user_id,))
        response = self.client.put(url, data=self.user, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_edit_user_staff_promote(self):
        """Validate a staff user can promote others to staff user"""
        self.user['is_staff'] = True

        rest.login_client(self.client, is_staff=True)
        url = rest_util.get_url('/accounts/users/%i/' % (self.user_id,))
        response = self.client.put(url, data=self.user, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_delete_user_self(self):
        url = rest_util.get_url('/accounts/users/%i/' % (self.user_id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_delete_user_other_regular_user(self):
        user = User.objects.create_user(username='other')

        url = rest_util.get_url('/accounts/users/%i/' % (user.id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.content)

    def test_delete_user_other_staff_user(self):
        rest.login_client(self.client, is_staff=True)
        url = rest_util.get_url('/accounts/users/%i/' % (self.user_id,))
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
