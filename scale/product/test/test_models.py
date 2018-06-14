from __future__ import unicode_literals

import datetime
import hashlib
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
import trigger.test.utils as trigger_test_utils
from batch.models import BatchRecipe, BatchJob
from batch.test import utils as batch_test_utils
from job.execution.container import SCALE_JOB_EXE_OUTPUT_PATH
from job.models import Job, JobManager
from product.models import FileAncestryLink, ProductFile
from recipe.models import RecipeManager
from storage.models import ScaleFile


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

    def test_batch_recipe(self):
        """Tests creating a link that has a recipe and batch."""

        parent_ids = [self.file_1.id]
        job_exe = job_test_utils.create_job_exe()
        recipe_job = recipe_test_utils.create_recipe_job(job=job_exe.job)
        batch = batch_test_utils.create_batch()
        BatchRecipe.objects.create(batch_id=batch.id, recipe_id=recipe_job.recipe.id)
        BatchJob.objects.create(batch_id=batch.id, job_id=job_exe.job_id)
        FileAncestryLink.objects.create_file_ancestry_links(parent_ids, None, job_exe.job, job_exe.id)

        link = FileAncestryLink.objects.get(job_exe=job_exe)
        self.assertEqual(link.recipe_id, recipe_job.recipe_id)
        self.assertEqual(link.batch_id, batch.id)

    def test_inputs(self):
        """Tests creating links for only input files before any products are generated."""

        parent_ids = [self.file_4.id, self.file_6.id, self.file_7.id]
        job_exe = job_test_utils.create_job_exe()
        recipe_test_utils.create_recipe_job(job=job_exe.job)
        FileAncestryLink.objects.create_file_ancestry_links(parent_ids, None, job_exe.job, job_exe.id)

        direct_qry = FileAncestryLink.objects.filter(descendant__isnull=True, job_exe=job_exe,
                                                     ancestor_job__isnull=True)
        self.assertEqual(direct_qry.count(), 2)
        file_8_parent_ids = {link.ancestor_id for link in direct_qry}
        self.assertSetEqual(file_8_parent_ids, {self.file_1.id, self.file_2.id})

    def test_products(self):
        """Tests creating links for inputs with generated products at the same time."""

        file_8 = storage_test_utils.create_file()

        parent_ids = [self.file_4.id, self.file_6.id, self.file_7.id]
        child_ids = [file_8.id]
        job_exe = job_test_utils.create_job_exe()
        recipe_test_utils.create_recipe_job(job=job_exe.job)
        FileAncestryLink.objects.create_file_ancestry_links(parent_ids, child_ids, job_exe.job, job_exe.id)

        direct_qry = FileAncestryLink.objects.filter(descendant=file_8, job_exe=job_exe, ancestor_job__isnull=True)
        self.assertEqual(direct_qry.count(), 2)
        file_8_parent_ids = {link.ancestor_id for link in direct_qry}
        self.assertSetEqual(file_8_parent_ids, {self.file_1.id, self.file_2.id})

    def test_inputs_and_products(self):
        """Tests creating links for inputs and then later replacing with generated products."""

        file_8 = storage_test_utils.create_file()

        parent_ids = [self.file_4.id, self.file_6.id, self.file_7.id]
        child_ids = [file_8.id]
        job_exe = job_test_utils.create_job_exe()
        recipe_test_utils.create_recipe_job(job=job_exe.job)

        # First create only the input files
        FileAncestryLink.objects.create_file_ancestry_links(parent_ids, None, job_exe.job, job_exe.id)

        # Replace the inputs with the new links for both inputs and products
        FileAncestryLink.objects.create_file_ancestry_links(parent_ids, child_ids, job_exe.job, job_exe.id)

        # Make sure the old entries were deleted
        old_direct_qry = FileAncestryLink.objects.filter(descendant__isnull=True, job_exe=job_exe,
                                                         ancestor_job__isnull=True)
        self.assertEqual(len(old_direct_qry), 0)

        old_indirect_qry = FileAncestryLink.objects.filter(descendant__isnull=True, job_exe=job_exe,
                                                           ancestor_job__isnull=False)
        self.assertEqual(len(old_indirect_qry), 0)

        direct_qry = FileAncestryLink.objects.filter(descendant=file_8, job_exe=job_exe, ancestor_job__isnull=True)
        self.assertEqual(direct_qry.count(), 2)
        file_8_parent_ids = {link.ancestor_id for link in direct_qry}
        self.assertSetEqual(file_8_parent_ids, {self.file_1.id, self.file_2.id})


