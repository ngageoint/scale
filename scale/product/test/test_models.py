from __future__ import unicode_literals

import datetime
import os
import time

import django
from django.db import transaction
from django.test import TestCase
from django.utils.timezone import now, utc
from mock import MagicMock, patch

import job.test.utils as job_test_utils
import product.test.utils as prod_test_utils
import recipe.test.utils as recipe_test_utils
import source.test.utils as source_test_utils
import storage.test.utils as storage_test_utils
from job.execution.container import SCALE_JOB_EXE_OUTPUT_PATH
from product.models import FileAncestryLink, ProductFile


class TestFileAncestryLinkManagerCreateFileAncestryLinks(TestCase):

    def setUp(self):
        django.setup()

        # Generation 1
        self.file_1 = storage_test_utils.create_file()
        self.file_2 = storage_test_utils.create_file()

        # Generation 2
        job_exe_1 = job_test_utils.create_job_exe()
        recipe_job_1 = recipe_test_utils.create_recipe_job(job=job_exe_1.job)
        self.file_3 = prod_test_utils.create_product(job_exe=job_exe_1)
        self.file_4 = prod_test_utils.create_product(job_exe=job_exe_1)
        self.file_5 = prod_test_utils.create_product(job_exe=job_exe_1)

        # Generation 3
        job_exe_2 = job_test_utils.create_job_exe()
        recipe_job_2 = recipe_test_utils.create_recipe_job(job=job_exe_2.job)
        self.file_6 = prod_test_utils.create_product(job_exe=job_exe_2)

        # Stand alone file
        self.file_7 = prod_test_utils.create_product()

        # First job links generation 1 to 2
        FileAncestryLink.objects.create(ancestor=self.file_1, descendant=self.file_3, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.file_1, descendant=self.file_4, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.file_1, descendant=self.file_5, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)

        FileAncestryLink.objects.create(ancestor=self.file_2, descendant=self.file_3, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.file_2, descendant=self.file_4, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.file_2, descendant=self.file_5, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)

        # Second job links generation 2 to 3
        FileAncestryLink.objects.create(ancestor=self.file_3, descendant=self.file_6, job_exe=job_exe_2,
                                        job=job_exe_2.job, recipe=recipe_job_2.recipe)
        FileAncestryLink.objects.create(ancestor=self.file_1, descendant=self.file_6, job_exe=job_exe_2,
                                        job=job_exe_2.job, recipe=recipe_job_2.recipe,
                                        ancestor_job_exe=job_exe_1, ancestor_job=job_exe_1.job)
        FileAncestryLink.objects.create(ancestor=self.file_2, descendant=self.file_6, job_exe=job_exe_2,
                                        job=job_exe_2.job, recipe=recipe_job_2.recipe,
                                        ancestor_job_exe=job_exe_1, ancestor_job=job_exe_1.job)

    def test_inputs(self):
        """Tests creating links for only input files before any products are generated."""

        parent_ids = [self.file_4.id, self.file_6.id, self.file_7.id]
        job_exe = job_test_utils.create_job_exe()
        recipe_test_utils.create_recipe_job(job=job_exe.job)
        FileAncestryLink.objects.create_file_ancestry_links(parent_ids, None, job_exe)

        direct_qry = FileAncestryLink.objects.filter(descendant__isnull=True, job_exe=job_exe,
                                                     ancestor_job__isnull=True)
        self.assertEqual(direct_qry.count(), 3)
        file_8_parent_ids = set()
        for link in direct_qry:
            file_8_parent_ids.add(link.ancestor_id)
        self.assertSetEqual(file_8_parent_ids, set([self.file_4.id, self.file_6.id, self.file_7.id]))

        indirect_qry = FileAncestryLink.objects.filter(descendant__isnull=True, job_exe=job_exe,
                                                       ancestor_job__isnull=False)
        self.assertEqual(indirect_qry.count(), 3)
        file_8_ancestor_ids = set()
        for link in indirect_qry:
            file_8_ancestor_ids.add(link.ancestor_id)
        self.assertSetEqual(file_8_ancestor_ids, set([self.file_1.id, self.file_2.id, self.file_3.id]))

    def test_products(self):
        """Tests creating links for inputs with generated products at the same time."""

        file_8 = storage_test_utils.create_file()

        parent_ids = [self.file_4.id, self.file_6.id, self.file_7.id]
        child_ids = [file_8.id]
        job_exe = job_test_utils.create_job_exe()
        recipe_test_utils.create_recipe_job(job=job_exe.job)
        FileAncestryLink.objects.create_file_ancestry_links(parent_ids, child_ids, job_exe)

        direct_qry = FileAncestryLink.objects.filter(descendant=file_8, job_exe=job_exe, ancestor_job__isnull=True)
        self.assertEqual(direct_qry.count(), 3)
        file_8_parent_ids = set()
        for link in direct_qry:
            file_8_parent_ids.add(link.ancestor_id)
        self.assertSetEqual(file_8_parent_ids, set([self.file_4.id, self.file_6.id, self.file_7.id]))

        indirect_qry = FileAncestryLink.objects.filter(descendant=file_8, job_exe=job_exe, ancestor_job__isnull=False)
        self.assertEqual(indirect_qry.count(), 3)
        file_8_ancestor_ids = set()
        for link in indirect_qry:
            file_8_ancestor_ids.add(link.ancestor_id)
        self.assertSetEqual(file_8_ancestor_ids, set([self.file_1.id, self.file_2.id, self.file_3.id]))

    def test_inputs_and_products(self):
        """Tests creating links for inputs and then later replacing with generated products."""

        file_8 = storage_test_utils.create_file()

        parent_ids = [self.file_4.id, self.file_6.id, self.file_7.id]
        child_ids = [file_8.id]
        job_exe = job_test_utils.create_job_exe()
        recipe_test_utils.create_recipe_job(job=job_exe.job)

        # First create only the input files
        FileAncestryLink.objects.create_file_ancestry_links(parent_ids, None, job_exe)

        # Replace the inputs with the new links for both inputs and products
        FileAncestryLink.objects.create_file_ancestry_links(parent_ids, child_ids, job_exe)

        # Make sure the old entries were deleted
        old_direct_qry = FileAncestryLink.objects.filter(descendant__isnull=True, job_exe=job_exe,
                                                         ancestor_job__isnull=True)
        self.assertEqual(len(old_direct_qry), 0)

        old_indirect_qry = FileAncestryLink.objects.filter(descendant__isnull=True, job_exe=job_exe,
                                                           ancestor_job__isnull=False)
        self.assertEqual(len(old_indirect_qry), 0)

        direct_qry = FileAncestryLink.objects.filter(descendant=file_8, job_exe=job_exe, ancestor_job__isnull=True)
        self.assertEqual(direct_qry.count(), 3)
        file_8_parent_ids = set()
        for link in direct_qry:
            file_8_parent_ids.add(link.ancestor_id)
        self.assertSetEqual(file_8_parent_ids, set([self.file_4.id, self.file_6.id, self.file_7.id]))

        indirect_qry = FileAncestryLink.objects.filter(descendant=file_8, job_exe=job_exe, ancestor_job__isnull=False)
        self.assertEqual(indirect_qry.count(), 3)
        file_8_ancestor_ids = set()
        for link in indirect_qry:
            file_8_ancestor_ids.add(link.ancestor_id)
        self.assertSetEqual(file_8_ancestor_ids, set([self.file_1.id, self.file_2.id, self.file_3.id]))


