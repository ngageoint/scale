from __future__ import unicode_literals

import datetime
import os

import copy
import django
from django.test import TestCase
from django.utils.timezone import now
from mock import patch

from job.test import utils as job_utils
from recipe.test import utils as recipe_test_utils
from source.models import SourceFile
from source.test import utils as source_test_utils
from storage.brokers.broker import FileMove
from storage.models import ScaleFile, Workspace
from storage.test import utils as storage_utils
from trigger.models import TriggerEvent
from trigger.test import utils as trigger_utils

FEATURE_COLLECTION_GEOJSON = {"type": "FeatureCollection", "features": [{ "type": "Feature", "properties": { "prop_a": "A", "prop_b": "B" }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 1.0, 10.5 ], [ 1.1, 21.1 ], [ 1.2, 21.2 ], [ 1.3, 21.6 ], [ 1.0, 10.5 ] ] ] } }]}
FEATURE_GEOJSON = {"type": "Feature", "properties": { "prop_a": "A", "prop_b": "B" }, "geometry": { "type": "Polygon", "coordinates": [ [ [ 1.0, 10.5 ], [ 1.1, 21.1 ], [ 1.2, 21.2 ], [ 1.3, 21.6 ], [ 1.0, 10.5 ] ] ] } }
POLYGON_GEOJSON = {"type": "Polygon", "coordinates": [ [ [ 1.0, 10.5 ], [ 1.1, 21.1 ], [ 1.2, 21.2 ], [ 1.3, 21.6 ], [ 1.0, 10.5 ] ] ] }


class TestSourceFileManager(TestCase):

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.workspace = Workspace.objects.create(name='Test Workspace', is_active=True, created=now(),
                                                  last_modified=now())

        self.src_file = ScaleFile.objects.create(file_name='text.txt', file_type='SOURCE', media_type='text/plain',
                                                 file_size=10, data_type_tags=['type'], file_path='the_path',
                                                 workspace=self.workspace)

        self.started = now()
        self.ended = self.started + datetime.timedelta(days=1)

    def test_get_source_ingests(self):
        """Tests calling get_source_ingests()"""

        from ingest.test import utils as ingest_test_utils
        ingest_1 = ingest_test_utils.create_ingest(source_file=self.src_file, status='INGESTED')
        ingest_test_utils.create_ingest(source_file=self.src_file, status='DUPLICATE')

        ingests = SourceFile.objects.get_source_ingests(self.src_file.id, statuses=['INGESTED'])
        self.assertEqual(len(ingests), 1)
        self.assertEqual(ingests[0].id, ingest_1.id)

    def test_get_source_jobs(self):
        """Tests calling get_source_jobs()"""

        from product.test import utils as product_test_utils
        job_exe = job_utils.create_job_exe()
        product_1 = product_test_utils.create_product(job_exe=job_exe, has_been_published=True,
                                                      workspace=self.workspace)
        product_2 = product_test_utils.create_product(job_exe=job_exe, has_been_published=True,
                                                      workspace=self.workspace)
        product_test_utils.create_file_link(ancestor=self.src_file, descendant=product_1, job=job_exe.job,
                                            job_exe=job_exe)
        product_test_utils.create_file_link(ancestor=self.src_file, descendant=product_2, job=job_exe.job,
                                            job_exe=job_exe)

        jobs = SourceFile.objects.get_source_jobs(self.src_file.id)
        # Should only return one job despite two file_ancestry_link models
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].id, job_exe.job.id)

    def test_get_source_products(self):
        """Tests calling get_source_products()"""

        from batch.test import utils as batch_test_utils
        from product.test import utils as product_test_utils
        job_exe_1 = job_utils.create_job_exe()
        job_exe_2 = job_utils.create_job_exe()
        product_1 = product_test_utils.create_product(job_exe=job_exe_1, has_been_published=True,
                                                      workspace=self.workspace)
        product_2 = product_test_utils.create_product(job_exe=job_exe_2, has_been_published=True,
                                                      workspace=self.workspace)
        batch_1 = batch_test_utils.create_batch()
        batch_2 = batch_test_utils.create_batch()
        product_test_utils.create_file_link(ancestor=self.src_file, descendant=product_1, job=job_exe_1.job,
                                            job_exe=job_exe_1, batch=batch_1)
        product_test_utils.create_file_link(ancestor=self.src_file, descendant=product_2, job=job_exe_2.job,
                                            job_exe=job_exe_2, batch=batch_2)

        products = SourceFile.objects.get_source_products(self.src_file.id, batch_ids=[batch_1.id])
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, product_1.id)

    def test_get_sources_data_time(self):
        """Tests calling get_sources() using data time"""

        source_test_utils.create_source(data_started='2016-01-01T00:00:00Z', data_ended='2016-02-01T00:00:00Z')
        source_test_utils.create_source(data_started='2016-02-01T00:00:00Z', data_ended='2016-02-01T00:00:00Z')
        source_test_utils.create_source(data_started='2016-01-01T00:00:00Z', data_ended='2016-03-01T00:00:00Z')
        source_test_utils.create_source(data_started='2016-01-01T00:00:00Z', data_ended='2016-04-01T00:00:00Z')

        sources = SourceFile.objects.get_sources(started='2015-12-01T00:00:00Z', ended='2016-01-15T00:00:00Z',
                                                 time_field='data')
        self.assertEqual(len(sources), 3)

        sources = SourceFile.objects.get_sources(started='2016-02-15T00:00:00Z', time_field='data')
        self.assertEqual(len(sources), 2)

        sources = SourceFile.objects.get_sources(ended='2016-01-15T00:00:00Z', time_field='data')
        self.assertEqual(len(sources), 3)


