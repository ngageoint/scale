#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import os
import django

from django.utils.timezone import now
from django.test import TestCase
from mock import MagicMock, patch

from job.models import Job, JobExecution, JobType
from job.test import utils as job_utils
from product.configuration.product_data_file import ProductDataFileStore
from storage.models import Workspace
from trigger.models import TriggerEvent


class TestProductDataFileStoreGetWorkspaces(TestCase):

    def setUp(self):
        django.setup()

        self.workspace_1 = Workspace.objects.create(name='Test workspace 1')
        self.workspace_2 = Workspace.objects.create(name='Test workspace 2', is_active=False)
        self.invalid_workspace_id = long(999)

    def test_successful(self):
        '''Tests calling ProductDataFileStore.get_workspaces() successfully'''

        workspaces_ids = [self.workspace_1.id, self.workspace_2.id, self.invalid_workspace_id]

        results = ProductDataFileStore().get_workspaces(workspaces_ids)

        self.assertDictEqual(results, {self.workspace_1.id: True, self.workspace_2.id: False})


class TestProductDataFileStoreStoreFiles(TestCase):

    def setUp(self):
        django.setup()

        self.workspace_1 = Workspace.objects.create(name='Test workspace 1')
        self.workspace_2 = Workspace.objects.create(name='Test workspace 2', is_active=False)

        interface = {'version': '1.0', 'command': 'my command'}  

        job_type = job_utils.create_job_type(name='Type 1', version='1.0', interface=interface)

        event = TriggerEvent.objects.create_trigger_event('TEST', None, {}, now())
        self.job = job_utils.create_job(job_type=job_type, event=event, status='RUNNING', last_status_change=now())
        self.job_exe = job_utils.create_job_exe(job=self.job, status='RUNNING', timeout=1, queued=now())

    @patch('product.models.FileAncestryLink.objects.create_file_ancestry_links')
    @patch('product.models.ProductFile.objects.upload_files')
    def test_successful(self, mock_upload_files, mock_create_file_ancestry_links):
        '''Tests calling ProductDataFileType.store_files() successfully'''

        local_path_1 = os.path.join('my', 'path', 'one', 'my_test.txt')
        media_type_1 = 'text/plain'
        local_path_2 = os.path.join('my', 'path', 'one', 'my_test.json')
        media_type_2 = 'application/json'
        local_path_3 = os.path.join('my', 'path', 'three', 'my_test.png')
        media_type_3 = 'image/png'
        local_path_4 = os.path.join('my', 'path', 'four', 'my_test.xml')
        media_type_4 = None

        # Set up mocks
        def new_upload_files(upload_dir, work_dir, file_entries, input_file_ids, job_exe, workspace):
            results = []
            for file_entry in file_entries:
                if file_entry[0] == local_path_1:
                    mock_1 = MagicMock()
                    mock_1.id = 1
                    results.append(mock_1)
                elif file_entry[0] == local_path_2:
                    mock_2 = MagicMock()
                    mock_2.id = 2
                    results.append(mock_2)
                elif file_entry[0] == local_path_3:
                    mock_3 = MagicMock()
                    mock_3.id = 3
                    results.append(mock_3)
                elif file_entry[0] == local_path_4:
                    mock_4 = MagicMock()
                    mock_4.id = 4
                    results.append(mock_4)
            return results
        mock_upload_files.side_effect = new_upload_files

        data_files = {self.workspace_1.id: [(local_path_1, media_type_1), (local_path_2, media_type_2)],
                      self.workspace_2.id: [(local_path_3, media_type_3), (local_path_4, media_type_4)]}

        parent_ids = set([98, 99])

        upload_dir = 'upload_dir'
        results = ProductDataFileStore().store_files(upload_dir, 'work_dir', data_files, parent_ids, self.job_exe)

        self.assertDictEqual(results, {os.path.join(upload_dir, local_path_1): long(1), os.path.join(upload_dir, local_path_2): long(2),
                                       os.path.join(upload_dir, local_path_3): long(3), os.path.join(upload_dir, local_path_4): long(4)})
        mock_create_file_ancestry_links.assert_once_called_with(parent_ids, set([1, 2, 3, 4]))

    @patch('product.models.FileAncestryLink.objects.create_file_ancestry_links')
    @patch('product.models.ProductFile.objects.upload_files')
    def test_geo_metadata(self, mock_upload_files, mock_create_file_ancestry_links):
        '''Tests calling ProductDataFileType.store_files() successfully'''

        geo_metadata = {
            "data_started": "2015-05-15T10:34:12Z",
            "data_ended": "2015-05-15T10:36:12Z",
            "geo_json": {
                "type": "Polygon",
                "coordinates": [[[1.0, 10.0], [2.0, 10.0], [2.0, 20.0],
                                 [1.0, 20.0], [1.0, 10.0]]]
            }
        }

        upload_dir = 'upload_dir'
        work_dir = 'work_dir'

        parent_ids = set([98, 99])
        local_path_1 = os.path.join('my', 'path', 'one', 'my_test.txt')
        remote_path_1 = os.path.join(ProductDataFileStore()._calculate_remote_path(self.job_exe, parent_ids), local_path_1)
        media_type_1 = 'text/plain'
        local_path_2 = os.path.join('my', 'path', 'one', 'my_test.json')
        remote_path_2 = os.path.join(ProductDataFileStore()._calculate_remote_path(self.job_exe, parent_ids), local_path_2)
        media_type_2 = 'application/json'

        data_files = {self.workspace_1.id: [(local_path_1, media_type_1, geo_metadata), (local_path_2, media_type_2)]}
        ProductDataFileStore().store_files(upload_dir, work_dir, data_files, parent_ids, self.job_exe)
        files_to_store = [(local_path_1, remote_path_1, media_type_1, geo_metadata),
                          (local_path_2, remote_path_2, media_type_2)]
        mock_upload_files.assert_called_with(upload_dir, work_dir, files_to_store, parent_ids, self.job_exe, self.workspace_1)
