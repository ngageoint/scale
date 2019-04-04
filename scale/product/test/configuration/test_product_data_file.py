from __future__ import unicode_literals

import os
import django

from django.test import TestCase, TransactionTestCase
from django.utils.text import get_valid_filename
from django.utils.timezone import now
from mock import MagicMock, patch

from job.execution.container import SCALE_JOB_EXE_OUTPUT_PATH
from job.test import utils as job_utils
from product.configuration.product_data_file import ProductDataFileStore
from product.types import ProductFileMetadata
from recipe.test import utils as recipe_utils
from storage.models import Workspace
from trigger.models import TriggerEvent


class TestProductDataFileStoreGetWorkspaces(TestCase):

    def setUp(self):
        django.setup()

        self.workspace_1 = Workspace.objects.create(name='Test workspace 1')
        self.workspace_2 = Workspace.objects.create(name='Test workspace 2', is_active=False)
        self.invalid_workspace_id = long(999)

    def test_successful(self):
        """Tests calling ProductDataFileStore.get_workspaces() successfully"""

        workspaces_ids = [self.workspace_1.id, self.workspace_2.id, self.invalid_workspace_id]

        results = ProductDataFileStore().get_workspaces(workspaces_ids)

        self.assertDictEqual(results, {self.workspace_1.id: True, self.workspace_2.id: False})


