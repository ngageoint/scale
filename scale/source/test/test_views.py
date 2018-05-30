from __future__ import unicode_literals

import json

import django
from django.test import TestCase, TransactionTestCase
from rest_framework import status

import batch.test.utils as batch_test_utils
import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import source.test.utils as source_test_utils
import storage.test.utils as storage_test_utils
import util.rest as rest_util


class TestSourcesViewV5(TestCase):
    api = 'v5'

    def setUp(self):
        django.setup()

        self.source1 = source_test_utils.create_source(data_started='2016-01-01T00:00:00Z',
                                                       data_ended='2016-01-01T00:00:00Z', is_parsed=True,
                                                       file_name='test.txt')
        self.source2 = source_test_utils.create_source(data_started='2017-01-01T00:00:00Z',
                                                       data_ended='2017-01-01T00:00:00Z', is_parsed=False)

    def test_invalid_started(self):
        """Tests calling the source files view when the started parameter is invalid."""

        url = '/%s/sources/?started=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the source files view when the started parameter is missing timezone."""

        url = '/%s/sources/?started=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the source files view when the ended parameter is invalid."""

        url = '/%s/sources/?started=1970-01-01T00:00:00Z&ended=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the source files view when the ended parameter is missing timezone."""

        url = '/%s/sources/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the source files view with a negative time range."""

        url = '/%s/sources/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_time_field(self):
        """Tests calling the source files view when the time_field parameter is invalid."""

        url = '/%s/sources/?started=1970-01-01T00:00:00Z&time_field=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_time_field(self):
        """Tests successfully calling the source files view using the time_field parameter"""

        url = '/%s/sources/?started=2016-02-01T00:00:00Z&time_field=data' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

    def test_is_parsed(self):
        """Tests successfully calling the source files view filtered by is_parsed flag."""

        url = '/%s/sources/?is_parsed=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['is_parsed'], self.source1.is_parsed)

    def test_file_name(self):
        """Tests successfully calling the source files view filtered by file name."""

        url = '/%s/sources/?file_name=test.txt' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.source1.file_name)

    def test_successful(self):
        """Tests successfully calling the source files view."""

        url = '/%s/sources/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)


class TestSourceDetailsViewV5(TestCase):
    api = 'v5'
    
    def setUp(self):
        django.setup()

        self.country = storage_test_utils.create_country()
        self.source = source_test_utils.create_source(countries=[self.country])

    def test_id(self):
        """Tests successfully calling the source files view by id"""

        url = '/v5/sources/%i/' % self.source.id
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.source.id)
        self.assertEqual(result['file_name'], self.source.file_name)
        self.assertFalse('ingests' in result)
        self.assertFalse('products' in result)
        self.assertEqual(result['countries'][0], self.country.iso3)
        self.assertEqual(result['file_type'], self.source.file_type)
        self.assertEqual(result['file_path'], self.source.file_path)

    def test_missing(self):
        """Tests calling the source files view with an invalid id"""

        url = '/v5/sources/12345/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)


