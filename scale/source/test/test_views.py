from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from rest_framework import status

import job.test.utils as job_test_utils
import source.test.utils as source_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util


class TestSourcesView(TestCase):

    def setUp(self):
        django.setup()

        self.source1 = source_test_utils.create_source(data_started='2016-01-01T00:00:00Z',
                                                       data_ended='2016-01-01T00:00:00Z', is_parsed=True,
                                                       file_name='test.txt')
        self.source2 = source_test_utils.create_source(data_started='2017-01-01T00:00:00Z',
                                                       data_ended='2017-01-01T00:00:00Z', is_parsed=False)

    def test_invalid_started(self):
        """Tests calling the source files view when the started parameter is invalid."""

        url = rest_util.get_url('/sources/?started=hello')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the source files view when the started parameter is missing timezone."""

        url = rest_util.get_url('/sources/?started=1970-01-01T00:00:00')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the source files view when the ended parameter is invalid."""

        url = rest_util.get_url('/sources/?started=1970-01-01T00:00:00Z&ended=hello')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the source files view when the ended parameter is missing timezone."""

        url = rest_util.get_url('/sources/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the source files view with a negative time range."""

        url = rest_util.get_url('/sources/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_time_field(self):
        """Tests calling the source files view when the time_field parameter is invalid."""

        url = rest_util.get_url('/sources/?started=1970-01-01T00:00:00Z&time_field=hello')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_time_field(self):
        """Tests successfully calling the source files view using the time_field parameter"""

        url = rest_util.get_url('/sources/?started=2016-02-01T00:00:00Z&time_field=data')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

    def test_is_parsed(self):
        """Tests successfully calling the source files view filtered by is_parsed flag."""

        url = rest_util.get_url('/sources/?is_parsed=true')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['is_parsed'], self.source1.is_parsed)

    def test_file_name(self):
        """Tests successfully calling the source files view filtered by file name."""

        url = rest_util.get_url('/sources/?file_name=test.txt')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.source1.file_name)

    def test_successful(self):
        """Tests successfully calling the source files view."""

        url = rest_util.get_url('/sources/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
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
            self.product1 = product_test_utils.create_product(is_superseded=True)

            product_test_utils.create_file_link(ancestor=self.source, descendant=self.product1)
        except:
            self.product1 = None

        try:
            import product.test.utils as product_test_utils
            self.product2 = product_test_utils.create_product()

            product_test_utils.create_file_link(ancestor=self.source, descendant=self.product2)
        except:
            self.product2 = None

    def test_id(self):
        """Tests successfully calling the source files view by id."""

        url = rest_util.get_url('/sources/%i/' % self.source.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.source.id)
        self.assertEqual(result['file_name'], self.source.file_name)

        if self.ingest:
            self.assertEqual(len(result['ingests']), 1)
            self.assertEqual(result['ingests'][0]['id'], self.ingest.id)

        if self.product2:
            self.assertEqual(len(result['products']), 1)
            self.assertEqual(result['products'][0]['id'], self.product2.id)

    def test_file_name(self):
        """Tests successfully calling the source files view by file name."""

        url = rest_util.get_url('/sources/%s/' % self.source.file_name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.source.id)
        self.assertEqual(result['file_name'], self.source.file_name)

        if self.ingest:
            self.assertEqual(len(result['ingests']), 1)
            self.assertEqual(result['ingests'][0]['id'], self.ingest.id)

        if self.product2:
            self.assertEqual(len(result['products']), 1)
            self.assertEqual(result['products'][0]['id'], self.product2.id)

    def test_missing(self):
        """Tests calling the source files view with an invalid id or file name."""

        url = rest_util.get_url('/sources/12345/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

        url = rest_util.get_url('/sources/missing_file.txt/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_superseded(self):
        """Tests successfully calling the source files view filtered by superseded."""

        url = rest_util.get_url('/sources/%i/?include_superseded=true' % self.source.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.source.id)

        if self.product1 and self.product2:
            self.assertEqual(len(result['products']), 2)
            for product in result['products']:
                self.assertIn(product['id'], [self.product1.id, self.product2.id])


class TestSourceProductsView(TestCase):

    fixtures = ['batch_job_types.json']

    def setUp(self):
        django.setup()

        from batch.test import utils as batch_test_utils
        from product.test import utils as product_test_utils
        self.country = storage_test_utils.create_country()
        self.src_file = source_test_utils.create_source()
        self.job_type1 = job_test_utils.create_job_type(name='test1', category='test-1', is_operational=True)
        self.job1 = job_test_utils.create_job(job_type=self.job_type1)
        self.job_exe1 = job_test_utils.create_job_exe(job=self.job1)
        self.product1 = product_test_utils.create_product(job_exe=self.job_exe1, has_been_published=True,
                                                          is_published=True, file_name='test.txt',
                                                          countries=[self.country])
        product_test_utils.create_file_link(ancestor=self.src_file, descendant=self.product1, job=self.job1,
                                            job_exe=self.job_exe1)

        self.batch = batch_test_utils.create_batch()
        self.job_type2 = job_test_utils.create_job_type(name='test2', category='test-2', is_operational=False)
        self.job2 = job_test_utils.create_job(job_type=self.job_type2)
        self.job_exe2 = job_test_utils.create_job_exe(job=self.job2)
        self.product2a = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=False, countries=[self.country])
        product_test_utils.create_file_link(ancestor=self.src_file, descendant=self.product2a, job=self.job2,
                                            job_exe=self.job_exe2, batch=self.batch)

        self.product2b = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=True, is_superseded=True,
                                                           countries=[self.country])
        product_test_utils.create_file_link(ancestor=self.src_file, descendant=self.product2b, job=self.job2,
                                            job_exe=self.job_exe2, batch=self.batch)

        self.product2c = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=True, countries=[self.country])
        product_test_utils.create_file_link(ancestor=self.src_file, descendant=self.product2c, job=self.job2,
                                            job_exe=self.job_exe2, batch=self.batch)

    def test_invalid_source_id(self):
        """Tests calling the source products view when the source ID is invalid."""

        url = rest_util.get_url('/sources/12345678/products/')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_invalid_started(self):
        """Tests calling the source products view when the started parameter is invalid."""

        url = rest_util.get_url('/sources/%d/products/?started=hello' % self.src_file.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the source products view when the started parameter is missing timezone."""

        url = rest_util.get_url('/sources/%d/products/?started=1970-01-01T00:00:00' % self.src_file.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the source products view when the ended parameter is invalid."""

        url = rest_util.get_url('/sources/%d/products/?started=1970-01-01T00:00:00Z&ended=hello' % self.src_file.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the source products view when the ended parameter is missing timezone."""

        url = '/sources/%d/products/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00' % self.src_file.id
        url = rest_util.get_url(url)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the source products view with a negative time range."""

        url = '/sources/%d/products/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00' % self.src_file.id
        url = rest_util.get_url(url)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_batch_id(self):
        """Tests successfully calling the source products view filtered by batch identifier."""

        url = rest_util.get_url('/sources/%d/products/?batch_id=%s' % (self.src_file.id, self.batch.id))
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

    def test_job_type_id(self):
        """Tests successfully calling the source products view filtered by job type identifier."""

        url = rest_util.get_url('/sources/%d/products/?job_type_id=%s' % (self.src_file.id, self.job_type1.id))
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job_type1.id)

    def test_job_type_name(self):
        """Tests successfully calling the source products view filtered by job type name."""

        url = rest_util.get_url('/sources/%d/products/?job_type_name=%s' % (self.src_file.id,  self.job_type1.name))
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job_type1.name)

    def test_job_type_category(self):
        """Tests successfully calling the source products view filtered by job type category."""

        url = '/sources/%d/products/?job_type_category=%s' % (self.src_file.id, self.job_type1.category)
        url = rest_util.get_url(url)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['category'], self.job_type1.category)

    def test_is_operational(self):
        """Tests successfully calling the source products view filtered by is_operational flag."""

        url = rest_util.get_url('/sources/%d/products/?is_operational=true' % self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['is_operational'], self.job_type1.is_operational)

    def test_is_published(self):
        """Tests successfully calling the source products view filtered by is_published flag."""

        url = rest_util.get_url('/sources/%d/products/?is_published=false' % self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.product2a.id)
        self.assertFalse(result['results'][0]['is_published'])

    def test_file_name(self):
        """Tests successfully calling the source products view filtered by file name."""

        url = rest_util.get_url('/sources/%d/products/?file_name=test.txt' % self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.product1.file_name)

    def test_successful(self):
        """Tests successfully calling the source products view."""

        url = rest_util.get_url('/sources/%d/products/' % self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)

        for entry in result['results']:
            # Make sure country info is included
            self.assertEqual(entry['countries'][0], self.country.iso3)


