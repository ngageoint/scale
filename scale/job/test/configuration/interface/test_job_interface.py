#@PydevCodeAnalysisIgnore
import os

import django
from django.test import TestCase
from mock import patch, MagicMock, Mock

from job.configuration.data.exceptions import InvalidConnection
from job.configuration.data.job_connection import JobConnection
from job.configuration.data.job_data import JobData
from job.configuration.environment.job_environment import JobEnvironment
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.configuration.interface.job_interface import JobInterface
from job.execution.file_system import get_job_exe_input_data_dir, get_job_exe_output_data_dir, get_job_exe_output_work_dir
from storage.test import utils as storage_utils


class TestJobInterfaceAddOutputToConnection(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        '''Tests calling JobInterface.add_output_to_connection() successfully.'''
        job_interface_dict = {
            u'command': u'simple-command',
            u'command_arguments': u'',
            u'version': u'1.0',
            u'input_data': [],
            u'output_data': [{u'name': u'Output 1', u'type': u'file'}]
        }

        job_interface = JobInterface(job_interface_dict)
        job_conn = MagicMock()

        job_interface.add_output_to_connection(u'Output 1', job_conn, u'Input 1')
        job_conn.add_input_file.assert_called_with(u'Input 1', False, [], False)


class TestJobInterfacePostSteps(TestCase):

    def setUp(self):
        django.setup()

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_output_file(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'output_data'] = [{"name":"output_file", "type":"file", "required": True}]
        job_data_dict[u'output_data'].append({"name":"output_file", "workspace_id":1})
        results_manifest={"version" : "1.0", "files" : [{"name":"output_file", "path":"/some/path/foo.txt"}]}
        mock_loads.return_value = results_manifest 
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = u''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({u'output_file': (u'/some/path/foo.txt', None)}, job_exe)

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_output_files(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'output_data'] = [{"name":"output_files", "type":"files", "required": True}]
        job_data_dict[u'output_data'].append({"name":"output_files", "workspace_id":1})
        results_manifest={"version" : "1.0", "files" : [{"name":"output_files", "paths": ["/some/path/foo.txt", "/other/path/foo.txt"]}]}
        mock_loads.return_value = results_manifest 
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = u''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({u'output_files': [(u'/some/path/foo.txt', None),(u'/other/path/foo.txt', None)]}, job_exe)

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_output_file_with_geo_metadata(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'output_data'] = [{"name":"output_file", "type":"file", "required": True}]
        job_data_dict[u'output_data'].append({"name":"output_file", "workspace_id":1})
        geo_metadata = {
            "data_started": "2015-05-15T10:34:12Z",
            "data_ended" : "2015-05-15T10:36:12Z",
            "geo_json": {
                "type": "Polygon",
                "coordinates": [ [ [ 1.0, 10.0 ], [ 2.0, 10.0 ], [ 2.0, 20.0 ],[ 1.0, 20.0 ], [ 1.0, 10.0 ] ] ]
            }
        }
        results_manifest = {
            "version": "1.1",
            "output_data": [
                {
                    "name" : "output_file",
                    "file": {
                        "path" : "/some/path/foo.txt",
                        "geo_metadata": geo_metadata
                    }
                }
            ]
        }
        mock_loads.return_value = results_manifest 
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = u''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({u'output_file': (u'/some/path/foo.txt', None, geo_metadata)}, job_exe)

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_output_files_with_geo_metadata(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'output_data'] = [{"name":"output_files", "type":"files", "required": True}]
        job_data_dict[u'output_data'].append({"name":"output_files", "workspace_id":1})
        geo_metadata = {
            "data_started": "2015-05-15T10:34:12Z",
            "data_ended": "2015-05-15T10:36:12Z",
            "geo_json": {
                "type": "Polygon",
                "coordinates": [[[ 1.0, 10.0 ], [ 2.0, 10.0 ], [ 2.0, 20.0 ],[ 1.0, 20.0 ], [ 1.0, 10.0 ]]]
            }
        }
        results_manifest = {
            "version": "1.1",
            "output_data": [
                {
                    "name" : "output_files",
                    "files": [
                        {
                            "path" : "/some/path/foo.txt",
                            "geo_metadata": geo_metadata
                        },
                        {
                            "path" : "/other/path/foo.txt",
                            "geo_metadata": geo_metadata
                        }
                    ]
                }
            ]
        }
         
        mock_loads.return_value = results_manifest 
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = u''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with(
            {u'output_files': [(u'/some/path/foo.txt', None, geo_metadata),(u'/other/path/foo.txt', None, geo_metadata)]}, job_exe)

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_parse_data(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'input_data'] = [{"name":"input_file", "type":"file", "required": True}]
        job_data_dict[u'input_data'].append({"name":"input_file", "file_id":1})
        geo_json = {"type": 'Feature'}
        geo_metadata = {
            "data_started": '2015-01-01T00:00:00Z',
            "geo_json": geo_json
        }
        results_manifest={"version" : "1.1", "parse_results" : [{"filename":"/some/path/foo.txt", "geo_metadata":geo_metadata}]}
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = u''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.save_parse_results.assert_called_with({u'/some/path/foo.txt': (geo_json, '2015-01-01T00:00:00Z', None, [], None, None)})

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_parse_stdout(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'input_data'] = [{"name":"input_file", "type":"file", "required": True}]
        job_interface_dict[u'output_data'] = [{"name":"output_file", "type":"file", "required": True},{"name":"output_file_2", "type":"file", "required": True}]
        job_data_dict[u'input_data'].append({"name":"input_file", "file_id":1})
        results_manifest={}
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = '''
This text is supposed to mimick the output
of a program we should see artifacts registered with
the format: ARTIFACT:<input-name>:path, but it needs be at the beginning of a line
so the example above won't match, but this will
ARTIFACT:output_file:/path/to/foo.txt
We should also be able to have text after the artifact and multiple artifacts.
ARTIFACT:output_file_2:/path/to/foo_2.txt
'''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({u'output_file': (u'/path/to/foo.txt', None), u'output_file_2': (u'/path/to/foo_2.txt', None)}, job_exe)

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_parse_stdout_required(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'input_data'] = [{"name":"input_file", "type":"file", "required": True}]
        job_interface_dict[u'output_data'] = [{"name":"output_file", "type":"file", "required": True}]
        job_data_dict[u'input_data'].append({"name":"input_file", "file_id":1})
        results_manifest={}
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = '''
This text is supposed to mimick the output
of a program we should see artifacts registered with
the format: ARTIFACT:<input-name>:path, but it needs be at the beginning of a line
so the example above won't match, but this will
ARTIFACT:output_file:/path/to/foo.txt
'''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({u'output_file': (u'/path/to/foo.txt', None)}, job_exe)

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_manifest_overrides_stdout(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'input_data'] = [{"name":"input_file", "type":"file", "required": True}]
        job_interface_dict[u'output_data'] = [{"name":"output_file", "type":"file", "required": True},{"name":"output_file_2", "type":"file", "required": True}]
        job_data_dict[u'input_data'].append({"name":"input_file", "file_id":1})
        results_manifest={"version" : "1.0", "files" : [{"name":"output_file", "path":"/new/path/foo.txt"}]}
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = '''
This text is supposed to mimick the output
of a program we should see artifacts registered with
the format: ARTIFACT:<input-name>:path, but it needs be at the beginning of a line
so the example above won't match, but this will
ARTIFACT:output_file:/path/to/foo.txt
We should also be able to have text after the artifact and multiple artifacts.
ARTIFACT:output_file_2:/path/to/foo_2.txt
'''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({u'output_file': (u'/new/path/foo.txt', None), u'output_file_2': (u'/path/to/foo_2.txt', None)}, job_exe)


    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_extra_products_are_fine(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'input_data'] = [{"name":"input_file", "type":"file", "required": True}]
        job_interface_dict[u'output_data'] = [{"name":"output_file", "type":"file", "required": True}]
        job_data_dict[u'input_data'].append({"name":"input_file", "file_id":1})
        results_manifest={"version" : "1.0", "files" : [{"name":"output_file", "path":"/new/path/foo.txt"}]}
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = '''
This text is supposed to mimick the output
of a program we should see artifacts registered with
the format: ARTIFACT:<input-name>:path, but it needs be at the beginning of a line
so the example above won't match, but this will
ARTIFACT:output_file:/path/to/foo.txt
We should also be able to have text after the artifact and multiple artifacts.
ARTIFACT:output_file_2:/path/to/foo_2.txt
'''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({u'output_file': (u'/new/path/foo.txt', None)}, job_exe)

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface.json.loads')
    def test_output_data_media_types(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict= self._get_simple_interface_data()
        job_interface_dict[u'output_data'] = [{"name":"output_file", "type":"file", "required": True, "media_type": "text/x-some-weird-type"}]
        job_data_dict[u'output_data'].append({"name":"output_file", "workspace_id":1})
        results_manifest={"version" : "1.0", "files" : [{"name":"output_file", "path":"/some/path/foo.txt"}]}
        mock_loads.return_value = results_manifest 
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = u''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({u'output_file': (u'/some/path/foo.txt', 'text/x-some-weird-type')}, job_exe)

    def _get_simple_interface_data(self):
        job_interface_dict = {
            u'command': u'simple-command',
            u'command_arguments': u'',
            u'version': u'1.0'
        }

        job_data_dict = {
            u'version': u'1.0',
            u'input_data': [],
            u'output_data': [],
            u'shared_resources': []
        }

        return job_interface_dict, job_data_dict


class TestJobInterfacePreSteps(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_utils.create_workspace()

    def test_simple_case(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = JobEnvironment(job_environment_dict)

        job_work_dir = "/test"
        job_exe_id = 1
        
        job_interface.perform_pre_steps(job_data, job_environment, 1)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, u'', u'expected a different command from pre_steps')

    def test_property_in_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict[u'command_arguments'] = u'${prop1}'
        job_interface_dict[u'input_data'] = [{u'name' : u'prop1', u'type' : u'property', 'required' : True}]
        job_data_dict[u'input_data'].append({u'name': u'prop1', u'value': u'property-value'})

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = JobEnvironment(job_environment_dict)
        
        job_work_dir = "/test"
        job_exe_id = 1
        
        job_interface.perform_pre_steps(job_data, job_environment, 1)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, u'property-value', u'expected a different command from pre_steps')

    def test_complex_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict[u'command_arguments'] = u'${-f :prop1}'
        job_interface_dict[u'input_data'] = [{u'name' : u'prop1', u'type' : u'property', 'required' : True}]
        job_data_dict[u'input_data'].append({u'name': u'prop1', u'value': u'property-value'})

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = JobEnvironment(job_environment_dict)
        
        job_work_dir = "/test"
        job_exe_id = 1
        
        job_interface.perform_pre_steps(job_data, job_environment, 1)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, u'-f property-value', u'expected a different command from pre_steps')

    @patch('job.configuration.data.job_data.ScaleFile.objects.setup_upload_dir')
    @patch('job.configuration.interface.job_interface.JobInterface._get_one_file_from_directory')
    @patch('os.mkdir')
    @patch('job.configuration.data.job_data.JobData.retrieve_input_data_files')
    def test_file_in_command(self, mock_retrieve_call, mock_os_mkdir, mock_get_one_file, mock_setup_upload):
        job_work_dir = "/test"
        job_exe_id = 1
        job_input_dir = get_job_exe_input_data_dir(job_exe_id)
        job_output_dir = os.path.join(job_work_dir, u'outputs')

        def new_retrieve(arg1, arg2, arg3):
            return {u'file1_out': [input_file_path]}

        input_file_path = os.path.join(job_input_dir, 'file1', 'foo.txt')
        mock_retrieve_call.side_effect = new_retrieve
        mock_get_one_file.side_effect = lambda(arg1): input_file_path
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict[u'command_arguments'] = u'${file1}'
        job_interface_dict[u'input_data'] = [{u'name' : u'file1', u'type' : u'file', 'required' : True}]
        job_data_dict[u'input_data'].append({u'name': u'file1', u'file_id': 1})
        job_data_dict[u'output_data'].append({u'name': u'file1_out', u'workspace_id': self.workspace.id})

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = JobEnvironment(job_environment_dict)
        
        
        job_interface.perform_pre_steps(job_data, job_environment, job_exe_id)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, input_file_path, u'expected a different command from pre_steps')
        mock_setup_upload.assert_called_once_with(get_job_exe_output_data_dir(job_exe_id), get_job_exe_output_work_dir(job_exe_id), self.workspace)

    @patch('job.configuration.data.job_data.ScaleFile.objects.setup_upload_dir')
    @patch('os.mkdir')
    @patch('job.configuration.data.job_data.JobData.retrieve_input_data_files')
    def test_files_in_command(self, mock_retrieve_call, mock_os_mkdir, mock_setup_upload):
        def new_retrieve(arg1, arg2, arg3):
            return {u'files1_out': [u'/test/file1/foo.txt', u'/test/file1/bar.txt']}

        mock_retrieve_call.side_effect = new_retrieve
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict[u'command_arguments'] = u'${files1}'
        job_interface_dict[u'input_data'] = [{u'name' : u'files1', u'type' : u'files', 'required' : True}]
        job_data_dict[u'input_data'].append({u'name': u'files1', u'file_ids': [1,2,3]})
        job_data_dict[u'output_data'].append({u'name': u'files1_out', u'workspace_id': self.workspace.id})

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = JobEnvironment(job_environment_dict)

        job_work_dir = "/test"
        job_exe_id = 1
        job_input_dir = get_job_exe_input_data_dir(job_exe_id)

        job_interface.perform_pre_steps(job_data, job_environment, 1)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        expected_command_arguments = os.path.join(job_input_dir, 'files1')
        self.assertEqual(job_command_arguments, expected_command_arguments, u'expected a different command from pre_steps')
        mock_setup_upload.assert_called_once_with(get_job_exe_output_data_dir(job_exe_id), get_job_exe_output_work_dir(job_exe_id), self.workspace)

    def test_output_dir_in_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict[u'command_arguments'] = u'${job_output_dir}'

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = JobEnvironment(job_environment_dict)
        
        job_work_dir = "/test"
        job_exe_id = 1
        job_output_dir = get_job_exe_output_data_dir(job_exe_id)
        
        job_interface.perform_pre_steps(job_data, job_environment, 1)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, job_output_dir, u'expected a different command from pre_steps')

    def _get_simple_interface_data_env(self):
        job_interface_dict = {
            u'command': u'simple-command',
            u'command_arguments': u'',
            u'version': u'1.0'
        }

        job_data_dict = {
            u'version': u'1.0',
            u'input_data': [],
            u'output_data': [],
            u'shared_resources': []
        }

        job_environment_dict = {
            u'version': u'1.0',
            u'shared_resources': []
        }
        
        return job_interface_dict, job_data_dict, job_environment_dict


