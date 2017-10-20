from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
from mock import patch

from job.configuration.data.data_file import AbstractDataFileStore
from job.configuration.results.exceptions import OutputCaptureError
from job.data.job_data import JobData
from product.models import ProductFileMetadata


class DummyDataFileStore(AbstractDataFileStore):

    def get_workspaces(self, workspace_ids):
        results = {}
        if 1 in workspace_ids:
            results[long(1)] = True
        if 3 in workspace_ids:
            results[long(3)] = False
        return results

    def store_files(self, files, input_file_ids, job_exe):
        """

        :param files: workspace id -> [`ProductFileMetadata`]
        :param input_file_ids:
        :param job_exe:
        :return:
        """
        sequence = 1

        results = {}
        for workspace_id in files:
            for file_tuple in files[workspace_id]:
                file_path = file_tuple.local_path
                results[file_path] = sequence
                sequence += 1
        return results


class TestJobData(TransactionTestCase):
    """Tests functions in the JobData module."""

    def setUp(self):
        django.setup()

        self.test_output_snippet = {
            "name": "OUTPUT_TIFFS",
            "mediaType": "image/tiff",
            "pattern": "outfile*.tif",
            "multiple": False,
            "required": True
        }

    @patch('job.data.job_data.SeedOutputFiles.get_files')
    def test_capture_output_files_missing(self, get_files):
        get_files.side_effect = OutputCaptureError('message')

        with self.assertRaises(OutputCaptureError) as exc:
            JobData().capture_output_files([self.test_output_snippet])

    @patch('job.data.job_data.SeedOutputFiles.get_files')
    def test_capture_output_files_multiple(self, get_files):
        name = 'OUTPUT_TIFFS'
        get_files.return_value = ['outfile0.tif', 'outfile1.tif']

        outputs = JobData().capture_output_files([self.test_output_snippet])

        self.assertIn(name, outputs)
        files = outputs[name]
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].__dict__, ProductFileMetadata(name, 'outfile0.tif', media_type='image/tiff').__dict__)
        self.assertEqual(files[1].__dict__, ProductFileMetadata(name, 'outfile1.tif', media_type='image/tiff').__dict__)

    @patch('os.path.isfile', return_value=True)
    @patch('job.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_store_output_files(self, dummy_store, isfile):
        data = {'output_data':
                        {'files':
                         [{'name':'OUTPUT_TIFFS',
                           'workspace_id': 1}]}}
        files = {'OUTPUT_TIFFS': [ProductFileMetadata('OUTPUT_TIFFS', 'outfile0.tif', media_type='image/tiff')]}

        results = JobData(data).store_output_data_files(files, {}, None)
        self.assertEqual([{'name':'OUTPUT_TIFFS', 'file_ids': [1]}], results.output_data)