class TestFileAncestryLinkManagerGetSourceAncestors(TestCase):

    def setUp(self):
        django.setup()

        # Generation 1
        self.file_1 = source_test_utils.create_source(file_name='my_file_1.txt')
        self.file_2 = source_test_utils.create_source(file_name='my_file_2.txt')
        self.file_8 = source_test_utils.create_source(file_name='my_file_8.txt')

        # Generation 2
        job_exe_1 = job_test_utils.create_job_exe()
        recipe_job_1 = recipe_test_utils.create_recipe_job(job=job_exe_1.job)
        self.file_3 = prod_test_utils.create_product(job_exe=job_exe_1)
        self.file_4 = prod_test_utils.create_product(job_exe=job_exe_1)
        self.file_5 = prod_test_utils.create_product(job_exe=job_exe_1)

        # Generation 3
        job_exe_2 = job_test_utils.create_job_exe()
        recipe_job_2 = recipe_test_utils.create_recipe_job(job=job_exe_2.job)
        self.file_6 = prod_test_utils.create_product(job_exe=job_exe_2)

        # Stand alone file
        self.file_7 = prod_test_utils.create_product()

        # First job links generation 1 to 2
        FileAncestryLink.objects.create(ancestor=self.file_1, descendant=self.file_3, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.file_1, descendant=self.file_4, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.file_1, descendant=self.file_5, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)

        FileAncestryLink.objects.create(ancestor=self.file_2, descendant=self.file_4, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.file_2, descendant=self.file_5, job_exe=job_exe_1,
                                        job=job_exe_1.job, recipe=recipe_job_1.recipe)

        # Second job links generation 2 to 3
        FileAncestryLink.objects.create(ancestor=self.file_3, descendant=self.file_6, job_exe=job_exe_2,
                                        job=job_exe_2.job, recipe=recipe_job_2.recipe)
        FileAncestryLink.objects.create(ancestor=self.file_1, descendant=self.file_6, job_exe=job_exe_2,
                                        job=job_exe_2.job, recipe=recipe_job_2.recipe,
                                        ancestor_job_exe=job_exe_1, ancestor_job=job_exe_1.job)

    def test_successful(self):
        """Tests calling FileAncestryLinkManager.get_source_ancestors() successfully."""

        source_files = FileAncestryLink.objects.get_source_ancestors([self.file_6.id, self.file_8.id])

        result_ids = []
        for source_file in source_files:
            result_ids.append(source_file.id)
        result_ids.sort()

        self.assertListEqual(result_ids, [self.file_1.id, self.file_8.id])


