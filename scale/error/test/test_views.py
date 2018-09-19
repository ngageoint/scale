from __future__ import unicode_literals
from __future__ import absolute_import

import json

import django
from django.test import TestCase
from rest_framework import status

import error.test.utils as error_test_utils
import util.rest as rest_util
from error.models import Error


class TestErrorsViewV5(TestCase):

    api = 'v5'

    def setUp(self):
        django.setup()

        Error.objects.all().delete()  # Need to remove initial errors loaded by fixtures
        error_test_utils.create_error(category='SYSTEM', is_builtin=True)
        error_test_utils.create_error(category='ALGORITHM')
        error_test_utils.create_error(category='DATA')

    def test_list_errors(self):
        """Tests successfully calling the get Errors method."""

        url = '/%s/errors/' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

    def test_create_error_success(self):
        """Test successfully calling the create Error method."""

        url = '/%s/errors/' % self.api
        json_data = {
            'name': 'error4',
            'title': 'Error 4',
            'description': 'new error #4',
            'category': 'ALGORITHM',
        }
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        result = json.loads(response.content)
        self.assertIsNotNone(result['id'])
        self.assertEqual(result['name'], 'error4')
        self.assertEqual(result['title'], 'Error 4')
        self.assertEqual(result['description'], 'new error #4')
        self.assertEqual(result['category'], 'ALGORITHM')
        self.assertFalse(result['is_builtin'])

    def test_create_error_missing(self):
        """Test calling the create Error method with missing data."""

        url = '/%s/errors/' % self.api
        json_data = {
            'name': 'error4',
            'category': 'ALGORITHM',
        }
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_error_bad_category(self):
        """Test calling the create Error method with a bad category value."""

        url = '/%s/errors/' % self.api
        json_data = {
            'name': 'error4',
            'title': 'Error 4',
            'description': 'new error #4',
            'category': 'BAD',
        }
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_error_system(self):
        """Test that system errors cannot be created."""

        url = '/%s/errors/' % self.api
        json_data = {
            'name': 'error4',
            'title': 'Error 4',
            'description': 'new error #4',
            'category': 'SYSTEM',
        }
        response = self.client.post(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

class TestErrorsViewV6(TestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        Error.objects.all().delete()  # Need to remove initial errors loaded by fixtures
        error_test_utils.create_error(category='SYSTEM', is_builtin=True)
        error_test_utils.create_error(category='ALGORITHM')
        error_test_utils.create_error(category='DATA')

    def test_list_errors(self):
        """Tests successfully calling the get Errors method."""

        url = '/%s/errors/' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

    def test_create_error(self):
        """Test that the create error API is gone in v6"""

        url = '/%s/errors/' % self.api
        json_data = {
            'name': 'error4',
            'title': 'Error 4',
            'description': 'new error #4',
            'category': 'ALGORITHM',
        }
        response = self.client.post(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)


class TestErrorDetailsViewV5(TestCase):

    api = 'v5'
    
    def setUp(self):
        django.setup()

        Error.objects.all().delete()  # Need to remove initial errors loaded by fixtures
        self.error1 = error_test_utils.create_error(category='SYSTEM', is_builtin=True)
        self.error2 = error_test_utils.create_error(category='ALGORITHM')
        self.error3 = error_test_utils.create_error(category='DATA')

    def test_get_error_success(self):
        """Test successfully calling the Get Error method."""

        url = '/%s/errors/%d/' % (self.api, self.error1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.error1.id)
        self.assertEqual(result['name'], self.error1.name)
        self.assertEqual(result['title'], self.error1.title)
        self.assertEqual(result['description'], self.error1.description)
        self.assertEqual(result['category'], self.error1.category)
        self.assertTrue(result['is_builtin'])

    def test_get_error_not_found(self):
        """Test calling the Get Error method with a bad error id."""

        url = '/%s/errors/9999/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_edit_error_success(self):
        """Test successfully calling the edit Error method."""

        url = '/%s/errors/%d/' % (self.api, self.error2.id)
        json_data = {
            'title': 'error EDIT',
        }
        response = self.client.patch(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.error2.id)
        self.assertEqual(result['name'], self.error2.name)
        self.assertEqual(result['title'], 'error EDIT')
        self.assertEqual(result['description'], self.error2.description)
        self.assertEqual(result['category'], self.error2.category)
        self.assertFalse(result['is_builtin'])

        error = Error.objects.get(pk=self.error2.id)
        self.assertEqual(error.title, 'error EDIT')

    def test_edit_error_not_found(self):
        """Test calling the edit Error method with a bad error id."""

        url = '/%s/errors/9999/' % self.api
        json_data = {
            'title': 'error EDIT',
        }
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_edit_error_bad_category(self):
        """Test calling the edit Error method with a bad category."""

        url = '/%s/errors/%d/' % (self.api, self.error2.id)
        json_data = {
            'category': 'BAD',
        }
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_edit_error_system(self):
        """Test that an existing system error cannot be edited."""

        url = '/%s/errors/%d/' % (self.api, self.error1.id)
        json_data = {
            'title': 'error EDIT',
        }
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_edit_error_change_system(self):
        """Test that an existing error cannot be changed to a system level error."""

        url = '/%s/errors/%d/' % (self.api, self.error2.id)
        json_data = {
            'category': 'SYSTEM',
        }
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

class TestErrorDetailsViewV6(TestCase):

    api = 'v6'
    
    def setUp(self):
        django.setup()

        Error.objects.all().delete()  # Need to remove initial errors loaded by fixtures
        self.error1 = error_test_utils.create_error(category='SYSTEM', is_builtin=True)
        self.error2 = error_test_utils.create_error(category='ALGORITHM')
        self.error3 = error_test_utils.create_error(category='DATA')

    def test_get_error_success(self):
        """Test successfully calling the Get Error method."""

        url = '/%s/errors/%d/' % (self.api, self.error1.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.error1.id)
        self.assertEqual(result['name'], self.error1.name)
        self.assertEqual(result['title'], self.error1.title)
        self.assertEqual(result['description'], self.error1.description)
        self.assertEqual(result['category'], self.error1.category)
        self.assertTrue(result['is_builtin'])

    def test_get_error_not_found(self):
        """Test calling the Get Error method with a bad error id."""

        url = '/%s/errors/9999/' % self.api
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_edit_error(self):
        """Test that the edit error api is removed in v6."""

        url = '/%s/errors/%d/' % (self.api, self.error2.id)
        json_data = {
            'title': 'error EDIT',
        }
        response = self.client.patch(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)