class TestProductFileManager(TestCase):
    """Tests on the ProductFileManager"""

    def setUp(self):
        django.setup()

        self.job_exe = job_test_utils.create_job_exe()

        self.product_1 = prod_test_utils.create_product(job_exe=self.job_exe)
        self.product_2 = prod_test_utils.create_product(job_exe=self.job_exe)
        self.product_3 = prod_test_utils.create_product(job_exe=self.job_exe)

    def test_publish_products_successfully(self):
        """Tests calling ProductFileManager.publish_products() successfully"""

        when = now()
        ProductFile.objects.publish_products(self.job_exe, self.job_exe.job, when)

        product_1 = ScaleFile.objects.get(id=self.product_1.id)
        product_2 = ScaleFile.objects.get(id=self.product_2.id)
        product_3 = ScaleFile.objects.get(id=self.product_3.id)
        self.assertTrue(product_1.has_been_published)
        self.assertTrue(product_1.is_published)
        self.assertEqual(product_1.published, when)
        self.assertTrue(product_2.has_been_published)
        self.assertTrue(product_2.is_published)
        self.assertEqual(product_2.published, when)
        self.assertTrue(product_3.has_been_published)
        self.assertTrue(product_3.is_published)
        self.assertEqual(product_3.published, when)

    def test_publish_products_already_superseded(self):
        """Tests calling ProductFileManager.publish_products() where the job execution is already superseded"""

        self.job_exe.job.is_superseded = True
        when = now()
        ProductFile.objects.publish_products(self.job_exe, self.job_exe.job, when)

        product_1 = ScaleFile.objects.get(id=self.product_1.id)
        product_2 = ScaleFile.objects.get(id=self.product_2.id)
        product_3 = ScaleFile.objects.get(id=self.product_3.id)
        self.assertFalse(product_1.has_been_published)
        self.assertFalse(product_1.is_published)
        self.assertIsNone(product_1.published)
        self.assertFalse(product_2.has_been_published)
        self.assertFalse(product_2.is_published)
        self.assertIsNone(product_2.published)
        self.assertFalse(product_3.has_been_published)
        self.assertFalse(product_3.is_published)
        self.assertIsNone(product_3.published)

    def test_publish_products_unpublish_superseded(self):
        """Tests calling ProductFileManager.publish_products() where the job has superseded job products that must be
        unpublished
        """

        # Job 1 is superseded by Job 2 and Job 2 is superseded by Job 3
        job_exe_1 = job_test_utils.create_job_exe()
        product_1_a = prod_test_utils.create_product(job_exe=job_exe_1, has_been_published=True, is_published=True)
        product_1_b = prod_test_utils.create_product(job_exe=job_exe_1, has_been_published=True, is_published=True)
        job_type = job_test_utils.create_job_type()
        event = trigger_test_utils.create_trigger_event()
        job_2 = Job.objects.create_job(job_type=job_type, event_id=event.id, superseded_job=job_exe_1.job)
        job_2.save()
        job_exe_2 = job_test_utils.create_job_exe(job=job_2)
        Job.objects.supersede_jobs_old([job_exe_1.job], now())
        product_2_a = prod_test_utils.create_product(job_exe=job_exe_2, has_been_published=True, is_published=True)
        product_2_b = prod_test_utils.create_product(job_exe=job_exe_2, has_been_published=True, is_published=True)
        job_3 = Job.objects.create_job(job_type=job_type, event_id=event.id, superseded_job=job_exe_2.job)
        job_3.save()
        job_exe_3 = job_test_utils.create_job_exe(job=job_3)
        Job.objects.supersede_jobs_old([job_2], now())
        product_3_a = prod_test_utils.create_product(job_exe=job_exe_3)
        product_3_b = prod_test_utils.create_product(job_exe=job_exe_3)

        when = now()
        ProductFile.objects.publish_products(job_exe_3, job_3, when)

        # Make sure products from Job 1 and Job 2 are unpublished
        product_1_a = ScaleFile.objects.get(id=product_1_a.id)
        product_1_b = ScaleFile.objects.get(id=product_1_b.id)
        product_2_a = ScaleFile.objects.get(id=product_2_a.id)
        product_2_b = ScaleFile.objects.get(id=product_2_b.id)
        self.assertTrue(product_1_a.has_been_published)
        self.assertFalse(product_1_a.is_published)
        self.assertEqual(product_1_a.unpublished, when)
        self.assertTrue(product_1_b.has_been_published)
        self.assertFalse(product_1_b.is_published)
        self.assertEqual(product_1_b.unpublished, when)
        self.assertTrue(product_2_a.has_been_published)
        self.assertFalse(product_2_a.is_published)
        self.assertEqual(product_2_a.unpublished, when)
        self.assertTrue(product_2_b.has_been_published)
        self.assertFalse(product_2_b.is_published)
        self.assertEqual(product_2_b.unpublished, when)

        # Make sure Job 3 products are published
        product_3_a = ScaleFile.objects.get(id=product_3_a.id)
        product_3_b = ScaleFile.objects.get(id=product_3_b.id)
        self.assertTrue(product_3_a.has_been_published)
        self.assertTrue(product_3_a.is_published)
        self.assertFalse(product_3_a.is_superseded)
        self.assertEqual(product_3_a.published, when)
        self.assertIsNone(product_3_a.superseded)
        self.assertTrue(product_3_b.has_been_published)
        self.assertTrue(product_3_b.is_published)
        self.assertFalse(product_3_b.is_superseded)
        self.assertEqual(product_3_b.published, when)
        self.assertIsNone(product_3_b.superseded)

    def test_publish_products_supersede_products(self):
        """Tests calling ProductFileManager.publish_products() where products with existing UUIDs get superseded
        """

        # Create existing products with known UUIDs
        builder = hashlib.md5()
        builder.update('test')
        uuid_1 = builder.hexdigest()
        builder.update('hello')
        uuid_2 = builder.hexdigest()
        builder.update('again')
        uuid_3 = builder.hexdigest()
        product_a = prod_test_utils.create_product(uuid=uuid_1, has_been_published=True, is_published=True)
        product_b = prod_test_utils.create_product(uuid=uuid_2, has_been_published=True, is_published=True)
        product_c = prod_test_utils.create_product(uuid=uuid_3, has_been_published=True, is_published=True)

        # Set the new products with the same UUIDs
        ScaleFile.objects.filter(id=self.product_1.id).update(uuid=uuid_1)
        ScaleFile.objects.filter(id=self.product_2.id).update(uuid=uuid_2)
        ScaleFile.objects.filter(id=self.product_3.id).update(uuid=uuid_3)

        # Publish new products
        when = now()
        ProductFile.objects.publish_products(self.job_exe, self.job_exe.job, when)

        # Check old products to make sure they are superseded
        product_a = ScaleFile.objects.get(id=product_a.id)
        product_b = ScaleFile.objects.get(id=product_b.id)
        product_c = ScaleFile.objects.get(id=product_c.id)
        self.assertFalse(product_a.is_published)
        self.assertTrue(product_a.is_superseded)
        self.assertEqual(product_a.superseded, when)
        self.assertFalse(product_b.is_published)
        self.assertTrue(product_b.is_superseded)
        self.assertEqual(product_b.superseded, when)
        self.assertFalse(product_c.is_published)
        self.assertTrue(product_c.is_superseded)
        self.assertEqual(product_c.superseded, when)


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

        updates_qry = ProductFile.objects.get_products(started=self.last_modified_start, ended=self.last_modified_end,
                                                       time_field='last_modified')
        list_of_ids = []
        for product in updates_qry:
            list_of_ids.append(product.id)

        expected_ids = [self.product_6.id, self.product_7.id, self.product_8.id]
        self.assertListEqual(list_of_ids, expected_ids)

    def test_job_types(self):
        """Tests calling ProductFileManager.get_updates() with a "job_type_ids" argument value"""

        job_type_ids = [self.job_type_1_id, self.job_type_2_id]
        updates_qry = ProductFile.objects.get_products(started=self.last_modified_start, ended=self.last_modified_end,
                                                       time_field='last_modified', job_type_ids=job_type_ids)
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

        products = ScaleFile.objects.filter(id__in=[self.product_1.id, self.product_2.id, self.product_3.id])

        ProductFile.objects.populate_source_ancestors(products)

        for product in products:
            if product.id == self.product_1.id:
                self.assertSetEqual(set(product.source_files), {self.src_file_1, self.src_file_2})
            elif product.id == self.product_2.id:
                self.assertSetEqual(set(product.source_files), {self.src_file_1, self.src_file_2})
            elif product.id == self.product_3.id:
                self.assertSetEqual(set(product.source_files), {self.src_file_3, self.src_file_4})


