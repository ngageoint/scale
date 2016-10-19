from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from rest_framework import status

import recipe.test.utils as recipe_test_utils
import batch.test.utils as batch_test_utils
import util.rest as rest_util


class TestBatchesView(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

        self.recipe_type1 = recipe_test_utils.create_recipe_type(name='test1', version='1.0')
        self.batch1 = batch_test_utils.create_batch(recipe_type=self.recipe_type1, status='SUBMITTED')

        self.recipe_type2 = recipe_test_utils.create_recipe_type(name='test2', version='1.0')
        self.batch2 = batch_test_utils.create_batch(recipe_type=self.recipe_type2, status='CREATED')

    def test_successful(self):
        """Tests successfully calling the batches view."""

        url = rest_util.get_url('/batches/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.batch1.id:
                expected = self.batch1
            elif entry['id'] == self.batch2.id:
                expected = self.batch2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['recipe_type']['id'], expected.recipe_type.id)

    def test_status(self):
        """Tests successfully calling the batches view filtered by status."""

        url = rest_util.get_url('/batches/?status=SUBMITTED')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['recipe_type']['id'], self.batch1.recipe_type.id)

    def test_recipe_type_id(self):
        """Tests successfully calling the batches view filtered by recipe type identifier."""

        url = rest_util.get_url('/batches/?recipe_type_id=%s' % self.batch1.recipe_type.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['recipe_type']['id'], self.batch1.recipe_type.id)

    def test_recipe_type_name(self):
        """Tests successfully calling the batches view filtered by recipe type name."""

        url = rest_util.get_url('/batches/?recipe_type_name=%s' % self.batch1.recipe_type.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['recipe_type']['name'], self.batch1.recipe_type.name)

    def test_order_by(self):
        """Tests successfully calling the batches view with sorting."""

        recipe_type1b = recipe_test_utils.create_recipe_type(name='test1', version='2.0')
        batch_test_utils.create_batch(recipe_type=recipe_type1b)

        recipe_type1c = recipe_test_utils.create_recipe_type(name='test1', version='3.0')
        batch_test_utils.create_batch(recipe_type=recipe_type1c)

        url = rest_util.get_url('/batches/?order=recipe_type__name&order=-recipe_type__version')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)
        self.assertEqual(result['results'][0]['recipe_type']['id'], recipe_type1c.id)
        self.assertEqual(result['results'][1]['recipe_type']['id'], recipe_type1b.id)
        self.assertEqual(result['results'][2]['recipe_type']['id'], self.recipe_type1.id)
        self.assertEqual(result['results'][3]['recipe_type']['id'], self.recipe_type2.id)


class TestBatchDetailsView(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

        self.recipe_type = recipe_test_utils.create_recipe_type()
        self.batch = batch_test_utils.create_batch(recipe_type=self.recipe_type)

    def test_not_found(self):
        """Tests successfully calling the get batch details view with a batch id that does not exist."""

        url = rest_util.get_url('/batches/100/')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get batch details view."""

        url = rest_util.get_url('/batches/%d/' % self.batch.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.batch.id)
        self.assertEqual(result['title'], self.batch.title)
        self.assertEqual(result['description'], self.batch.description)
        self.assertEqual(result['status'], self.batch.status)

        self.assertEqual(result['recipe_type']['id'], self.recipe_type.id)
        self.assertIsNotNone(result['event'])
        self.assertIsNotNone(result['creator_job'])
        self.assertIsNotNone(result['definition'])
