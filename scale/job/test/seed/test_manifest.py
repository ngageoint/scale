from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch

from job.configuration.data.data_file import AbstractDataFileStore
from job.configuration.results.exceptions import OutputCaptureError
from job.data.job_data import JobData
from job.seed.types import SeedInputFiles
from product.types import ProductFileMetadata


class TestSeedManifest(TestCase):
    """Tests functions in the SeedManifest class."""

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

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_success_single_input_file(self, retrieve_files, join):
        job_data = JobData()
        job_data.add_file_input({'name':'TEST_FILE_INPUT', 'file_ids': [1]})
        retrieve_files.return_value = {1: '/scale/input/TEST_FILE_INPUT'}

        data_files = [SeedInputFiles({'name':'TEST_FILE_INPUT', 'multiple': False, 'required': True, 'mediaTypes': [], 'partial': False})]

        result = job_data.retrieve_input_data_files(data_files)
        self.assertEqual(result, {'TEST_FILE_INPUT': ['/scale/input/TEST_FILE_INPUT']})

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_success_multiple_input_file(self, retrieve_files, join):
        raise NotImplementedError

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_missing_file(self, retrieve_files, join):
        raise NotImplementedError

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_missing_plurality_mismatch(self, retrieve_files, join):
        raise NotImplementedError