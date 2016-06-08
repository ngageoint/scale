from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from rest_framework import status

import source.test.utils as source_test_utils


class TestSourcesView(TestCase):

    def setUp(self):
        django.setup()

        self.source1 = source_test_utils.create_source(is_parsed=True, file_name='test.txt')
        self.source2 = source_test_utils.create_source(is_parsed=False)

    def test_invalid_started(self):
        """Tests calling the source files view when the started parameter is invalid."""

        url = '/sources/?started=hello'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_tz_started(self):
        """Tests calling the source files view when the started parameter is missing timezone."""

        url = '/sources/?started=1970-01-01T00:00:00'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_ended(self):
        """Tests calling the source files view when the ended parameter is invalid."""

        url = '/sources/?started=1970-01-01T00:00:00Z&ended=hello'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_tz_ended(self):
        """Tests calling the source files view when the ended parameter is missing timezone."""

        url = '/sources/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_time_range(self):
        """Tests calling the source files view with a negative time range."""

        url = '/sources/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_is_parsed(self):
        """Tests successfully calling the source files view filtered by is_parsed flag."""

        url = '/sources/?is_parsed=true'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['is_parsed'], self.source1.is_parsed)

    def test_file_name(self):
        """Tests successfully calling the source files view filtered by file name."""

        url = '/sources/?file_name=test.txt'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.source1.file_name)

    def test_successful(self):
        """Tests successfully calling the source files view."""

        url = '/sources/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)


class TestSourceDetailsView(TestCase):

    def setUp(self):
        django.setup()

        self.source = source_test_utils.create_source()

        try:
            import ingest.test.utils as ingest_test_utils
            self.ingest = ingest_test_utils.create_ingest(source_file=self.source)
        except:
            self.ingest = None

        try:
            import product.test.utils as product_test_utils
            self.product = product_test_utils.create_product()

            product_test_utils.create_file_link(ancestor=self.source, descendant=self.product)
        except:
            self.product = None

    def test_id(self):
        """Tests successfully calling the source files view by id."""

        url = '/sources/%i/' % self.source.id
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(result['id'], self.source.id)
        self.assertEqual(result['file_name'], self.source.file_name)

        if self.ingest:
            self.assertEqual(len(result['ingests']), 1)
            self.assertEqual(result['ingests'][0]['id'], self.ingest.id)

        if self.product:
            self.assertEqual(len(result['products']), 1)
            self.assertEqual(result['products'][0]['id'], self.product.id)

    def test_file_name(self):
        """Tests successfully calling the source files view by file name."""

        url = '/sources/%s/' % self.source.file_name
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(result['id'], self.source.id)
        self.assertEqual(result['file_name'], self.source.file_name)

        if self.ingest:
            self.assertEqual(len(result['ingests']), 1)
            self.assertEqual(result['ingests'][0]['id'], self.ingest.id)

        if self.product:
            self.assertEqual(len(result['products']), 1)
            self.assertEqual(result['products'][0]['id'], self.product.id)

    def test_missing(self):
        """Tests calling the source files view with an invalid id or file name."""

        url = '/sources/12345/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url = '/sources/missing_file.txt/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestSourceUpdatesView(TestCase):

    def setUp(self):
        django.setup()

        self.source1 = source_test_utils.create_source(file_name='test.txt', is_parsed=True)
        self.source2 = source_test_utils.create_source(is_parsed=False)

    def test_invalid_started(self):
        """Tests calling the source file updates view when the started parameter is invalid."""

        url = '/sources/updates/?started=hello'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_tz_started(self):
        """Tests calling the source file updates view when the started parameter is missing timezone."""

        url = '/sources/updates/?started=1970-01-01T00:00:00'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_ended(self):
        """Tests calling the source file updates view when the ended parameter is invalid."""

        url = '/sources/updates/?started=1970-01-01T00:00:00Z&ended=hello'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_tz_ended(self):
        """Tests calling the source file updates view when the ended parameter is missing timezone."""

        url = '/sources/updates/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_time_range(self):
        """Tests calling the source file updates view with a negative time range."""

        url = '/sources/updates/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00'
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_is_parsed(self):
        """Tests successfully calling the source files view filtered by is_parsed flag."""

        url = '/sources/updates/?is_parsed=true'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['is_parsed'], self.source1.is_parsed)

    def test_file_name(self):
        """Tests successfully calling the source file updates view filtered by file name."""

        url = '/sources/updates/?file_name=test.txt'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.source1.file_name)

    def test_successful(self):
        """Tests successfully calling the source file updates view."""

        url = '/sources/updates/'
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)

        for entry in result['results']:
            self.assertIsNotNone(entry['update'])