class TestSourceFileManagerSaveParseResults(TestCase):

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        workspace = Workspace.objects.create(name='Test Workspace', is_active=True, created=now(), last_modified=now())

        self.src_file = ScaleFile.objects.create(file_name='text.txt', file_type='SOURCE', media_type='text/plain',
                                                 file_size=10, data_type_tags=['type'], file_path='the_path',
                                                 workspace=workspace)

        self.started = now()
        self.ended = self.started + datetime.timedelta(days=1)

    @patch('source.models.ScaleFile.objects.move_files')
    def test_move_source_file(self, mock_move_files):
        """Tests calling save_parse_results so that the source file is moved to a different path in the workspace"""

        new_path = os.path.join('the', 'new', 'workspace', 'path', self.src_file.file_name)

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, None, None, None, [], new_path)

        # Check results
        mock_move_files.assert_called_once_with([FileMove(self.src_file, new_path)])

    @patch('source.models.ScaleFile.objects.move_files')
    def test_move_source_file_denied(self, mock_move_files):
        """Tests calling save_parse_results where the source file is not allowed to be moved within the workspace"""

        self.src_file.workspace.is_move_enabled = False
        self.src_file.workspace.save()
        new_path = os.path.join('the', 'new', 'workspace', 'path', self.src_file.file_name)

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, None, None, None, [], new_path)

        # Check results
        self.assertFalse(mock_move_files.called, 'ScaleFile.objects.move_files() should not be called')

    def test_successful_data_time_save(self):
        """Tests calling save_parse_results and checks that the data time is saved within the corresponding ingest
        model
        """

        from ingest.models import Ingest
        from ingest.test import utils
        ingest = utils.create_ingest(file_name=self.src_file.file_name, status='INGESTED', source_file=self.src_file)

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, FEATURE_COLLECTION_GEOJSON, self.started, self.ended,
                                              [], None)

        # Check results
        ingest = Ingest.objects.get(pk=ingest.id)
        self.assertEqual(ingest.data_started, self.started)
        self.assertEqual(ingest.data_ended, self.ended)

    def test_valid_feature_collection(self):
        """Tests calling save_parse_results with valid arguments"""

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, FEATURE_COLLECTION_GEOJSON, self.started, self.ended,
                                              [], None)

        # Check results
        src_file = ScaleFile.objects.get(pk=self.src_file.id)
        self.assertEqual(src_file.is_parsed, True)
        self.assertIsNotNone(src_file.parsed)
        self.assertEqual(src_file.data_started, self.started)
        self.assertEqual(src_file.data_ended, self.ended)
        self.assertDictEqual(src_file.meta_data, {'prop_a': 'A', 'prop_b': 'B'})
        self.assertIsNotNone(src_file.geometry)
        self.assertIsNotNone(src_file.center_point)

    def test_valid_feature(self):
        """Tests calling save_parse_results with valid arguments"""

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, FEATURE_GEOJSON, self.started, self.ended, [], None)

        # Check results
        src_file = ScaleFile.objects.get(pk=self.src_file.id)
        self.assertEqual(src_file.is_parsed, True)
        self.assertIsNotNone(src_file.parsed)
        self.assertEqual(src_file.data_started, self.started)
        self.assertEqual(src_file.data_ended, self.ended)
        self.assertDictEqual(src_file.meta_data, {'prop_a': 'A', 'prop_b': 'B'})
        self.assertIsNotNone(src_file.geometry)
        self.assertIsNotNone(src_file.center_point)


    def test_valid_polygon(self):
        """Tests calling save_parse_results with valid arguments"""

        # Call method to test
        SourceFile.objects.save_parse_results(self.src_file.id, POLYGON_GEOJSON, None, None, [], None)

        # Check results
        src_file = ScaleFile.objects.get(pk=self.src_file.id)
        self.assertEqual(src_file.is_parsed, True)
        self.assertIsNotNone(src_file.parsed)
        self.assertIsNone(src_file.data_started)
        self.assertIsNone(src_file.data_ended)
        self.assertIsNotNone(src_file.meta_data)
        self.assertIsNotNone(src_file.geometry)
        self.assertIsNotNone(src_file.center_point)