class TestProductFileManagerGetProductUpdatesQuery(TestCase):
    """Tests on the ProductFileManager.get_product_updates_query() method"""

    def setUp(self):
        django.setup()

        self.job_exe_1 = job_test_utils.create_job_exe()
        self.job_type_1_id = self.job_exe_1.job.job_type.id
        self.job_exe_2 = job_test_utils.create_job_exe()
        self.job_type_2_id = self.job_exe_2.job.job_type.id

        self.product_1 = prod_test_utils.create_product()
        self.product_2 = prod_test_utils.create_product(has_been_published=True)
        self.product_3 = prod_test_utils.create_product(self.job_exe_2, has_been_published=True)

        time.sleep(0.001)
        self.last_modified_start = now()
        self.product_4 = prod_test_utils.create_product()
        self.product_5 = prod_test_utils.create_product(self.job_exe_2)
        self.product_6 = prod_test_utils.create_product(self.job_exe_2, has_been_published=True)
        time.sleep(0.001)
        self.product_7 = prod_test_utils.create_product(self.job_exe_1, has_been_published=True)
        time.sleep(0.001)
        self.product_8 = prod_test_utils.create_product(has_been_published=True)
        self.last_modified_end = now()

    def test_no_job_types(self):
        """Tests calling ProductFileManager.get_updates() without a "job_type_ids" argument value"""

        updates_qry = ProductFile.objects.get_products(self.last_modified_start, self.last_modified_end)
        list_of_ids = []
        for product in updates_qry:
            list_of_ids.append(product.id)

        expected_ids = [self.product_6.id, self.product_7.id, self.product_8.id]
        self.assertListEqual(list_of_ids, expected_ids)

    def test_job_types(self):
        """Tests calling ProductFileManager.get_updates() with a "job_type_ids" argument value"""

        job_type_ids = [self.job_type_1_id, self.job_type_2_id]
        updates_qry = ProductFile.objects.get_products(self.last_modified_start, self.last_modified_end, job_type_ids)
        list_of_ids = []
        for product in updates_qry:
            list_of_ids.append(product.id)

        expected_ids = [self.product_6.id, self.product_7.id]
        self.assertListEqual(list_of_ids, expected_ids)