# TODO: remove when REST API v4 is removed
class TestSourceDetailsViewV4(TestCase):

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

        response = self.client.generic('GET', '/v4/sources/%i/' % self.source.id)
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

        response = self.client.generic('GET', '/v4/sources/%s/' % self.source.file_name)
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

        response = self.client.generic('GET', '/v4/sources/12345/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

        response = self.client.generic('GET', '/v4/sources/missing_file.txt/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_superseded(self):
        """Tests successfully calling the source files view filtered by superseded."""

        response = self.client.generic('GET', '/v4/sources/%i/?include_superseded=true' % self.source.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.source.id)

        if self.product1 and self.product2:
            self.assertEqual(len(result['products']), 2)
            for product in result['products']:
                self.assertIn(product['id'], [self.product1.id, self.product2.id])


class TestSourceIngestsViewV5(TestCase):
    api = 'v5'
    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.source_file = source_test_utils.create_source()
        from ingest.test import utils as ingest_test_utils
        self.strike = ingest_test_utils.create_strike()
        self.ingest1 = ingest_test_utils.create_ingest(source_file=self.source_file, status='QUEUED',
                                                       strike=self.strike)
        self.ingest2 = ingest_test_utils.create_ingest(source_file=self.source_file, status='INGESTED')

    def test_invalid_source_id(self):
        """Tests calling the source ingests view when the source ID is invalid."""

        url = '/%s/sources/12345678/ingests/' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the source ingests view."""

        url = '/%s/sources/%s/ingests/' % (self.api, self.source_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            if entry['id'] == self.ingest1.id:
                expected = self.ingest1
            elif entry['id'] == self.ingest2.id:
                expected = self.ingest2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['status'], expected.status)

    def test_status(self):
        """Tests successfully calling the source ingests view filtered by status."""

        url = '/%s/sources/%s/ingests/?status=%s' % (self.api, self.source_file.id, self.ingest1.status)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['status'], self.ingest1.status)

    def test_strike_id(self):
        """Tests successfully calling the source ingests view filtered by strike processor."""

        url = '/%s/sources/%s/ingests/?strike_id=%d' % (self.api, self.source_file.id, self.ingest1.strike.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['strike']['id'], self.ingest1.strike.id)


class TestSourceJobsViewV5(TransactionTestCase):
    api = 'v5'
    
    def setUp(self):
        django.setup()

        from product.test import utils as product_test_utils
        self.src_file = source_test_utils.create_source()

        self.job_type1 = job_test_utils.create_job_type(name='scale-batch-creator', version='1.0', category='test-1')
        self.job1 = job_test_utils.create_job(job_type=self.job_type1, status='RUNNING')
        self.job_exe1 = job_test_utils.create_job_exe(job=self.job1)
        product_test_utils.create_file_link(ancestor=self.src_file, job=self.job1, job_exe=self.job_exe1)

        self.job_type2 = job_test_utils.create_job_type(name='test2', version='1.0', category='test-2')
        self.job2 = job_test_utils.create_job(job_type=self.job_type2, status='PENDING')
        self.job_exe2 = job_test_utils.create_job_exe(job=self.job2)
        product_test_utils.create_file_link(ancestor=self.src_file, job=self.job2, job_exe=self.job_exe2)

        self.job3 = job_test_utils.create_job(is_superseded=True)
        self.job_exe3 = job_test_utils.create_job_exe(job=self.job3)
        product_test_utils.create_file_link(ancestor=self.src_file, job=self.job3, job_exe=self.job_exe3)

    def test_invalid_source_id(self):
        """Tests calling the source jobs view when the source ID is invalid."""

        url = '/%s/sources/12345678/jobs/' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the source jobs view."""

        url = '/%s/sources/%d/jobs/' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            if entry['id'] == self.job1.id:
                expected = self.job1
            elif entry['id'] == self.job2.id:
                expected = self.job2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['job_type']['name'], expected.job_type.name)
            self.assertEqual(entry['job_type_rev']['job_type']['id'], expected.job_type.id)

    def test_status(self):
        """Tests successfully calling the source jobs view filtered by status."""

        url = '/%s/sources/%d/jobs/?status=RUNNING' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job1.job_type.id)

    def test_job_id(self):
        """Tests successfully calling the source jobs view filtered by job identifier."""

        url = '/%s/sources/%d/jobs/?job_id=%s' % (self.api, self.src_file.id, self.job1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job1.id)

    def test_job_type_id(self):
        """Tests successfully calling the source jobs view filtered by job type identifier."""

        url = '/%s/sources/%d/jobs/?job_type_id=%s' % (self.api, self.src_file.id, self.job1.job_type.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job1.job_type.id)

    def test_job_type_name(self):
        """Tests successfully calling the source jobs view filtered by job type name."""

        url = '/%s/sources/%d/jobs/?job_type_name=%s' % (self.api, self.src_file.id, self.job1.job_type.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job1.job_type.name)

    def test_job_type_category(self):
        """Tests successfully calling the source jobs view filtered by job type category."""

        url = '/%s/sources/%d/jobs/?job_type_category=%s'
        url = url % (self.api, self.src_file.id, self.job1.job_type.category)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['category'], self.job1.job_type.category)

    def test_error_category(self):
        """Tests successfully calling the source jobs view filtered by error category."""

        from product.test import utils as product_test_utils
        error = error_test_utils.create_error(category='DATA')
        job = job_test_utils.create_job(error=error)
        job_exe = job_test_utils.create_job_exe(job=job)
        product_test_utils.create_file_link(ancestor=self.src_file, job=job, job_exe=job_exe)

        url = '/%s/sources/%d/jobs/?error_category=%s' % (self.api, self.src_file.id, error.category)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], job.id)
        self.assertEqual(result['results'][0]['error']['category'], error.category)

    def test_superseded(self):
        """Tests getting superseded jobs from source jobs view."""

        url = '/%s/sources/%d/jobs/?include_superseded=true' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

    def test_batch(self):
        """Tests filtering jobs by batch"""
        batch = batch_test_utils.create_batch()
        self.job1.batch_id = batch.id
        self.job1.save()

        url = '/%s/sources/%d/jobs/?batch_id=%d' % (self.api, self.src_file.id, batch.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.job1.id)

    def test_order_by(self):
        """Tests successfully calling the source jobs view with sorting."""

        from product.test import utils as product_test_utils
        job_type1b = job_test_utils.create_job_type(name='scale-batch-creator', version='2.0', category='test-1')
        job1b = job_test_utils.create_job(job_type=job_type1b, status='RUNNING')
        job_exe1b = job_test_utils.create_job_exe(job=job1b)
        product_test_utils.create_file_link(ancestor=self.src_file, job=job1b, job_exe=job_exe1b)

        job_type1c = job_test_utils.create_job_type(name='scale-batch-creator', version='3.0', category='test-1')
        job1c = job_test_utils.create_job(job_type=job_type1c, status='RUNNING')
        job_exe1c = job_test_utils.create_job_exe(job=job1c)
        product_test_utils.create_file_link(ancestor=self.src_file, job=job1c, job_exe=job_exe1c)

        url = '/%s/sources/%d/jobs/?order=job_type__name&order=-job_type__version' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)
        self.assertEqual(result['results'][0]['job_type']['id'], job_type1c.id)
        self.assertEqual(result['results'][1]['job_type']['id'], job_type1b.id)
        self.assertEqual(result['results'][2]['job_type']['id'], self.job_type1.id)
        self.assertEqual(result['results'][3]['job_type']['id'], self.job_type2.id)