class TestProductDataFileStoreStoreFiles(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.workspace_1 = Workspace.objects.create(name='Test workspace 1')
        self.workspace_2 = Workspace.objects.create(name='Test workspace 2', is_active=False)

        manifest = job_utils.create_seed_manifest(name='Type-1')
        job_type = job_utils.create_seed_job_type(manifest=manifest)

        event = TriggerEvent.objects.create_trigger_event('TEST', None, {}, now())
        self.job = job_utils.create_job(job_type=job_type, event=event, status='RUNNING', last_status_change=now())
        self.job_exe = job_utils.create_job_exe(job=self.job, status='RUNNING', timeout=1, queued=now())
        self.remote_base_path = os.path.join('jobs', get_valid_filename(self.job.job_type.name),
                                             get_valid_filename(self.job.job_type.version))

    @patch('product.models.FileAncestryLink.objects.create_file_ancestry_links')
    @patch('product.models.ProductFile.objects.upload_files')
    def test_successful(self, mock_upload_files, mock_create_file_ancestry_links):
        """Tests calling ProductDataFileType.store_files() successfully"""

        local_path_1 = os.path.join('my', 'path', 'one', 'my_test.txt')
        media_type_1 = 'text/plain'
        job_output_1 = 'mock_output_1'
        local_path_2 = os.path.join('my', 'path', 'one', 'my_test.json')
        media_type_2 = 'application/json'
        job_output_2 = 'mock_output_2'
        local_path_3 = os.path.join('my', 'path', 'three', 'my_test.png')
        media_type_3 = 'image/png'
        job_output_3 = 'mock_output_3'
        local_path_4 = os.path.join('my', 'path', 'four', 'my_test.xml')
        media_type_4 = None
        job_output_4 = 'mock_output_4'

        # Set up mocks
        def new_upload_files(file_entries, input_file_ids, job_exe, workspace):
            results = []
            for file_entry in file_entries:
                # Check base remote path for job type name and version
                self.assertTrue(file_entry.remote_path.startswith(self.remote_base_path))
                if file_entry.local_path == local_path_1:
                    mock_1 = MagicMock()
                    mock_1.id = 1
                    results.append(mock_1)
                elif file_entry.local_path == local_path_2:
                    mock_2 = MagicMock()
                    mock_2.id = 2
                    results.append(mock_2)
                elif file_entry.local_path == local_path_3:
                    mock_3 = MagicMock()
                    mock_3.id = 3
                    results.append(mock_3)
                elif file_entry.local_path == local_path_4:
                    mock_4 = MagicMock()
                    mock_4.id = 4
                    results.append(mock_4)
            return results
        mock_upload_files.side_effect = new_upload_files

        data_files = {self.workspace_1.id: [ProductFileMetadata(output_name=job_output_1,
                                                                local_path=local_path_1,
                                                                media_type=media_type_1),
                                            ProductFileMetadata(output_name=job_output_2,
                                                                local_path=local_path_2,
                                                                media_type=media_type_2)],
                      self.workspace_2.id: [ProductFileMetadata(output_name=job_output_3,
                                                                local_path=local_path_3,
                                                                media_type=media_type_3),
                                            ProductFileMetadata(output_name=job_output_4,
                                                                local_path=local_path_4,
                                                                media_type=media_type_4)]}

        parent_ids = {98, 99}

        results = ProductDataFileStore().store_files(data_files, parent_ids, self.job_exe)

        self.assertDictEqual(results, {local_path_1: long(1), local_path_2: long(2), local_path_3: long(3),
                                       local_path_4: long(4)})
        mock_create_file_ancestry_links.assert_called_once_with(parent_ids, {1, 2, 3, 4}, self.job_exe.job,
                                                                self.job_exe.id)

    @patch('product.models.FileAncestryLink.objects.create_file_ancestry_links')
    @patch('product.models.ProductFile.objects.upload_files')
    def test_successful_recipe_path(self, mock_upload_files, mock_create_file_ancestry_links):
        """Tests calling ProductDataFileType.store_files() successfully with a job that is in a recipe"""

        job_exe_in_recipe = job_utils.create_job_exe(status='RUNNING')
        recipe = recipe_utils.create_recipe()
        _recipe_job = recipe_utils.create_recipe_job(recipe=recipe, job_name='My Job', job=job_exe_in_recipe.job)
        remote_base_path_with_recipe = os.path.join('recipes', get_valid_filename(recipe.recipe_type.name),
                                                    get_valid_filename('revision_%i'%recipe.recipe_type.revision_num), 'jobs',
                                                    get_valid_filename(job_exe_in_recipe.job.job_type.name),
                                                    get_valid_filename(job_exe_in_recipe.job.job_type.version))

        local_path_1 = os.path.join('my', 'path', 'one', 'my_test.txt')
        media_type_1 = 'text/plain'
        job_output_1 = 'mock_output_1'
        local_path_2 = os.path.join('my', 'path', 'one', 'my_test.json')
        media_type_2 = 'application/json'
        job_output_2 = 'mock_output_2'
        local_path_3 = os.path.join('my', 'path', 'three', 'my_test.png')
        media_type_3 = 'image/png'
        job_output_3 = 'mock_output_3'
        local_path_4 = os.path.join('my', 'path', 'four', 'my_test.xml')
        media_type_4 = None
        job_output_4 = 'mock_output_4'

        # Set up mocks
        def new_upload_files(file_entries, input_file_ids, job_exe, workspace):
            results = []
            for file_entry in file_entries:
                # Check base remote path for recipe type and job type information
                self.assertTrue(file_entry.remote_path.startswith(remote_base_path_with_recipe))
                if file_entry.local_path == local_path_1:
                    mock_1 = MagicMock()
                    mock_1.id = 1
                    results.append(mock_1)
                elif file_entry.local_path == local_path_2:
                    mock_2 = MagicMock()
                    mock_2.id = 2
                    results.append(mock_2)
                elif file_entry.local_path == local_path_3:
                    mock_3 = MagicMock()
                    mock_3.id = 3
                    results.append(mock_3)
                elif file_entry.local_path == local_path_4:
                    mock_4 = MagicMock()
                    mock_4.id = 4
                    results.append(mock_4)
            return results
        mock_upload_files.side_effect = new_upload_files

        data_files = {self.workspace_1.id: [ProductFileMetadata(output_name=job_output_1,
                                                                local_path=local_path_1,
                                                                media_type=media_type_1),
                                            ProductFileMetadata(output_name=job_output_2,
                                                                local_path=local_path_2,
                                                                media_type=media_type_2)],
                      self.workspace_2.id: [ProductFileMetadata(output_name=job_output_3,
                                                                local_path=local_path_3,
                                                                media_type=media_type_3),
                                            ProductFileMetadata(output_name=job_output_4,
                                                                local_path=local_path_4,
                                                                media_type=media_type_4)]}

        parent_ids = {98, 99}  # Dummy values

        ProductDataFileStore().store_files(data_files, parent_ids, job_exe_in_recipe)

    @patch('product.models.FileAncestryLink.objects.create_file_ancestry_links')
    @patch('product.models.ProductFile.objects.upload_files')
    def test_geo_metadata(self, mock_upload_files, mock_create_file_ancestry_links):
        """Tests calling ProductDataFileType.store_files() successfully"""

        geo_metadata = {
            "data_started": "2015-05-15T10:34:12Z",
            "data_ended": "2015-05-15T10:36:12Z",
            "geo_json": {
                "type": "Polygon",
                "coordinates": [[[1.0, 10.0], [2.0, 10.0], [2.0, 20.0],
                                 [1.0, 20.0], [1.0, 10.0]]]
            }
        }

        parent_ids = set([98, 99])
        local_path_1 = os.path.join('my', 'path', 'one', 'my_test.txt')
        full_local_path_1 = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, local_path_1)
        remote_path_1 = os.path.join(ProductDataFileStore()._calculate_remote_path(self.job_exe, parent_ids), local_path_1)
        media_type_1 = 'text/plain'
        job_output_1 = 'mock_output_1'
        local_path_2 = os.path.join('my', 'path', 'one', 'my_test.json')
        full_local_path_2 = os.path.join(SCALE_JOB_EXE_OUTPUT_PATH, local_path_2)
        remote_path_2 = os.path.join(ProductDataFileStore()._calculate_remote_path(self.job_exe, parent_ids), local_path_2)
        media_type_2 = 'application/json'
        job_output_2 = 'mock_output_2'
        metadata_1 = ProductFileMetadata(output_name=job_output_1,
                                         local_path=full_local_path_1,
                                         remote_path=remote_path_1,
                                         media_type=media_type_1,
                                         geojson=geo_metadata)
        metadata_2 = ProductFileMetadata(output_name=job_output_2,
                                         local_path=full_local_path_2,
                                         remote_path=remote_path_2,
                                         media_type=media_type_2)

        data_files = {self.workspace_1.id: [metadata_1, metadata_2]}
        ProductDataFileStore().store_files(data_files, parent_ids, self.job_exe)
        files_to_store = [metadata_1, metadata_2]
        mock_upload_files.assert_called_with(files_to_store, parent_ids, self.job_exe, self.workspace_1)