class TestJobInterfaceValidateConnection(TestCase):

    def setUp(self):
        django.setup()

    def test_successful(self):
        '''Tests calling JobInterface.validate_connection() successfully.'''
        job_interface_dict = {
            u'command': u'simple-command',
            u'command_arguments': u'',
            u'version': u'1.0',
            u'input_data': [{u'name': u'Input 1', u'type': u'property'},
                            {u'name': u'Input 2', u'type': u'file', u'media_types': [u'text/plain']}],
            u'output_data': [{u'name': u'Output 1', u'type': u'file'}]
        }

        job_interface = JobInterface(job_interface_dict)

        job_conn = JobConnection()
        job_conn.add_property(u'Input 1')
        job_conn.add_input_file(u'Input 2', False, [u'text/plain'], False)
        job_conn.add_workspace()
        
        # No exception is success
        job_interface.validate_connection(job_conn)

    def test_required_workspace_missing(self):
        '''Tests calling JobInterface.validate_connection() when a required workspace is missing'''
        job_interface_dict = {
            u'command': u'simple-command',
            u'command_arguments': u'',
            u'version': u'1.0',
            u'input_data': [{u'name': u'Input 1', u'type': u'property'},
                            {u'name': u'Input 2', u'type': u'file', u'media_types': [u'text/plain']}],
            u'output_data': [{u'name': u'Output 1', u'type': u'file'}]
        }

        job_interface = JobInterface(job_interface_dict)

        job_conn = JobConnection()
        job_conn.add_property(u'Input 1')
        job_conn.add_input_file(u'Input 2', False, [u'text/plain'], False)
        
        self.assertRaises(InvalidConnection, job_interface.validate_connection, job_conn)

    def test_no_workspace_needed(self):
        '''Tests calling JobInterface.validate_connection() without a workspace, but none is needed.'''
        job_interface_dict = {
            u'command': u'simple-command',
            u'command_arguments': u'',
            u'version': u'1.0',
            u'input_data': [{u'name': u'Input 1', u'type': u'property'},
                            {u'name': u'Input 2', u'type': u'file', u'media_types': [u'text/plain']}],
            u'output_data': []
        }

        job_interface = JobInterface(job_interface_dict)

        job_conn = JobConnection()
        job_conn.add_property(u'Input 1')
        job_conn.add_input_file(u'Input 2', False, [u'text/plain'], False)
        
        # No exception is success
        job_interface.validate_connection(job_conn)