class TestSourceProductsViewV5(TestCase):
    api = 'v5'
    
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

        url = '/%s/sources/12345678/products/' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_invalid_started(self):
        """Tests calling the source products view when the started parameter is invalid."""

        url = '/%s/sources/%d/products/?started=hello' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the source products view when the started parameter is missing timezone."""

        url = '/%s/sources/%d/products/?started=1970-01-01T00:00:00' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the source products view when the ended parameter is invalid."""

        url = '/%s/sources/%d/products/?started=1970-01-01T00:00:00Z&ended=hello' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the source products view when the ended parameter is missing timezone."""

        url = '/%s/sources/%d/products/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the source products view with a negative time range."""

        url = '/%s/sources/%d/products/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_batch_id(self):
        """Tests successfully calling the source products view filtered by batch identifier."""

        url = '/%s/sources/%d/products/?batch_id=%s' % (self.api, self.src_file.id, self.batch.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 3)

    def test_job_type_id(self):
        """Tests successfully calling the source products view filtered by job type identifier."""

        url = '/%s/sources/%d/products/?job_type_id=%s' % (self.api, self.src_file.id, self.job_type1.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['id'], self.job_type1.id)

    def test_job_type_name(self):
        """Tests successfully calling the source products view filtered by job type name."""

        url = '/%s/sources/%d/products/?job_type_name=%s' % (self.api, self.src_file.id,  self.job_type1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['name'], self.job_type1.name)

    def test_job_type_category(self):
        """Tests successfully calling the source products view filtered by job type category."""

        url = '/%s/sources/%d/products/?job_type_category=%s' % (self.api, self.src_file.id, self.job_type1.category)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['category'], self.job_type1.category)

    def test_is_operational(self):
        """Tests successfully calling the source products view filtered by is_operational flag."""

        url = '/%s/sources/%d/products/?is_operational=true' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['job_type']['is_operational'], self.job_type1.is_operational)

    def test_is_published(self):
        """Tests successfully calling the source products view filtered by is_published flag."""

        url = '/%s/sources/%d/products/?is_published=false' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['id'], self.product2a.id)
        self.assertFalse(result['results'][0]['is_published'])

    def test_file_name(self):
        """Tests successfully calling the source products view filtered by file name."""

        url = '/%s/sources/%d/products/?file_name=test.txt' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.product1.file_name)

    def test_successful(self):
        """Tests successfully calling the source products view."""

        url = '/%s/sources/%d/products/' % (self.api, self.src_file.id)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 4)

        for entry in result['results']:
            # Make sure country info is included
            self.assertEqual(entry['countries'][0], self.country.iso3)


