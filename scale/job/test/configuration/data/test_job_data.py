from __future__ import unicode_literals
import os

import django
from django.test import TestCase
from mock import MagicMock, patch

from job.configuration.data.data_file import AbstractDataFileStore
from job.configuration.data.exceptions import InvalidData
from job.configuration.data.job_data import JobData
from job.configuration.interface.scale_file import ScaleFileDescription
from storage.test import utils as storage_utils


class DummyDataFileStore(AbstractDataFileStore):

    def get_workspaces(self, workspace_ids):
        results = {}
        if 1 in workspace_ids:
            results[long(1)] = True
        if 3 in workspace_ids:
            results[long(3)] = False
        return results

    def store_files(self, files, input_file_ids, job_exe):
        sequence = 1

        results = {}
        for workspace_id in files:
            for file_tuple in files[workspace_id]:
                file_path = file_tuple[0]
                results[file_path] = sequence
                sequence += 1
        return results


class TestJobDataAddFileInput(TestCase):

    def setUp(self):
        django.setup()

        self.file_1 = storage_utils.create_file('my_json_file.json', 'application/json')

    def test_successful(self):
        """Tests calling JobData.add_file_input() successfully."""

        data = {'input_data': []}
        job_data = JobData(data)

        # Method to test, we will test it by calling validate below
        job_data.add_file_input('File1', self.file_1.id)

        file_desc_1 = ScaleFileDescription()
        file_desc_1.add_allowed_media_type('application/json')
        files = {'File1': (True, False, file_desc_1)}
        # No exception is success
        warnings = JobData(data).validate_input_files(files)
        self.assertFalse(warnings)


class TestJobDataAddFileListInput(TestCase):

    def setUp(self):
        django.setup()

        self.file_1 = storage_utils.create_file('my_json_file.json', 'application/json')

    def test_successful(self):
        """Tests calling JobData.add_file_list_input() successfully."""

        data = {'input_data': []}
        job_data = JobData(data)

        # Method to test, we will test it by calling validate below
        job_data.add_file_list_input('File1', [self.file_1.id])

        file_desc_1 = ScaleFileDescription()
        file_desc_1.add_allowed_media_type('application/json')
        files = {'File1': (True, True, file_desc_1)}
        # No exception is success
        warnings = JobData(data).validate_input_files(files)
        self.assertFalse(warnings)