class TestJobInterfaceValidation(TestCase):

    def setUp(self):
        django.setup()

    def test_minimal_input_validation(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'some_argument',
            u'version' : u'1.0'
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('A valid definition should not raise an Exception')

    def test_interface_must_have_command(self):
        definition = {
            u'version' : u'1.0'
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_command_string_allows_special_formats(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'${-f :param-1}',
            u'version' : u'1.0',
            u'input_data' : [
                {u'name' : u'param-1', u'type' : u'file'}
            ]
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

    def test_command_string_special_formats_should_have_dollar_sign(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'${param-1:-f param-1}',
            u'version' : u'1.0',
            u'input_data' : [
                {u'name' : u'param-1', u'type' : u'file'}
            ]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass
    def test_command_param_will_fail_without_input(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'${param-1}',
            u'version' : u'1.0'
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_command_param_will_pass_with_input(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'${param-1}',
            u'version' : u'1.0',
            u'input_data' : [{u'name' : u'param-1', u'type' : u'file'}]
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

    def test_input_data_names_must_be_unique(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'${param-1}',
            u'version' : u'1.0',
            u'input_data' : [
                {u'name' : u'param-1', u'type' : u'file'},
                {u'name' : u'param-1', u'type' : u'property'}
            ]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_data_must_have_a_name(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'${param-1}',
            u'version' : u'1.0',
            u'input_data' : [
                {u'type' : u'file'}
            ]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_data_must_have_a_type(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'${param-1}',
            u'version' : u'1.0',
            u'input_data' : [
                {u'name' : u'param-1'}
            ]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_data_must_be_an_approved_type(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'${param-1}',
            u'version' : u'1.0',
            u'input_data' : [
                {u'name' : u'param-1', u'type' : u'book'}
            ]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_data_required_must_be_true_or_false(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'${param-1}',
            u'version' : u'1.0',
            u'input_data' : [
                {u'name' : u'param-1', u'type' : u'file', 'required' : True}
            ]
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

        definition[u'input_data'][0][u'required'] = False
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

        definition[u'input_data'][0][u'required'] = u'some_string'
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_interface_with_share_resource_works(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'',
            u'version' : u'1.0',
            u'shared_resources' : [
                { u'name' : u'resource-1', u'type' : u'db-connection' }
            ]
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

    def test_share_resources_must_have_unque_names(self):
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'',
            u'version' : u'1.0',
            u'shared_resources' : [
                { u'name' : u'resource-1', u'type' : u'db-connection' },
                { u'name' : u'resource-1', u'type' : u'db-connection' }
            ]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_definition_with_unkown_field_fails(self):
        #This definition's shared resources attribute should be 'shared_resources' not 'shared-resources'
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'',
            u'version' : u'1.0',
            u'shared-resources' : [
                { u'name' : u'resource-1', u'type' : u'db-connection' }
            ]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_name_appropriate(self):
        good_names=[u'foo', u'bar', u'baz', u'a file with spaces', u'file_with_underscores']
        bad_names=[u'ca$h_money', u'do|do_not', 'try!=found',
'this_file_is_over_255_characters_long_12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890!']
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'',
            u'version' : u'1.0',
            u'input_data' : [
                {u'name' : u'foo', u'type' : u'file', 'required' : True}
            ],
            u'output_data': [{u'name': u'some_output', u'type': u'file'}]
        }
        for input_name in good_names:
            definition[u'input_data'][0][u'name']=input_name
            try:
                JobInterface(definition)
            except InvalidInterfaceDefinition:
                self.fail(u'Unable to parse a good interface definition with input name: %s' % input_name)
        for input_name in bad_names:
            definition[u'input_data'][0][u'name']=input_name
            try:
                JobInterface(definition)
                self.fail(u'job interface with a bad input name (%s) was able to get past validation' % input_name)
            except InvalidInterfaceDefinition:
                pass

    def test_output_name_appropriate(self):
        good_names=[u'foo', u'bar', u'baz', u'a file with spaces', u'file_with_underscores']
        bad_names=[u'ca$h_money', u'do|do_not', 'try!=found',
'this_file_is_over_255_characters_long_12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890!']
        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'',
            u'version' : u'1.0',
            u'input_data' : [
                {u'name' : u'foo', u'type' : u'file', 'required' : True}
            ],
            u'output_data': [{u'name': u'some_output', u'type': u'file'}]
        }

        for output_name in good_names:
            definition[u'output_data'][0][u'name']=output_name
            try:
                JobInterface(definition)
            except InvalidInterfaceDefinition:
                self.fail(u'Unable to parse a good interface definition with output name: %s' % output_name)
        for output_name in bad_names:
            definition[u'output_data'][0][u'name']=output_name
            try:
                JobInterface(definition)
                self.fail(u'job interface with a bad output name (%s) was able to get past validation' % output_name)
            except InvalidInterfaceDefinition:
                pass

    def test_bad_version(self):
        '''Tests calling JobInterface constructor with good and bad versions.  Versions longer than 50 should fail.'''

        definition = {
            u'command' : u'test-command',
            u'command_arguments' : u'',
            u'version' : u'BAD Version',
            u'input_data' : [
                {u'name' : u'foo', u'type' : u'file', 'required' : True}
            ],
            u'output_data': [{u'name': u'some_output', u'type': u'file'}]
        }

        self.assertRaises(InvalidInterfaceDefinition, JobInterface, definition)