class TestSourceUpdatesView(TestCase):

    def setUp(self):
        django.setup()

        self.source1 = source_test_utils.create_source(data_started='2016-01-01T00:00:00Z',
                                                       data_ended='2016-01-01T00:00:00Z', file_name='test.txt',
                                                       is_parsed=True)
        self.source2 = source_test_utils.create_source(data_started='2017-01-01T00:00:00Z',
                                                       data_ended='2017-01-01T00:00:00Z', is_parsed=False)

    def test_invalid_started(self):
        """Tests calling the source file updates view when the started parameter is invalid."""

        url = rest_util.get_url('/sources/updates/?started=hello')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the source file updates view when the started parameter is missing timezone."""

        url = rest_util.get_url('/sources/updates/?started=1970-01-01T00:00:00')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the source file updates view when the ended parameter is invalid."""

        url = rest_util.get_url('/sources/updates/?started=1970-01-01T00:00:00Z&ended=hello')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the source file updates view when the ended parameter is missing timezone."""

        url = rest_util.get_url('/sources/updates/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the source file updates view with a negative time range."""

        url = rest_util.get_url('/sources/updates/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_time_field(self):
        """Tests calling the source file updates view when the time_field parameter is invalid."""

        url = rest_util.get_url('/sources/updates/?started=1970-01-01T00:00:00Z&time_field=hello')
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_time_field(self):
        """Tests successfully calling the source file updates view using the time_field parameter"""

        url = rest_util.get_url('/sources/updates/?started=2016-02-01T00:00:00Z&time_field=data')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

    def test_is_parsed(self):
        """Tests successfully calling the source files view filtered by is_parsed flag."""

        url = rest_util.get_url('/sources/updates/?is_parsed=true')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['is_parsed'], self.source1.is_parsed)

    def test_file_name(self):
        """Tests successfully calling the source file updates view filtered by file name."""

        url = rest_util.get_url('/sources/updates/?file_name=test.txt')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.source1.file_name)

    def test_successful(self):
        """Tests successfully calling the source file updates view."""

        url = rest_util.get_url('/sources/updates/')
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

        for entry in result['results']:
            self.assertIsNotNone(entry['update'])