class TestProductFileManagerPopulateSourceAncestors(TestCase):
    """Tests on the ProductFileManager.populate_source_ancestors() method"""

    def setUp(self):
        django.setup()

        self.src_file_1 = source_test_utils.create_source()
        self.src_file_2 = source_test_utils.create_source()
        self.src_file_3 = source_test_utils.create_source()
        self.src_file_4 = source_test_utils.create_source()

        self.job_exe_1 = job_test_utils.create_job_exe()
        self.recipe_job_1 = recipe_test_utils.create_recipe_job(job=self.job_exe_1.job)
        self.product_1 = prod_test_utils.create_product(self.job_exe_1, has_been_published=True)
        self.product_2 = prod_test_utils.create_product(self.job_exe_1, has_been_published=True)
        FileAncestryLink.objects.create(ancestor=self.src_file_1, descendant=self.product_1, job_exe=self.job_exe_1,
                                        job=self.job_exe_1.job, recipe=self.recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.src_file_1, descendant=self.product_2, job_exe=self.job_exe_1,
                                        job=self.job_exe_1.job, recipe=self.recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.src_file_2, descendant=self.product_1, job_exe=self.job_exe_1,
                                        job=self.job_exe_1.job, recipe=self.recipe_job_1.recipe)
        FileAncestryLink.objects.create(ancestor=self.src_file_2, descendant=self.product_2, job_exe=self.job_exe_1,
                                        job=self.job_exe_1.job, recipe=self.recipe_job_1.recipe)

        self.job_exe_2 = job_test_utils.create_job_exe()
        self.recipe_job_2 = recipe_test_utils.create_recipe_job(job=self.job_exe_2.job)
        self.product_3 = prod_test_utils.create_product(self.job_exe_2, has_been_published=True)
        FileAncestryLink.objects.create(ancestor=self.src_file_3, descendant=self.product_3, job_exe=self.job_exe_2,
                                        job=self.job_exe_2.job, recipe=self.recipe_job_2.recipe)
        FileAncestryLink.objects.create(ancestor=self.src_file_4, descendant=self.product_3, job_exe=self.job_exe_2,
                                        job=self.job_exe_2.job, recipe=self.recipe_job_2.recipe)

    def test_successful(self):
        """Tests calling ProductFileManager.populate_source_ancestors() successfully"""

        products = ProductFile.objects.filter(id__in=[self.product_1.id, self.product_2.id, self.product_3.id])

        ProductFile.objects.populate_source_ancestors(products)

        for product in products:
            if product.id == self.product_1.id:
                self.assertSetEqual(set(product.source_files), set([self.src_file_1, self.src_file_2]))
            elif product.id == self.product_2.id:
                self.assertSetEqual(set(product.source_files), set([self.src_file_1, self.src_file_2]))
            elif product.id == self.product_3.id:
                self.assertSetEqual(set(product.source_files), set([self.src_file_3, self.src_file_4]))


