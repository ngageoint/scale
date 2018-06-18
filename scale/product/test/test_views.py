from __future__ import unicode_literals

import json

import django
from django.test import TestCase, TransactionTestCase
from rest_framework import status

import job.test.utils as job_test_utils
import product.test.utils as product_test_utils
import source.test.utils as source_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util

# TODO: remove when REST API v5 is removed
class TestProductsViewV5(TransactionTestCase):

    api = 'v5'
    
    def setUp(self):
        django.setup()

        self.country = storage_test_utils.create_country()
        self.job_type1 = job_test_utils.create_job_type(name='test1', category='test-1', is_operational=True)
        self.job1 = job_test_utils.create_job(job_type=self.job_type1)
        self.job_exe1 = job_test_utils.create_job_exe(job=self.job1)
        self.product1 = product_test_utils.create_product(job_exe=self.job_exe1, has_been_published=True,
                                                          is_published=True, file_name='test.txt',
                                                          countries=[self.country])

        self.job_type2 = job_test_utils.create_job_type(name='test2', category='test-2', is_operational=False)
        self.job2 = job_test_utils.create_job(job_type=self.job_type2)
        self.job_exe2 = job_test_utils.create_job_exe(job=self.job2)
        self.product2a = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=False, countries=[self.country])

        self.product2b = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=True, is_superseded=True,
                                                           countries=[self.country])

        self.product2c = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=True, countries=[self.country])

    def test_invalid_started(self):
        """Tests calling the product files view when the started parameter is invalid."""

        url = '/%s/products/?started=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the product files view when the started parameter is missing timezone."""

        url = '/%s/products/?started=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the product files view when the ended parameter is invalid."""

        url = '/%s/products/?started=1970-01-01T00:00:00Z&ended=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the product files view when the ended parameter is missing timezone."""

        url = '/%s/products/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the product files view with a negative time range."""

        url = '/%s/products/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_job_type_id(self):
        """Tests successfully calling the product files view filtered by job type identifier."""

        url = '/%s/products/?job_type_id=%s' % (self.api, self.job_type1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job_type1.id)

    def test_job_type_name(self):
        """Tests successfully calling the product files view filtered by job type name."""

        url = '/%s/products/?job_type_name=%s' % (self.api, self.job_type1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job_type1.name)

    # TODO: Remove when v5 deprecated
    def test_job_type_legacy_category(self):
        """Tests successfully calling the product files view filtered by job type category."""

        url = '/%s/products/?job_type_category=%s' % (self.api, self.job_type1.category)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['category'], self.job_type1.category)

    def test_is_operational(self):
        """Tests successfully calling the product files view filtered by is_operational flag."""

        url = '/%s/products/?is_operational=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['is_operational'], self.job_type1.is_operational)

    def test_is_published(self):
        """Tests successfully calling the product files view filtered by is_published flag."""

        url = '/%s/products/?is_published=false' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.product2a.id)
        self.assertFalse(result['results'][0]['is_published'])

    def test_file_name(self):
        """Tests successfully calling the product files view filtered by file name."""

        url = '/%s/products/?file_name=test.txt' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.product1.file_name)

    def test_successful(self):
        """Tests successfully calling the product files view."""

        url = '/%s/products/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

        for entry in result['results']:

            # Make sure unpublished and superseded products are not included
            self.assertNotEqual(entry['id'], self.product2a.id)
            self.assertNotEqual(entry['id'], self.product2b.id)

            # Make sure country info is included
            self.assertEqual(entry['countries'][0], self.country.iso3)