class TestProductFileManagerUploadFiles(TestCase):
    def setUp(self):
        django.setup()

        def upload_files(file_uploads):
            for file_upload in file_uploads:
                file_upload.file.save()

        def delete_files(files):
            for scale_file in files:
                scale_file.save()

        self.workspace = storage_test_utils.create_workspace()
        self.workspace.upload_files = MagicMock(side_effect=upload_files)
        self.workspace.delete_files = MagicMock(side_effect=delete_files)

        self.source_file = source_test_utils.create_source(file_name='input1.txt', workspace=self.workspace)

        self.job_exe = job_test_utils.create_job_exe()
        data = self.job_exe.job.get_job_data()
        data.add_property_input('property1', 'value1')
        data.add_property_input('property2', 'value2')
        self.job_exe.job.data = data.get_dict()
        self.job_exe.job.save()
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
            (self.local_path_1, 'remote/1/file.txt', None, 'output_name_1'),
            (self.local_path_2, 'remote/2/file.json', 'application/x-custom-json', 'output_name_2'),
        ]
        self.files_no = [
            (self.local_path_3, 'remote/3/file.h5', 'image/x-hdf5-image', 'output_name_3'),
        ]

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_success(self):
        """Tests calling ProductFileManager.upload_files() successfully"""
        products = ProductFile.objects.upload_files(self.files, [self.source_file.id], self.job_exe, self.workspace)

        self.assertEqual('file.txt', products[0].file_name)
        self.assertEqual('PRODUCT', products[0].file_type)
        self.assertEqual('remote/1/file.txt', products[0].file_path)
        self.assertEqual('text/plain', products[0].media_type)
        self.assertEqual(self.workspace.id, products[0].workspace_id)
        self.assertIsNotNone(products[0].uuid)
        self.assertTrue(products[0].is_operational)

        self.assertEqual('file.json', products[1].file_name)
        self.assertEqual('PRODUCT', products[1].file_type)
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
        products = ProductFile.objects.upload_files(self.files, [self.source_file.id, products_no[0].id],
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
                  'output_1', geo_metadata)]

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
    def test_batch_link(self):
        """Tests calling ProductFileManager.upload_files() successfully when associated with a batch"""

        job_type = job_test_utils.create_job_type(name='scale-batch-creator')
        job_exe = job_test_utils.create_job_exe(job_type=job_type)
        recipe_job = recipe_test_utils.create_recipe_job(job=job_exe.job)
        batch = batch_test_utils.create_batch()
        BatchRecipe.objects.create(batch_id=batch.id, recipe_id=recipe_job.recipe.id)
        BatchJob.objects.create(batch_id=batch.id, job_id=job_exe.job_id)

        products_no = ProductFile.objects.upload_files(self.files_no, [self.source_file.id], self.job_exe_no,
                                                       self.workspace)
        products = ProductFile.objects.upload_files(self.files, [self.source_file.id, products_no[0].id],
                                                    job_exe, self.workspace)

        self.assertEqual(batch.id, products[0].batch_id)

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_recipe_link(self):
        """Tests calling ProductFileManager.upload_files() successfully when associated with a recipe"""
        test_recipe = recipe_test_utils.create_recipe()
        recipe_job = recipe_test_utils.create_recipe_job(job=self.job_exe.job, recipe=test_recipe)

        products_no = ProductFile.objects.upload_files(self.files_no, [self.source_file.id], self.job_exe_no,
                                                       self.workspace)
        products = ProductFile.objects.upload_files(self.files, [self.source_file.id, products_no[0].id],
                                                    self.job_exe, self.workspace)

        self.assertEqual(recipe_job.recipe.id, products[0].recipe_id)
        self.assertEqual(recipe_job.node_name, products[0].recipe_node)

        self.assertEqual(self.files[0][3], products[0].job_output)

        recipe_manager = RecipeManager()
        self.assertEqual(recipe_manager.get_details(recipe_job.recipe.id).recipe_type, products[0].recipe_type)

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

    @patch('storage.models.os.path.getsize', lambda path: 100)
    def test_uuid_use_properties(self):
        """Tests setting UUIDs on products with different property values."""
        job_type = job_test_utils.create_job_type()
        job1 = job_test_utils.create_job(job_type=job_type)
        job_exe1 = job_test_utils.create_job_exe(job=job1)
        data1 = job_exe1.job.get_job_data()
        data1.add_property_input('property1', 'value1')
        data1.add_property_input('property2', 'value2')
        job_exe1.job.data = data1.get_dict()
        job2 = job_test_utils.create_job(job_type=job_type)
        job_exe2 = job_test_utils.create_job_exe(job=job2)
        data2 = job_exe2.job.get_job_data()
        data2.add_property_input('property1', 'diffvalue1')
        data2.add_property_input('property2', 'value2')
        job_exe2.job.data = data2.get_dict()

        products1 = ProductFile.objects.upload_files(self.files, [self.source_file.id], job_exe1, self.workspace)
        products2 = ProductFile.objects.upload_files(self.files, [self.source_file.id], job_exe2, self.workspace)

        # Make sure the product files have different UUIDs
        self.assertIsNotNone(products1[0].uuid)
        self.assertIsNotNone(products1[1].uuid)
        self.assertNotEqual(products1[0].uuid, products2[0].uuid)
        self.assertNotEqual(products1[1].uuid, products2[1].uuid)