class TestJobDataAddOutput(TestCase):

    def setUp(self):
        django.setup()

    @patch('job.configuration.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful(self, mock_store):
        """Tests calling JobData.add_output() successfully."""

        data = {'output_data': []}
        job_data = JobData(data)

        # Method to test, we will test it by calling validate below
        job_data.add_output('File1', 1)

        files = ['File1']
        # No exception is success
        warnings = JobData(data).validate_output_files(files)
        self.assertFalse(warnings)


class TestJobDataAddPropertyInput(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests calling JobData.add_property_input() successfully."""

        data = {'input_data': []}
        job_data = JobData(data)

        # Method to test, we will test it by calling validate below
        job_data.add_property_input('Param1', 'Value1')

        properties = {'Param1': True}
        # No exception is success
        warnings = JobData(data).validate_properties(properties)
        self.assertFalse(warnings)


class TestJobDataGetInputFileIds(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests calling JobData.get_input_file_ids() successfully"""

        data = {'input_data': [{'name': 'Param1', 'value': 'Value1'},
                                {'name': 'Param2', 'file_id': 1},
                                {'name': 'Param3', 'file_ids': [5, 7, 23]},
                                {'name': 'Param4', 'file_id': 1},
                                {'name': 'Param5', 'value': 'Value5'}]}

        file_ids = JobData(data).get_input_file_ids()

        self.assertSetEqual(set(file_ids), set([1, 5, 7, 23]))


class TestJobDataGetPropertyValues(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests calling JobData.get_property_values() successfully"""

        data = {'input_data': [{'name': 'Param1', 'value': 'Value1'},
                                {'name': 'Param2', 'file_id': 1},
                                {'name': 'Param3', 'value': 'Value3'},
                                {'name': 'Param5', 'value': 'Value5'}]}
        property_names = ['Param1', 'Param3', 'Param4']

        property_values = JobData(data).get_property_values(property_names)

        self.assertDictEqual(property_values, {'Param1': 'Value1', 'Param3': 'Value3'})


class TestJobDataInit(TestCase):

    def setUp(self):
        django.setup()

    def test_init_blank(self):
        """Tests calling JobData constructor with blank JSON."""

        # No exception is success
        JobData({})

    def test_init_bad_version(self):
        """Tests calling JobData constructor with bad version number."""

        data = {'version': 'BAD VERSION'}
        self.assertRaises(InvalidData, JobData, data)

    def test_init_no_input_name(self):
        """Tests calling JobData constructor with missing data input name."""

        data = {'input_data': [{'value': '1'}]}
        self.assertRaises(InvalidData, JobData, data)

    def test_init_duplicate_input_name(self):
        """Tests calling JobData constructor with duplicate data input name."""

        data = {'input_data': [{'name': 'My Name', 'value': '1'},
                                {'name': 'My Name', 'value': '1'}]}
        self.assertRaises(InvalidData, JobData, data)

    def test_init_no_output_name(self):
        """Tests calling JobData constructor with missing data output name."""

        data = {'output_data': [{'value': '1'}]}
        self.assertRaises(InvalidData, JobData, data)

    def test_init_duplicate_output_name(self):
        """Tests calling JobData constructor with duplicate data output name."""

        data = {'output_data': [{'name': 'My Name', 'value': '1'},
                                 {'name': 'My Name', 'value': '1'}]}
        self.assertRaises(InvalidData, JobData, data)

    def test_init_duplicate_input_output_name(self):
        """Tests calling JobData constructor with duplicate data input and output name."""

        data = {'input_data': [{'name': 'My Name', 'value': '1'}],
                'output_data': [{'name': 'My Name', 'value': '1'}]}
        self.assertRaises(InvalidData, JobData, data)

    def test_init_successful_one_property(self):
        """Tests calling JobData constructor successfully with a single property input."""

        data = {'input_data': [{'name': 'My Name', 'value': '1'}]}

        # No exception is success
        JobData(data)


class TestJobDataRetrieveFiles(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_utils.create_workspace()
        self.file_name_1 = 'my_file.txt'
        self.media_type_1 = 'text/plain'
        self.product_file_1 = storage_utils.create_file(file_name=self.file_name_1, media_type=self.media_type_1,
                                                        workspace=self.workspace)

        self.file_name_2 = 'my_file.txt'
        self.media_type_2 = 'text/plain'
        self.product_file_2 = storage_utils.create_file(file_name=self.file_name_2, media_type=self.media_type_2,
                                                        workspace=self.workspace)

        self.invalid_product_file_id = long(999)

    @patch('storage.models.ScaleFile.objects.download_files')
    def test_successful(self, mock_download_files):
        """Tests calling JobData._retrieve_files() successfully"""

        dir_path_1 = os.path.join('/my', 'path', 'one')
        file_path_1 = os.path.join(dir_path_1, self.file_name_1)

        # File name collision, so expect a different file name here
        file_path_2 = os.path.join(dir_path_1, '1_' + self.file_name_2)

        dir_path_2 = os.path.join('/my', 'path', 'two')
        data_files = {
            self.product_file_1.id: dir_path_1,
            self.product_file_2.id: dir_path_1,
            self.invalid_product_file_id: dir_path_2,
        }

        retrieved_files = JobData({})._retrieve_files(data_files)

        self.assertDictEqual(retrieved_files, {
            self.product_file_1.id: file_path_1,
            self.product_file_2.id: file_path_2,
        })


class TestJobDataRetrieveInputDataFiles(TestCase):

    def setUp(self):
        django.setup()

        self.file_1 = storage_utils.create_file('my_json_file.json', 'application/json')
        self.file_2 = storage_utils.create_file('my_text_file_1.txt', 'text/plain')
        self.file_3 = storage_utils.create_file('my_text_file_2.txt', 'text/plain')

    @patch('job.configuration.data.job_data.ScaleFile.objects.download_files')
    def test_bad_file_id(self, mock_download_files):
        """Tests calling JobData.retrieve_input_data_files() with an invalid file ID"""

        download_dir = 'download'
        work_dir = 'work'
        data = {'input_data': [{'name': 'Param1', 'file_id': 999999}]}
        file_path_1 = os.path.join('path', '1')
        data_files = {'Param1': (False, file_path_1)}

        self.assertRaises(Exception, JobData(data).retrieve_input_data_files, download_dir, work_dir, data_files)

    @patch('job.configuration.data.job_data.ScaleFile.objects.download_files')
    def test_successful(self, mock_download_files):
        """Tests calling JobData.retrieve_input_data_files() successfully"""

        data = {'input_data': [{'name': 'Param1', 'file_id': self.file_1.id},
                                {'name': 'Param2', 'value': 'Value2'},
                                {'name': 'Param3', 'file_ids': [self.file_2.id, self.file_3.id]},
                                {'name': 'Param5', 'file_id': 5}]}
        file_path_1 = os.path.join('/path', '1')
        file_path_3 = os.path.join('/path', '3')
        file_path_4 = os.path.join('/path', '4')
        data_files = {'Param1': (False, file_path_1), 'Param3': (True, file_path_3), 'Param4': (True, file_path_4)}

        results = JobData(data).retrieve_input_data_files(data_files)

        results_path_1 = os.path.join(file_path_1, 'my_json_file.json')
        results_path_3 = os.path.join(file_path_3, 'my_text_file_1.txt')
        results_path_33 = os.path.join(file_path_3, 'my_text_file_2.txt')
        self.assertDictEqual(results, {'Param1': [results_path_1], 'Param3': [results_path_3, results_path_33]})


class TestJobDataStoreOutputDataFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('job.configuration.data.job_data.os.path.isfile')
    @patch('job.configuration.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    @patch('job.configuration.data.job_data.JobResults.add_file_list_parameter')
    @patch('job.configuration.data.job_data.JobResults.add_file_parameter')
    def test_successful(self, mock_file_call, mock_file_list_call, mock_store, mock_isfile):
        """Tests calling JobData.store_output_data_files() successfully"""

        def new_isfile(path):
            return True
        mock_isfile.side_effect = new_isfile

        job_exe = MagicMock()
        job_exe.id = 1
        data = {'output_data': [{'name': 'Param1', 'workspace_id': 1},
                                 {'name': 'Param2', 'workspace_id': 2}]}
        file_path_1 = os.path.join('/path', '1', 'my_file.txt')
        file_path_2 = os.path.join('/path', '2', 'my_file_2.txt')
        file_path_3 = os.path.join('/path', '3', 'my_file_3.txt')
        data_files = {'Param1': (file_path_1, None), 'Param2': [(file_path_2, 'text/plain'), (file_path_3, None)]}

        JobData(data).store_output_data_files(data_files, job_exe)
        mock_file_call.assert_called_once_with('Param1', long(1))
        self.assertEqual('Param2', mock_file_list_call.call_args[0][0])
        self.assertSetEqual(set([long(3), long(2)]), set(mock_file_list_call.call_args[0][1]))


class TestJobDataValidateInputFiles(TestCase):

    def setUp(self):
        django.setup()

        self.file_1 = storage_utils.create_file('my_json_file.json', 'application/json')
        self.file_2 = storage_utils.create_file('my_text_file_1.txt', 'text/plain')
        self.file_3 = storage_utils.create_file('my_text_file_2.txt', 'text/plain')

    def test_missing_required(self):
        """Tests calling JobData.validate_input_files() when a file is required, but missing"""

        data = {'input_data': []}
        files = {'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidData, JobData(data).validate_input_files, files)

    def test_not_required(self):
        """Tests calling JobData.validate_input_files() when a file is missing, but required"""

        data = {'input_data': []}
        files = {'File1': (False, True, ScaleFileDescription())}
        # No exception is success
        warnings = JobData(data).validate_input_files(files)
        self.assertFalse(warnings)

    def test_multiple_missing_file_ids(self):
        """Tests calling JobData.validate_input_files() with a multiple file param missing the file_ids field"""

        data = {'input_data': [{'name': 'File1'}]}
        files = {'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidData, JobData(data).validate_input_files, files)

    def test_multiple_non_list(self):
        """Tests calling JobData.validate_input_files() with a multiple file param with a non-list for file_ids field"""

        data = {'input_data': [{'name': 'File1', 'file_ids': 'STRING'}]}
        files = {'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidData, JobData(data).validate_input_files, files)

    def test_multiple_non_integrals(self):
        """Tests calling JobData.validate_input_files() with a multiple file param and non-integral file_ids field"""

        data = {'input_data': [{'name': 'File1', 'file_ids': [123, 'STRING']}]}
        files = {'File1': (True, True, ScaleFileDescription())}
        self.assertRaises(InvalidData, JobData(data).validate_input_files, files)

    def test_multiple_given_single(self):
        """Tests calling JobData.validate_input_files() with a multiple file param given with a single file ID"""

        data = {'input_data': [{'name': 'File1', 'file_id': self.file_1.id}]}
        files = {'File1': (True, True, ScaleFileDescription())}
        # No exception is success
        warnings = JobData(data).validate_input_files(files)
        self.assertFalse(warnings)

    def test_single_missing_file_id(self):
        """Tests calling JobData.validate_input_files() with a single file param missing the file_id field"""

        data = {'input_data': [{'name': 'File1'}]}
        files = {'File1': (True, False, ScaleFileDescription())}
        self.assertRaises(InvalidData, JobData(data).validate_input_files, files)

    def test_single_non_integral(self):
        """Tests calling JobData.validate_input_files() with a single file param and non-integral file_id field"""

        data = {'input_data': [{'name': 'File1', 'file_id': 'STRING'}]}
        files = {'File1': (True, False, ScaleFileDescription())}
        self.assertRaises(InvalidData, JobData(data).validate_input_files, files)

    def test_bad_media_type(self):
        """Tests calling JobData.validate_input_files() with a file that has an invalid media type"""

        data = {'input_data': [{'name': 'File1', 'file_id': self.file_1.id}]}
        file_desc_1 = ScaleFileDescription()
        file_desc_1.add_allowed_media_type('text/plain')
        files = {'File1': (True, False, file_desc_1)}
        warnings = JobData(data).validate_input_files(files)
        self.assertTrue(warnings)

    def test_bad_file_id(self):
        """Tests calling JobData.validate_input_files() with a file that has an invalid ID"""

        data = {'input_data': [{'name': 'File1', 'file_id': 9999999999}]}
        files = {'File1': (True, False, ScaleFileDescription())}
        self.assertRaises(InvalidData, JobData(data).validate_input_files, files)

    def test_successful(self):
        """Tests calling JobData.validate_input_files() with a valid set of job data"""

        data = {'input_data': [{'name': 'File1', 'file_id': self.file_1.id},
                                {'name': 'File3', 'file_ids': [self.file_2.id]}]}
        file_desc_1 = ScaleFileDescription()
        file_desc_1.add_allowed_media_type('application/json')
        file_desc_3 = ScaleFileDescription()
        file_desc_3.add_allowed_media_type('text/plain')
        files = {'File1': (True, False, file_desc_1),
                 'File3': (True, True, file_desc_3)}
        # No exception is success
        warnings = JobData(data).validate_input_files(files)
        self.assertFalse(warnings)


class TestJobDataValidateOutputFiles(TestCase):

    def setUp(self):
        django.setup()

    @patch('job.configuration.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_missing_output(self, mock_store):
        """Tests calling JobData.validate_output_files() when an output is missing"""

        data = {'output_data': []}
        files = ['File1']
        self.assertRaises(InvalidData, JobData(data).validate_output_files, files)

    @patch('job.configuration.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_missing_workspace_id(self, mock_store):
        """Tests calling JobData.validate_output_files() when an output is missing the workspace_id field"""

        data = {'output_data': [{'name': 'File1'}]}
        files = ['File1']
        self.assertRaises(InvalidData, JobData(data).validate_output_files, files)

    @patch('job.configuration.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_multiple_outputs(self, mock_store):
        """Tests calling JobData.validate_output_files() when there are multiple outputs with the same workspace id"""

        data = {'output_data': [{'name': 'File1', 'workspace_id': 1}, {'name': 'File2', 'workspace_id': 1}]}
        files = ['File1', 'File2']
        # No exception is success
        warnings = JobData(data).validate_output_files(files)
        self.assertFalse(warnings)

    @patch('job.configuration.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_workspace_id_not_integer(self, mock_store):
        """Tests calling JobData.validate_output_files() when an output has a non-integral value for workspace_id"""

        data = {'output_data': [{'name': 'File1', 'workspace_id': 'foo'}]}
        files = ['File1']
        self.assertRaises(InvalidData, JobData(data).validate_output_files, files)

    @patch('job.configuration.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_workspace_not_exist(self, mock_store):
        """Tests calling JobData.validate_output_files() with a workspace that does not exist"""

        data = {'output_data': [{'name': 'File1', 'workspace_id': 2}]}
        files = ['File1']
        self.assertRaises(InvalidData, JobData(data).validate_output_files, files)

    @patch('job.configuration.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_workspace_not_active(self, mock_store):
        """Tests calling JobData.validate_output_files() with a workspace that is not active"""

        data = {'output_data': [{'name': 'File1', 'workspace_id': 3}]}
        files = ['File1']
        self.assertRaises(InvalidData, JobData(data).validate_output_files, files)

    @patch('job.configuration.data.job_data.DATA_FILE_STORE',
           new_callable=lambda: {'DATA_FILE_STORE': DummyDataFileStore()})
    def test_successful(self, mock_store):
        """Tests calling JobData.validate_output_files() with successful data"""

        data = {'output_data': [{'name': 'File1', 'workspace_id': 1}]}
        files = ['File1']
        # No exception is success
        warnings = JobData(data).validate_output_files(files)
        self.assertFalse(warnings)


class TestJobDataValidateProperties(TestCase):

    def setUp(self):
        django.setup()

    def test_missing_value(self):
        """Tests calling JobData.validate_properties() when a property is missing a value"""

        data = {'input_data': [{'name': 'Param1'}]}
        properties = {'Param1': False}
        self.assertRaises(InvalidData, JobData(data).validate_properties, properties)

    def test_value_not_string(self):
        """Tests calling JobData.validate_properties() when a property has a non-string value"""

        data = {'input_data': [{'name': 'Param1', 'value': 123}]}
        properties = {'Param1': False}
        self.assertRaises(InvalidData, JobData(data).validate_properties, properties)

    def test_missing_required(self):
        """Tests calling JobData.validate_properties() when a property is required, but missing"""

        data = {'input_data': []}
        properties = {'Param1': True}
        self.assertRaises(InvalidData, JobData(data).validate_properties, properties)

    def test_not_required(self):
        """Tests calling JobData.validate_properties() when a property is missing, but is not required"""

        data = {'input_data': []}
        properties = {'Param1': False}
        # No exception is success
        warnings = JobData(data).validate_properties(properties)
        self.assertFalse(warnings)

    def test_required_successful(self):
        """Tests calling JobData.validate_properties() successfully with a required property"""

        data = {'input_data': [{'name': 'Param1', 'value': 'Value1'}]}
        properties = {'Param1': True}
        # No exception is success
        warnings = JobData(data).validate_properties(properties)
        self.assertFalse(warnings)