class TestProductDetailsViewV5(TestCase):

    api = 'v5'
    
    def setUp(self):
        django.setup()

        self.source = source_test_utils.create_source()
        self.ancestor = product_test_utils.create_product(file_name='test_ancestor.txt')
        self.descendant = product_test_utils.create_product(file_name='test_descendant.txt')
        self.product = product_test_utils.create_product(file_name='test_product.txt')

        product_test_utils.create_file_link(ancestor=self.source, descendant=self.ancestor)
        product_test_utils.create_file_link(ancestor=self.source, descendant=self.product)
        product_test_utils.create_file_link(ancestor=self.source, descendant=self.descendant)
        product_test_utils.create_file_link(ancestor=self.ancestor, descendant=self.product)
        product_test_utils.create_file_link(ancestor=self.ancestor, descendant=self.descendant)
        product_test_utils.create_file_link(ancestor=self.product, descendant=self.descendant)

    def test_id(self):
        """Tests successfully calling the product files view by id."""

        url = '/%s/products/%i/' % (self.api, self.product.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.product.id)
        self.assertEqual(result['file_name'], self.product.file_name)
        self.assertEqual(result['job_type']['id'], self.product.job_type_id)

        self.assertEqual(len(result['sources']), 1)
        self.assertEqual(result['sources'][0]['id'], self.source.id)

        self.assertEqual(len(result['ancestors']), 1)
        self.assertEqual(result['ancestors'][0]['id'], self.ancestor.id)

        self.assertEqual(len(result['descendants']), 1)
        self.assertEqual(result['descendants'][0]['id'], self.descendant.id)

    def test_file_name(self):
        """Tests successfully calling the product files view by file name."""

        url = '/%s/products/%s/' % (self.api, self.product.file_name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.product.id)
        self.assertEqual(result['file_name'], self.product.file_name)
        self.assertEqual(result['job_type']['id'], self.product.job_type_id)

        self.assertEqual(len(result['sources']), 1)
        self.assertEqual(result['sources'][0]['id'], self.source.id)

        self.assertEqual(len(result['ancestors']), 1)
        self.assertEqual(result['ancestors'][0]['id'], self.ancestor.id)

        self.assertEqual(len(result['descendants']), 1)
        self.assertEqual(result['descendants'][0]['id'], self.descendant.id)

    def test_missing(self):
        """Tests calling the source files view with an invalid id or file name."""

        url = '/%s/products/12345/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

        url = '/%s/products/missing_file.txt/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

class TestProductsUpdatesViewV5(TransactionTestCase):

    api = 'v5'
    
    def setUp(self):
        django.setup()

        self.country = storage_test_utils.create_country()
        self.job_type1 = job_test_utils.create_job_type(name='test1', category='test-1', is_operational=True)
        self.job1 = job_test_utils.create_job(job_type=self.job_type1)
        self.job_exe1 = job_test_utils.create_job_exe(job=self.job1)
        self.product1 = product_test_utils.create_product(job_exe=self.job_exe1, has_been_published=True,
                                                          is_published=True, file_name='test.txt',
                                                          countries=[self.country])

        self.job_type2 = job_test_utils.create_job_type(name='test2', category='test-2', is_operational=False)
        self.job2 = job_test_utils.create_job(job_type=self.job_type2)
        self.job_exe2 = job_test_utils.create_job_exe(job=self.job2)
        self.product2a = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=False, countries=[self.country])
        self.product2b = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=True, is_superseded=True,
                                                           countries=[self.country])
        self.product2c = product_test_utils.create_product(job_exe=self.job_exe2, has_been_published=True,
                                                           is_published=True, countries=[self.country])

    def test_invalid_started(self):
        """Tests calling the product file updates view when the started parameter is invalid."""

        url = '/%s/products/updates/?started=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the product file updates view when the started parameter is missing timezone."""

        url = '/%s/products/updates/?started=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the product file updates view when the ended parameter is invalid."""

        url = '/%s/products/updates/?started=1970-01-01T00:00:00Z&ended=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the product file updates view when the ended parameter is missing timezone."""

        url = '/%s/products/updates/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the product file updates view with a negative time range."""

        url = '/%s/products/updates/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_job_type_id(self):
        """Tests successfully calling the product file updates view filtered by job type identifier."""

        url = '/%s/products/updates/?job_type_id=%s' % (self.api, self.job_type1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job_type1.id)

    def test_job_type_name(self):
        """Tests successfully calling the product file updates view filtered by job type name."""

        url = '/%s/products/updates/?job_type_name=%s' % (self.api, self.job_type1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job_type1.name)

    # TODO: Remove when v5 deprecated
    def test_job_type_legacy_category(self):
        """Tests successfully calling the product file updates view filtered by job type category."""

        url = '/%s/products/updates/?job_type_category=%s' % (self.api, self.job_type1.category)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['category'], self.job_type1.category)

    def test_is_operational(self):
        """Tests successfully calling the product file updates view filtered by is_operational flag."""

        url = '/%s/products/updates/?is_operational=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['is_operational'], self.job_type1.is_operational)

    def test_file_name(self):
        """Tests successfully calling the product file updates view filtered by file name."""

        url = '/%s/products/updates/?file_name=test.txt' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.product1.file_name)

    def test_successful(self):
        """Tests successfully calling the product file updates view."""

        url = '/%s/products/updates/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

        for entry in result['results']:

            # Make sure superseded products are not included
            self.assertNotEqual(entry['id'], self.product2b.id)

            # Make sure additional attributes are present
            self.assertIsNotNone(entry['update'])
            self.assertIsNotNone(entry['source_files'])
            self.assertEqual(entry['countries'][0], self.country.iso3)

