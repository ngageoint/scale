#@PydevCodeAnalysisIgnore
import json

import django
from django.test import TestCase
from rest_framework import status

from error.models import Error


class TestErrorsView(TestCase):

    def setUp(self):
        django.setup()

        Error.objects.all().delete()  # Need to remove initial errors loaded by fixtures
        self.error1_id = Error.objects.create_error(u'error1', u'Error 1', u'system error #1', u'SYSTEM').id
        self.error2 = Error.objects.create_error(u'error2', u'Error 2', u'algorithm error #2', u'ALGORITHM')
        self.error3_id = Error.objects.create_error(u'error3', u'Error 3', u'data error #3', u'DATA').id

    def test_list_errors(self):
        '''Tests successfully calling the Get Errors method.'''

        url = '/errors/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

    def test_create_error_success(self):
        '''Test sucessfully calling the Create Error method.'''

        url = '/errors/'
        newdata = {'name': 'error4',
                   'title': 'Error 4',
                   'description': 'new error #4',
                   'category': 'ALGORITHM'}
        response = self.client.post(url, json.dumps(newdata), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        data = json.loads(response.content)
        self.assertIn('error_id', data)
        response2 = self.client.get(response['Location'])
        self.assertEqual(response2.status_code, status.HTTP_200_OK, response2.content)
        data = json.loads(response2.content)
        self.assertEqual(newdata['name'], data['name'])
        self.assertEqual(newdata['title'], data['title'])
        self.assertEqual(newdata['description'], data['description'])
        self.assertEqual(newdata['category'], data['category'])

    def test_create_error_missing(self):
        '''Test calling the Create Error method with missing data.'''

        url = '/errors/'
        newdata = {'name': 'error4',
                   'category': 'ALGORITHM'}
        response = self.client.post(url, json.dumps(newdata), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_create_error_bad_category(self):
        '''Test calling the Create Error method with a bad category value.'''

        url = '/errors/'
        newdata = {'name': 'error4',
                   'title': 'Error 4',
                   'description': 'new error #4',
                   'category': 'BAD'}
        response = self.client.post(url, json.dumps(newdata), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestErrorDetailsView(TestCase):

    def setUp(self):
        django.setup()

        Error.objects.all().delete()  # Need to remove initial errors loaded by fixtures
        self.error1_id = Error.objects.create_error(u'error1', u'Error 1', u'system error #1', u'SYSTEM').id
        self.error2 = Error.objects.create_error(u'error2', u'Error 2', u'algorithm error #2', u'ALGORITHM')
        self.error3_id = Error.objects.create_error(u'error3', u'Error 3', u'data error #3', u'DATA').id

    def test_get_error_success(self):
        '''Test successfully calling the Get Error method.'''

        url = '/errors/%d/' % self.error2.id
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        data = json.loads(response.content)
        self.assertIn('name', data)
        self.assertIn('title', data)
        self.assertIn('description', data)
        self.assertIn('category', data)
        self.assertEqual(data['name'], self.error2.name)
        self.assertEqual(data['description'], self.error2.description)
        self.assertEqual(data['category'], self.error2.category)

    def test_get_error_not_found(self):
        '''Test calling the Get Error method with a bad error id.'''

        url = '/errors/9999/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