class TestSourceUpdatesViewV5(TestCase):
    api = 'v5'
    
    def setUp(self):
        django.setup()

        self.source1 = source_test_utils.create_source(data_started='2016-01-01T00:00:00Z',
                                                       data_ended='2016-01-01T00:00:00Z', file_name='test.txt',
                                                       is_parsed=True)
        self.source2 = source_test_utils.create_source(data_started='2017-01-01T00:00:00Z',
                                                       data_ended='2017-01-01T00:00:00Z', is_parsed=False)

    def test_invalid_started(self):
        """Tests calling the source file updates view when the started parameter is invalid."""

        url = '/%s/sources/updates/?started=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_started(self):
        """Tests calling the source file updates view when the started parameter is missing timezone."""

        url = '/%s/sources/updates/?started=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_ended(self):
        """Tests calling the source file updates view when the ended parameter is invalid."""

        url = '/%s/sources/updates/?started=1970-01-01T00:00:00Z&ended=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_missing_tz_ended(self):
        """Tests calling the source file updates view when the ended parameter is missing timezone."""

        url = '/%s/sources/updates/?started=1970-01-01T00:00:00Z&ended=1970-01-02T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_negative_time_range(self):
        """Tests calling the source file updates view with a negative time range."""

        url = '/%s/sources/updates/?started=1970-01-02T00:00:00Z&ended=1970-01-01T00:00:00' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_time_field(self):
        """Tests calling the source file updates view when the time_field parameter is invalid."""

        url = '/%s/sources/updates/?started=1970-01-01T00:00:00Z&time_field=hello' % self.api
        response = self.client.generic('GET', url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_time_field(self):
        """Tests successfully calling the source file updates view using the time_field parameter"""

        url = '/%s/sources/updates/?started=2016-02-01T00:00:00Z&time_field=data' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)

    def test_is_parsed(self):
        """Tests successfully calling the source files view filtered by is_parsed flag."""

        url = '/%s/sources/updates/?is_parsed=true' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['is_parsed'], self.source1.is_parsed)

    def test_file_name(self):
        """Tests successfully calling the source file updates view filtered by file name."""

        url = '/%s/sources/updates/?file_name=test.txt' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['file_name'], self.source1.file_name)

    def test_successful(self):
        """Tests successfully calling the source file updates view."""

        url = '/%s/sources/updates/' % self.api
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)

        for entry in result['results']:
            self.assertIsNotNone(entry['update'])