class TestProductSourcesViewV5(TestCase):

    api = 'v5'
    
    def setUp(self):
        django.setup()

        from product.test import utils as product_test_utils
        self.country = storage_test_utils.create_country()
        self.job_type1 = job_test_utils.create_job_type(name='test1', category='test-1', is_operational=True)
        self.job1 = job_test_utils.create_job(job_type=self.job_type1)
        self.job_exe1 = job_test_utils.create_job_exe(job=self.job1)

        self.src_file = source_test_utils.create_source(data_started='2016-01-01T00:00:00Z',
                                                        data_ended='2016-01-01T00:00:00Z', file_name='test.txt',
                                                        is_parsed=True)
        self.product1 = product_test_utils.create_product(job_exe=self.job_exe1, has_been_published=True,
                                                          is_published=True, file_name='test_prod.txt',
                                                          countries=[self.country])
        product_test_utils.create_file_link(ancestor=self.src_file, descendant=self.product1, job=self.job1,
                                            job_exe=self.job_exe1)

    def test_invalid_product_id(self):
        """Tests calling the product file source products view when the source ID is invalid."""

        url = '/%s/products/12345678/sources/' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_invalid_started(self):
        """Tests calling the product file source files view when the started parameter is invalid."""

        url = '/%s/products/%d/sources/?started=hello' %  (self.api, self.product1.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the product file source files view when the started parameter is missing timezone."""

        url = '/%s/products/%d/sources/?started=1970-01-01T00:00:00' % (self.api, self.product1.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the product file source files view when the ended parameter is invalid."""

        url = '/%s/products/%d/sources/?started=1970-01-01T00:00:00Z&ended=hello' % (self.api, self.product1.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the product file source files view when the ended parameter is missing timezone."""

        url = '/%s/products/%d/sources/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00' \
                                % (self.api, self.product1.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the product file source files view with a negative time range."""

        url = '/%s/products/%d/sources/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00' \
                                % (self.api, self.product1.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_time_field(self):
        """Tests calling the product file source files view when the time_field parameter is invalid."""

        url = '/%s/products/%d/sources/?started=1970-01-01T00:00:00Z&time_field=hello' \
                                % (self.api, self.product1.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_time_field(self):
        """Tests successfully calling the product file source files view using the time_field parameter"""

        url = '/%s/products/%d/sources/?started=%s&time_field=data' \
                                % (self.api, self.product1.id, self.src_file.data_started)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

    def test_is_parsed(self):
        """Tests successfully calling the product file source files view filtered by is_parsed flag."""

        url = '/%s/products/%d/sources/?is_parsed=true' % (self.api, self.product1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['is_parsed'], self.src_file.is_parsed)

    def test_file_name(self):
        """Tests successfully calling the product file source files view filtered by file name."""

        url = '/%s/products/%d/sources/?file_name=%s' % (self.api, self.product1.id, self.src_file.file_name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.src_file.file_name)

    def test_successful(self):
        """Tests successfully calling the product file source files view."""

        url = '/%s/products/%d/sources/' % (self.api, self.product1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

class TestProductsViewsV6(TestCase):

    api = 'v6'
    
    def setUp(self):
        django.setup()

    def test_v6_products(self):
        """Tests that product apis are removed in v6"""
        
        url = '/v6/products/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)
        url = '/v6/products/12345/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)
        url = '/%s/products/updates/?started=hello' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)
        url = '/%s/products/1/sources/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)