class TestProductFileManagerUploadFiles(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.workspace.upload_files = MagicMock()
        self.workspace.delete_files = MagicMock()

        self.source_file = source_test_utils.create_source(file_name='input1.txt', workspace=self.workspace)

        self.job_exe = job_test_utils.create_job_exe()
        self.job_exe_no = job_test_utils.create_job_exe()
        with transaction.atomic():
            self.job_exe_no.job.is_operational = False
            self.job_exe_no.job.job_type.is_operational = False
            self.job_exe_no.job.save()
            self.job_exe_no.job.job_type.save()

        self.local_path_1 = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, 'local/1/file.txt')
        self.local_path_2 = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, 'local/2/file.json')
        self.local_path_3 = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, 'local/3/file.h5')

        self.files = [
            (self.local_path_1, 'remote/1/file.txt', None),
            (self.local_path_2, 'remote/2/file.json', 'application/x-custom-json'),
        ]
        self.files_no = [
            (self.local_path_3, 'remote/3/file.h5', 'image/x-hdf5-image'),
        ]

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_success(self):
        """Tests calling ProductFileManager.upload_files() successfully"""
        products = ProductFile.objects.upload_files(self.files, [self.source_file.id], self.job_exe, self.workspace)

        self.assertEqual('file.txt', products[0].file_name)
        self.assertEqual('remote/1/file.txt', products[0].file_path)
        self.assertEqual('text/plain', products[0].media_type)
        self.assertEqual(self.workspace.id, products[0].workspace_id)
        self.assertIsNotNone(products[0].uuid)
        self.assertTrue(products[0].is_operational)

        self.assertEqual('file.json', products[1].file_name)
        self.assertEqual('remote/2/file.json', products[1].file_path)
        self.assertEqual('application/x-custom-json', products[1].media_type)
        self.assertEqual(self.workspace.id, products[1].workspace_id)
        self.assertIsNotNone(products[1].uuid)
        self.assertTrue(products[1].is_operational)

        self.assertNotEqual(products[0].uuid, products[1].uuid)

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_non_operational_product(self):
        """Tests calling ProductFileManager.upload_files() with a non-operational input file"""
        products_no = ProductFile.objects.upload_files(self.files_no, [self.source_file.id], self.job_exe_no,
                                                       self.workspace)
        products = ProductFile.objects.upload_files(self.files, [self.source_file.id, products_no[0].file.id],
                                                    self.job_exe, self.workspace)
        self.assertFalse(products[0].is_operational)
        self.assertFalse(products[1].is_operational)

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_geo_metadata(self):
        """Tests calling ProductFileManager.upload_files() successfully with extra geometry meta data"""
        geo_metadata = {
            'data_started': '2015-05-15T10:34:12Z',
            'data_ended': '2015-05-15T10:36:12Z',
            'geo_json': {
                'type': 'Polygon',
                'coordinates': [
                    [[1.0, 10.0], [2.0, 10.0], [2.0, 20.0], [1.0, 20.0], [1.0, 10.0]],
                ]
            }
        }
        files = [(os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, 'local/1/file.txt'), 'remote/1/file.txt', 'text/plain',
                  geo_metadata)]

        products = ProductFile.objects.upload_files(files, [self.source_file.id], self.job_exe, self.workspace)

        self.assertEqual('file.txt', products[0].file_name)
        self.assertEqual('remote/1/file.txt', products[0].file_path)
        self.assertEqual('text/plain', products[0].media_type)
        self.assertEqual(self.workspace.id, products[0].workspace_id)
        self.assertEqual('Polygon', products[0].geometry.geom_type)
        self.assertEqual('Point', products[0].center_point.geom_type)
        self.assertEqual(datetime.datetime(2015, 5, 15, 10, 34, 12, tzinfo=utc), products[0].data_started)
        self.assertEqual(datetime.datetime(2015, 5, 15, 10, 36, 12, tzinfo=utc), products[0].data_ended)
        self.assertIsNotNone(products[0].uuid)

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_uuid(self):
        """Tests setting UUIDs on products from a single job execution."""
        products = ProductFile.objects.upload_files(self.files, [], self.job_exe, self.workspace)

        # Make sure multiple products from the same job have different UUIDs
        self.assertIsNotNone(products[0].uuid)
        self.assertIsNotNone(products[1].uuid)
        self.assertNotEqual(products[0].uuid, products[1].uuid)

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_uuid_use_job_exe(self):
        """Tests setting UUIDs on products from multiple job executions of the same type."""
        job = job_test_utils.create_job()
        job_exe1 = job_test_utils.create_job_exe(job=job)
        job_exe2 = job_test_utils.create_job_exe(job=job)

        products1 = ProductFile.objects.upload_files(self.files, [self.source_file.id], job_exe1, self.workspace)
        products2 = ProductFile.objects.upload_files(self.files, [self.source_file.id], job_exe2, self.workspace)

        # Make sure products produced by multiple runs of the same job type have the same UUIDs
        self.assertIsNotNone(products1[0].uuid)
        self.assertIsNotNone(products1[1].uuid)
        self.assertEqual(products1[0].uuid, products2[0].uuid)
        self.assertEqual(products1[1].uuid, products2[1].uuid)

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_uuid_use_input_files(self):
        """Tests setting UUIDs on products with different source input files."""
        source_file2 = source_test_utils.create_source(file_name='input2.txt', workspace=self.workspace)

        products1 = ProductFile.objects.upload_files(self.files, [self.source_file.id], self.job_exe, self.workspace)
        products2 = ProductFile.objects.upload_files(self.files, [source_file2.id], self.job_exe, self.workspace)

        # Make sure the source files are taken into account
        self.assertIsNotNone(products1[0].uuid)
        self.assertIsNotNone(products1[1].uuid)
        self.assertNotEqual(products1[0].uuid, products2[0].uuid)
        self.assertNotEqual(products1[1].uuid, products2[1].uuid)

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_uuid_use_job_type(self):
        """Tests setting UUIDs on products with different job types."""
        job_exe2 = job_test_utils.create_job_exe()

        products1 = ProductFile.objects.upload_files(self.files, [self.source_file.id], self.job_exe, self.workspace)
        products2 = ProductFile.objects.upload_files(self.files, [self.source_file.id], job_exe2, self.workspace)

        # Make sure the same inputs with different job types have different UUIDs
        self.assertIsNotNone(products1[0].uuid)
        self.assertIsNotNone(products1[1].uuid)
        self.assertNotEqual(products1[0].uuid, products2[0].uuid)
        self.assertNotEqual(products1[1].uuid, products2[1].uuid)
