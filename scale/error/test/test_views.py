from __future__ import unicode_literals
from __future__ import absolute_import

import json

import django
from django.test import TestCase
from rest_framework import status

import error.test.utils as error_test_utils
import util.rest as rest_util
from error.models import Error
from rest_framework.test import APITestCase
from util import rest

class TestErrorsViewV6(APITestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

        Error.objects.all().delete()  # Need to remove initial errors loaded by fixtures
        error_test_utils.create_error(category='SYSTEM', is_builtin=True)
        error_test_utils.create_error(category='ALGORITHM')
        error_test_utils.create_error(name='data', category='DATA', job_type_name='type-1')

    def test_list_errors(self):
        """Tests successfully calling the get Errors method."""

        url = '/%s/errors/' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

    def test_list_errors_filter_time(self):
        url = '/%s/errors/?started=2017-01-01T00:00:00Z&ended=2017-01-02T00:00:00Z' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        count = results['count']
        self.assertEqual(count, 0)

        url = '/%s/errors/?started=2017-01-01T00:00:00Z&ended=2117-01-02T00:00:00Z' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        count = results['count']
        self.assertEqual(count, 3)

    def test_list_errors_filter_builtin(self):
        """Tests successfully calling the get Errors method."""

        url = '/%s/errors/?is_builtin=true' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 1)

        url = '/%s/errors/?is_builtin=false' % self.api
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(results['count'], 2)

    def test_list_errors_filter_job_type(self):
        url = '/%s/errors/?job_type_name=type-1' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        count = results['count']
        self.assertEqual(count, 1)

    def test_list_errors_filter_name(self):
        url = '/%s/errors/?name=data' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        count = results['count']
        self.assertEqual(count, 1)

    def test_list_errors_filter_category(self):
        url = '/%s/errors/?category=SYSTEM' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        count = results['count']
        self.assertEqual(count, 1)

    def test_create_error(self):
        """Test that the create error API is gone in v6"""

        url = '/%s/errors/' % self.api
        json_data = {
            'name': 'error4',
            'title': 'Error 4',
            'description': 'new error #4',
            'category': 'ALGORITHM',
        }
        response = self.client.post(url, json.dumps(json_data), 'json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)


class TestErrorDetailsViewV6(APITestCase):

    api = 'v6'

    def setUp(self):
        django.setup()

        rest.login_client(self.client, is_staff=True)

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
