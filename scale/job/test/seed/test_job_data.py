from __future__ import unicode_literals

import django
from django.test import TransactionTestCase
from job.seed.results.job_results import JobResults
from mock import patch, Mock

from job.configuration.configuration import JobConfiguration
from job.configuration.data.data_file import AbstractDataFileStore
from job.configuration.results.exceptions import OutputCaptureError
from job.data.job_data import JobData
from job.seed.types import SeedInputFiles, SeedOutputFiles
from product.types import ProductFileMetadata
from storage.test import utils as storage_test_utils


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

    @patch('os.path.isfile', return_value=True)
    @patch('job.seed.results.job_results.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_store_output_files(self, dummy_store, isfile):

        workspace = storage_test_utils.create_workspace()

        files = {'OUTPUT_TIFFS': [ProductFileMetadata('OUTPUT_TIFFS', 'outfile0.tif', media_type='image/tiff')]}
        job_data = JobData({})

        job_config = JobConfiguration()
        job_config.add_output_workspace('OUTPUT_TIFFS', workspace.name)
        job_exe = Mock()
        job_exe.job.get_job_configuration.return_value = job_config

        results = JobResults()._store_output_data_files(files, job_data, job_exe)
        self.assertEqual({'OUTPUT_TIFFS': [1]}, results.files)

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_success_single_input_file(self, retrieve_files, join):
        job_data = JobData({'files': {'TEST_FILE_INPUT': [1]}})
        retrieve_files.return_value = {1: '/scale/input/TEST_FILE_INPUT'}

        data_files = [SeedInputFiles({'name':'TEST_FILE_INPUT', 'multiple': False, 'required': True, 'mediaTypes': [], 'partial': False})]

        result = job_data.retrieve_input_data_files(data_files)
        self.assertEqual(result, {'TEST_FILE_INPUT': ['/scale/input/TEST_FILE_INPUT']})

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_success_multiple_input_file(self, retrieve_files, join):
        job_data = JobData({'files': {'TEST_FILE_INPUT': [1, 2]}})
        retrieve_files.return_value = {1: '/scale/input/TEST_FILE_INPUT1', 2: '/scale/input/TEST_FILE_INPUT2'}

        data_files = [SeedInputFiles(
            {'name': 'TEST_FILE_INPUT', 'multiple': True, 'required': True, 'mediaTypes': [], 'partial': False})]

        result = job_data.retrieve_input_data_files(data_files)
        self.assertEqual(result, {'TEST_FILE_INPUT': ['/scale/input/TEST_FILE_INPUT1', '/scale/input/TEST_FILE_INPUT2']})

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_failure_multiple_for_single_input_file(self, retrieve_files, join):
        job_data = JobData({'files': {'TEST_FILE_INPUT': [1, 2]}})
        retrieve_files.return_value = {1: '/scale/input/TEST_FILE_INPUT1', 2: '/scale/input/TEST_FILE_INPUT2'}

        data_files = [SeedInputFiles(
            {'name': 'TEST_FILE_INPUT', 'multiple': False, 'required': True, 'mediaTypes': [], 'partial': False})]

        with self.assertRaises(Exception):
            job_data.retrieve_input_data_files(data_files)

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_missing_file(self, retrieve_files, join):
        job_data = JobData({'files': {'TEST_FILE_INPUT': [1]}})
        retrieve_files.return_value = {}

        data_files = [SeedInputFiles(
            {'name': 'TEST_FILE_INPUT', 'multiple': False, 'required': True, 'mediaTypes': [], 'partial': False})]

        with self.assertRaises(Exception):
            job_data.retrieve_input_data_files(data_files)

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_missing_plurality_mismatch(self, retrieve_files, join):
        job_data = JobData({'files': {'TEST_FILE_INPUT': [1]}})
        retrieve_files.return_value = {}

        data_files = [SeedInputFiles(
            {'name': 'TEST_FILE_INPUT', 'multiple': True, 'required': True, 'mediaTypes': [], 'partial': False})]

        with self.assertRaises(Exception):
            job_data.retrieve_input_data_files(data_files)

    @patch('os.path.join', return_value='/scale/input')
    @patch('job.data.job_data.JobData._retrieve_files')
    def test_retrieve_input_data_files_missing_file_not_required(self, retrieve_files, join):
        job_data = JobData({'files': {}})
        retrieve_files.return_value = {}

        data_files = [SeedInputFiles(
            {'name': 'TEST_FILE_INPUT', 'multiple': False, 'required': False, 'mediaTypes': [],
             'partial': False})]

        result = job_data.retrieve_input_data_files(data_files)
        self.assertEqual(result, {})

    @patch('job.data.job_data.ScaleFile.objects.download_files')
    @patch('job.data.job_data.ScaleFile.objects.filter')
    def test_retrieve_files_with_id(self, filter, download):
        job_data = JobData({'files': {}})
        filter.return_value = [Mock(id=1, file_name='input_thing_file'), Mock(id=2, file_name='input_other_file')]

        data_files = {1: ("/scale/input/INPUT_THING", False), 2: ("/scale/input/INPUT_OTHER", True)}

        result = job_data._retrieve_files(data_files)
        self.assertEqual(result, {1: "/scale/input/INPUT_THING/input_thing_file",
                                  2: "/scale/input/INPUT_OTHER/input_other_file"})
