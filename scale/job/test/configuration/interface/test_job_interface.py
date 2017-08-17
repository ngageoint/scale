from __future__ import unicode_literals

import os

import django
from django.test import TestCase
from mock import patch, MagicMock, Mock

import job.test.utils as job_test_utils
import storage.test.utils as storage_test_utils
from job.configuration.data.exceptions import InvalidConnection, InvalidData
from job.configuration.data.job_connection import JobConnection
from job.configuration.data.job_data import JobData
from job.configuration.interface.exceptions import InvalidInterfaceDefinition
from job.configuration.interface.job_interface import JobInterface
from job.configuration.exceptions import MissingSetting
from job.configuration.json.execution.exe_config import ExecutionConfiguration
from job.configuration.results.exceptions import InvalidResultsManifest
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH


class TestJobInterfaceAddOutputToConnection(TestCase):
    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests calling JobInterface.add_output_to_connection() successfully."""
        job_interface_dict = {
            'command': 'simple-command',
            'command_arguments': '',
            'version': '1.0',
            'input_data': [],
            'output_data': [{
                'name': 'Output 1',
                'type': 'file',
            }]
        }

        job_interface = JobInterface(job_interface_dict)
        job_conn = MagicMock()

        job_interface.add_output_to_connection('Output 1', job_conn, 'Input 1')
        job_conn.add_input_file.assert_called_with('Input 1', False, [], False, False)


class TestJobInterfaceConvert(TestCase):
    """Tests performing conversion from lower to higher minor versions of interface schema."""

    def setUp(self):
        self.job_interface_dict = {
            'command': 'simple-command',
            'command_arguments': '',
            'version': '1.0',
            'input_data': [
                {
                    'name': 'Input 1',
                    'type': 'file'
                },
                {
                    'name': 'Input 2',
                    'type': 'property'
                }
            ],
            'output_data': []
        }

        django.setup()

    @patch('job.configuration.interface.job_interface_1_0.JobInterface.get_dict')
    def test_successful(self, mock_get_dict):
        """Tests calling JobInterface.update() successfully."""
        mock_get_dict.return_value = self.job_interface_dict
        job_interface = JobInterface.convert_interface(self.job_interface_dict)
        self.assertEqual(job_interface['version'], '1.4')
        self.assertIn('partial', job_interface['input_data'][0])
        self.assertFalse(job_interface['input_data'][0]['partial'])
        self.assertFalse(job_interface['env_vars'])
        self.assertFalse(job_interface['settings'])


class TestJobInterfacePostSteps(TestCase):
    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.file = storage_test_utils.create_file(workspace=self.workspace)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_output_file(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['output_data'] = [{
            'name': 'output_file',
            'type': 'file',
            'required': True,
        }]
        job_data_dict['output_data'].append({
            'name': 'output_file',
            'workspace_id': self.workspace.id,
        })
        results_manifest = {
            'version': '1.0',
            'files': [{
                'name': 'output_file',
                'path': '/some/path/foo.txt',
            }]
        }
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = ''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({
            'output_file': ('/some/path/foo.txt', None),
        }, job_exe)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_invalid_output_file(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['output_data'] = [{
            'name': 'output_file',
            'type': 'file',
            'required': True,
        }]
        job_data_dict['output_data'].append({
            'name': 'output_file',
            'workspace_id': self.workspace.id,
        })
        results_manifest = {
            'version': '1.0',
            'files': [{
                'name': 'output_file',
                'path': '/some/path/foo.txt',
            }]
        }
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = False

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = ''

        self.assertRaises(InvalidResultsManifest, job_interface.perform_post_steps, job_exe, job_data, fake_stdout)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_output_files(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['output_data'] = [{
            'name': 'output_files',
            'type': 'files',
            'required': True,
        }]
        job_data_dict['output_data'].append({
            'name': 'output_files',
            'workspace_id': self.workspace.id,
        })
        results_manifest = {
            'version': '1.0',
            'files': [{
                'name': 'output_files',
                'paths': ['/some/path/foo.txt', '/other/path/foo.txt'],
            }]
        }
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = ''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({
            'output_files': [
                ('/some/path/foo.txt', None),
                ('/other/path/foo.txt', None),
            ]
        }, job_exe)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_invalid_output_files(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['output_data'] = [{
            'name': 'output_files',
            'type': 'files',
            'required': True,
        }]
        job_data_dict['output_data'].append({
            'name': 'output_files',
            'workspace_id': self.workspace.id,
        })
        results_manifest = {
            'version': '1.0',
            'files': [{
                'name': 'output_files',
                'paths': ['/some/path/foo.txt', '/other/path/foo.txt'],
            }]
        }
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = False

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = ''

        self.assertRaises(InvalidResultsManifest, job_interface.perform_post_steps, job_exe, job_data, fake_stdout)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_output_file_with_geo_metadata(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['output_data'] = [{
            'name': 'output_file',
            'type': 'file',
            'required': True,
        }]
        job_data_dict['output_data'].append({
            'name': 'output_file',
            'workspace_id': self.workspace.id,
        })
        geo_metadata = {
            'data_started': '2015-05-15T10:34:12Z',
            'data_ended': '2015-05-15T10:36:12Z',
            'geo_json': {
                'type': 'Polygon',
                'coordinates': [[[1.0, 10.0], [2.0, 10.0], [2.0, 20.0], [1.0, 20.0], [1.0, 10.0]]],
            }
        }
        results_manifest = {
            'version': '1.1',
            'output_data': [{
                'name': 'output_file',
                'file': {
                    'path': '/some/path/foo.txt',
                    'geo_metadata': geo_metadata,
                }
            }]
        }
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = ''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({
            'output_file': ('/some/path/foo.txt', None, geo_metadata),
        }, job_exe)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_output_files_with_geo_metadata(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['output_data'] = [{
            'name': 'output_files',
            'type': 'files',
            'required': True,
        }]
        job_data_dict['output_data'].append({
            'name': 'output_files',
            'workspace_id': self.workspace.id,
        })
        geo_metadata = {
            'data_started': '2015-05-15T10:34:12Z',
            'data_ended': '2015-05-15T10:36:12Z',
            'geo_json': {
                'type': 'Polygon',
                'coordinates': [[[1.0, 10.0], [2.0, 10.0], [2.0, 20.0], [1.0, 20.0], [1.0, 10.0]]],
            }
        }
        results_manifest = {
            'version': '1.1',
            'output_data': [{
                'name': 'output_files',
                'files': [{
                    'path': '/some/path/foo.txt',
                    'geo_metadata': geo_metadata,
                }, {
                    'path': '/other/path/foo.txt',
                    'geo_metadata': geo_metadata,
                }]
            }]
        }

        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = ''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({
            'output_files': [
                ('/some/path/foo.txt', None, geo_metadata),
                ('/other/path/foo.txt', None, geo_metadata),
            ]
        }, job_exe)

    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_parse_data(self, mock_loads, mock_open, mock_exists):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'required': True,
        }]
        job_data_dict['input_data'].append({
            'name': 'input_file',
            'file_id': self.file.id,
        })
        geo_json = {'type': 'Feature'}
        geo_metadata = {
            'data_started': '2015-01-01T00:00:00Z',
            'geo_json': geo_json
        }
        results_manifest = {
            'version': '1.1',
            'parse_results': [{
                'filename': '/some/path/foo.txt',
                'geo_metadata': geo_metadata,
            }]
        }
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = ''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.save_parse_results.assert_called_with({
            '/some/path/foo.txt': (geo_json, '2015-01-01T00:00:00Z', None, [], None),
        })

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_parse_stdout(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'required': True,
        }]
        job_interface_dict['output_data'] = [{
            'name': 'output_file',
            'type': 'file',
            'required': True,
        }, {
            'name': 'output_file_2',
            'type': 'file',
            'required': True,
        }]
        job_data_dict['input_data'].append({
            'name': 'input_file',
            'file_id': self.file.id,
        })
        results_manifest = {}
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = """
This text is supposed to mimic the output
of a program we should see artifacts registered with
the format: ARTIFACT:<input-name>:path, but it needs be at the beginning of a line
so the example above won't match, but this will
ARTIFACT:output_file:/path/to/foo.txt
We should also be able to have text after the artifact and multiple artifacts.
ARTIFACT:output_file_2:/path/to/foo_2.txt
"""

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({
            'output_file': ('/path/to/foo.txt', None),
            'output_file_2': ('/path/to/foo_2.txt', None),
        }, job_exe)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_parse_stdout_required(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'required': True,
        }]
        job_interface_dict['output_data'] = [{
            'name': 'output_file',
            'type': 'file',
            'required': True,
        }]
        job_data_dict['input_data'].append({
            'name': 'input_file',
            'file_id': self.file.id,
        })
        results_manifest = {}
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = """
This text is supposed to mimic the output
of a program we should see artifacts registered with
the format: ARTIFACT:<input-name>:path, but it needs be at the beginning of a line
so the example above won't match, but this will
ARTIFACT:output_file:/path/to/foo.txt
"""

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({
            'output_file': ('/path/to/foo.txt', None),
        }, job_exe)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_manifest_overrides_stdout(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'required': True,
        }]
        job_interface_dict['output_data'] = [{
            'name': 'output_file',
            'type': 'file',
            'required': True,
        }, {
            'name': 'output_file_2',
            'type': 'file',
            'required': True,
        }]
        job_data_dict['input_data'].append({
            'name': 'input_file',
            'file_id': self.file.id,
        })
        results_manifest = {
            'version': '1.0',
            'files': [{
                'name': 'output_file',
                'path': '/new/path/foo.txt',
            }]
        }
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = """
This text is supposed to mimic the output
of a program we should see artifacts registered with
the format: ARTIFACT:<input-name>:path, but it needs be at the beginning of a line
so the example above won't match, but this will
ARTIFACT:output_file:/path/to/foo.txt
We should also be able to have text after the artifact and multiple artifacts.
ARTIFACT:output_file_2:/path/to/foo_2.txt
"""

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({
            'output_file': ('/new/path/foo.txt', None),
            'output_file_2': ('/path/to/foo_2.txt', None),
        }, job_exe)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_extra_products_are_fine(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'required': True,
        }]
        job_interface_dict['output_data'] = [{
            'name': 'output_file',
            'type': 'file',
            'required': True,
        }]
        job_data_dict['input_data'].append({
            'name': 'input_file',
            'file_id': self.file.id,
        })
        results_manifest = {
            'version': '1.0',
            'files': [{
                'name': 'output_file',
                'path': '/new/path/foo.txt',
            }]
        }
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = """
This text is supposed to mimic the output
of a program we should see artifacts registered with
the format: ARTIFACT:<input-name>:path, but it needs be at the beginning of a line
so the example above won't match, but this will
ARTIFACT:output_file:/path/to/foo.txt
We should also be able to have text after the artifact and multiple artifacts.
ARTIFACT:output_file_2:/path/to/foo_2.txt
"""

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({
            'output_file': ('/new/path/foo.txt', None),
        }, job_exe)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('__builtin__.open')
    @patch('job.configuration.interface.job_interface_1_0.json.loads')
    def test_output_data_media_types(self, mock_loads, mock_open, mock_exists, mock_isfile):
        job_interface_dict, job_data_dict = self._get_simple_interface_data()
        job_interface_dict['output_data'] = [{
            'name': 'output_file',
            'type': 'file',
            'required': True,
            'media_type': 'text/x-some-weird-type',
        }]
        job_data_dict['output_data'].append({
            'name': 'output_file',
            'workspace_id': self.workspace.id,
        })
        results_manifest = {
            'version': '1.0',
            'files': [{
                'name': 'output_file',
                'path': '/some/path/foo.txt',
            }]
        }
        mock_loads.return_value = results_manifest
        mock_exists.return_value = True
        mock_isfile.return_value = True

        job_exe = MagicMock()

        job_interface = JobInterface(job_interface_dict)
        job_data = Mock(spec=JobData)
        job_data.save_parse_results = Mock()
        fake_stdout = ''

        job_interface.perform_post_steps(job_exe, job_data, fake_stdout)
        job_data.store_output_data_files.assert_called_with({
            'output_file': ('/some/path/foo.txt', 'text/x-some-weird-type'),
        }, job_exe)

    def _get_simple_interface_data(self):
        job_interface_dict = {
            'command': 'simple-command',
            'command_arguments': '',
            'version': '1.0',
        }

        job_data_dict = {
            'version': '1.0',
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }

        return job_interface_dict, job_data_dict


class TestJobInterfacePreSteps(TestCase):
    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.file = storage_test_utils.create_file(workspace=self.workspace)

    def test_simple_case(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict
        job_exe_id = 1

        job_interface.perform_pre_steps(job_data, job_environment)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, '', 'expected a different command from pre_steps')

    def test_property_in_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict['command_arguments'] = '${prop1}'
        job_interface_dict['input_data'] = [{
            'name': 'prop1',
            'type': 'property',
            'required': True,
        }]
        job_data_dict['input_data'].append({
            'name': 'prop1',
            'value': 'property-value',
        })

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict
        job_exe_id = 1

        job_interface.perform_pre_steps(job_data, job_environment)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, 'property-value', 'expected a different command from pre_steps')

    def test_complex_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict['command_arguments'] = '${-f :prop1}'
        job_interface_dict['input_data'] = [{
            'name': 'prop1',
            'type': 'property',
            'required': True,
        }]
        job_data_dict['input_data'].append({
            'name': 'prop1',
            'value': 'property-value',
        })

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict
        job_exe_id = 1

        job_interface.perform_pre_steps(job_data, job_environment)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, '-f property-value', 'expected a different command from pre_steps')

    @patch('os.path.isdir')
    @patch('job.configuration.interface.job_interface.JobInterface._get_one_file_from_directory')
    @patch('os.mkdir')
    @patch('job.configuration.data.job_data.JobData.retrieve_input_data_files')
    def test_file_in_command(self, mock_retrieve_call, mock_os_mkdir, mock_get_one_file, mock_isdir):
        job_exe_id = 1

        def new_retrieve(arg1):
            return {
                'file1_out': [input_file_path],
            }

        input_file_path = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'file1', 'foo.txt')
        mock_retrieve_call.side_effect = new_retrieve
        mock_get_one_file.side_effect = lambda (arg1): input_file_path
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict['command_arguments'] = '${file1}'
        job_interface_dict['input_data'] = [{
            'name': 'file1',
            'type': 'file',
            'required': True,
        }]
        job_data_dict['input_data'].append({
            'name': 'file1',
            'file_id': self.file.id,
        })
        job_data_dict['output_data'].append({
            'name': 'file1_out',
            'workspace_id': self.workspace.id,
        })

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict

        job_interface.perform_pre_steps(job_data, job_environment)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, input_file_path, 'expected a different command from pre_steps')

    @patch('os.path.isdir')
    @patch('os.mkdir')
    @patch('job.configuration.data.job_data.JobData.retrieve_input_data_files')
    def test_files_in_command(self, mock_retrieve_call, mock_os_mkdir, mock_isdir):
        def new_retrieve(arg1):
            return {
                'files1_out': ['/test/file1/foo.txt', '/test/file1/bar.txt'],
            }

        mock_retrieve_call.side_effect = new_retrieve
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict['command_arguments'] = '${files1}'
        job_interface_dict['input_data'] = [{
            'name': 'files1',
            'type': 'files',
            'required': True,
        }]
        job_data_dict['input_data'].append({
            'name': 'files1',
            'file_ids': [1, 2, 3],
        })
        job_data_dict['output_data'].append({
            'name': 'files1_out',
            'workspace_id': self.workspace.id,
        })

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict
        job_exe_id = 1

        job_interface.perform_pre_steps(job_data, job_environment)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        expected_command_arguments = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'files1')
        self.assertEqual(job_command_arguments, expected_command_arguments,
                         'expected a different command from pre_steps')

    def test_output_dir_in_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict['command_arguments'] = '${job_output_dir}'

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict
        job_exe_id = 1
        job_output_dir = SCALE_JOB_EXE_OUTPUT_PATH

        job_interface.perform_pre_steps(job_data, job_environment)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, job_output_dir, 'expected a different command from pre_steps')

    def test_absent_required_file_in_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict['command_arguments'] = '${input_file}'

        job_interface_dict['input_data'] = [{
            'name': 'input_file',
            'type': 'file',
            'required': True,
        }]

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict
        job_exe_id = 1

        job_interface.perform_pre_steps(job_data, job_environment)
        self.assertRaises(InvalidData, lambda: job_interface.fully_populate_command_argument(job_data,
                                                                                             job_environment,
                                                                                             job_exe_id))

    def test_absent_optional_file_in_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict['command_arguments'] = '${input_file}'

        job_interface_dict['input_data'] = [{
            'name': 'input_file',
            'type': 'files',
            'required': False,
        }]

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict
        job_exe_id = 1

        job_interface.perform_pre_steps(job_data, job_environment)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, '', 'expected a different command from pre_steps')

    def test_absent_required_files_in_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict['command_arguments'] = '${input_files}'

        job_interface_dict['input_data'] = [{
            'name': 'input_files',
            'type': 'files',
            'required': True,
        }]

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict
        job_exe_id = 1

        job_interface.perform_pre_steps(job_data, job_environment)
        self.assertRaises(InvalidData, lambda: job_interface.fully_populate_command_argument(job_data,
                                                                                             job_environment,
                                                                                             job_exe_id))

    def test_absent_optional_files_in_command(self):
        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()
        job_interface_dict['command_arguments'] = '${input_files}'

        job_interface_dict['input_data'] = [{
            'name': 'input_files',
            'type': 'files',
            'required': False,
        }]

        job_interface = JobInterface(job_interface_dict)
        job_data = JobData(job_data_dict)
        job_environment = job_environment_dict
        job_exe_id = 1

        job_interface.perform_pre_steps(job_data, job_environment)
        job_command_arguments = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)
        self.assertEqual(job_command_arguments, '', 'expected a different command from pre_steps')

    def _get_simple_interface_data_env(self):
        job_interface_dict = {
            'command': 'simple-command',
            'command_arguments': '',
            'version': '1.0',
        }

        job_data_dict = {
            'version': '1.0',
            'input_data': [],
            'output_data': [],
            'shared_resources': [],
        }

        job_environment_dict = {
            'version': '1.0',
            'shared_resources': [],
        }

        return job_interface_dict, job_data_dict, job_environment_dict

    @patch('scheduler.vault.manager.SecretsManager.retrieve_job_type_secrets')
    def test_validate_populated_settings(self, mock_secrets_mgr):
        """Tests the validation of required settings defined in the job_interface"""

        mock_secrets_mgr.return_value = {
            'setting1': 'secret_val'
        }

        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()

        job_interface_dict['command_arguments'] = '${setting1}'
        job_interface_dict['version'] = '1.3'
        job_interface_dict['env_vars'] = [{
            'name': 'test_var',
            'value': '${setting2}',
        }]

        job_interface_dict['settings'] = [{
            'name': 'setting1',
            'required': True,
            'secret': True,
        }, {
            'name': 'setting2',
            'required': True,
        }]

        job_config_json = {'version': '1.1', 'job_task': {'settings': [{'name': 'setting2',
                                                                        'value': 'another_setting'}]}}

        job_interface = JobInterface(job_interface_dict)
        job_config = ExecutionConfiguration(job_config_json)

        job_type = job_test_utils.create_job_type(interface=job_interface_dict)

        job_interface.populate_command_argument_settings(job_interface_dict['command_arguments'], job_config, job_type)

        try:
            # Validate acceptable job_interface and job_configuration
            job_interface.validate_populated_settings(job_config)
        except MissingSetting:
            self.fail('Valid job_interface settings definition should not raise an Exception')

    def test_validate_populated_settings_no_cmd_args(self):
        """Tests the validation of required settings defined in the job_interface"""

        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()

        job_interface_dict['command_arguments'] = ''
        job_interface_dict['version'] = '1.2'
        job_interface_dict['env_vars'] = [{
            'name': 'test_var',
            'value': '${setting2}',
        }]

        job_interface_dict['settings'] = [{
            'name': 'setting1',
            'required': True,
        }, {
            'name': 'setting2',
            'required': True,
        }]

        job_config_json = {'version': '1.1', 'job_task': {'settings': [{'name': 'setting1', 'value': 'test_setting'}]}}

        job_interface = JobInterface(job_interface_dict)
        job_config = ExecutionConfiguration(job_config_json)

        job_exe = MagicMock()
        job_exe.command_arguments = ''

        self.assertRaises(MissingSetting, job_interface.validate_populated_settings, job_config)

    def test_validate_populated_settings_no_env_vars(self):
        """Tests the validation of required settings defined in the job_interface"""

        job_interface_dict, job_data_dict, job_environment_dict = self._get_simple_interface_data_env()

        job_interface_dict['command_arguments'] = '${setting1}'
        job_interface_dict['version'] = '1.2'
        job_interface_dict['env_vars'] = []
        job_interface_dict['settings'] = [{
            'name': 'setting1',
            'required': True,
        }, {
            'name': 'setting2',
            'required': True,
        }]

        job_config_json = {'version': '1.1', 'job_task': {'settings': [{'name': 'setting2',
                                                                        'value': 'another_setting'}]}}

        job_interface = JobInterface(job_interface_dict)
        job_config = ExecutionConfiguration(job_config_json)

        job_exe = MagicMock()
        job_exe.command_arguments = 'test_setting'

        self.assertRaises(MissingSetting, job_interface.validate_populated_settings, job_config)


class TestJobInterfaceValidateConnection(TestCase):
    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests calling JobInterface.validate_connection() successfully."""
        job_interface_dict = {
            'command': 'simple-command',
            'command_arguments': '',
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'type': 'property',
            }, {
                'name': 'Input 2',
                'type': 'file',
                'media_types': ['text/plain']
            }],
            'output_data': [{
                'name': 'Output 1',
                'type': 'file',
            }]
        }

        job_interface = JobInterface(job_interface_dict)

        job_conn = JobConnection()
        job_conn.add_property('Input 1')
        job_conn.add_input_file('Input 2', False, ['text/plain'], False, False)
        job_conn.add_workspace()

        # No exception is success
        job_interface.validate_connection(job_conn)

    def test_required_workspace_missing(self):
        """Tests calling JobInterface.validate_connection() when a required workspace is missing"""
        job_interface_dict = {
            'command': 'simple-command',
            'command_arguments': '',
            'version': '1.1',
            'input_data': [{
                'name': 'Input 1',
                'type': 'property',
            }, {
                'name': 'Input 2',
                'type': 'file',
                'media_types': ['text/plain'],
                'partial': True
            }],
            'output_data': [{
                'name': 'Output 1',
                'type': 'file',
            }]
        }

        job_interface = JobInterface(job_interface_dict)

        job_conn = JobConnection()
        job_conn.add_property('Input 1')
        job_conn.add_input_file('Input 2', False, ['text/plain'], False, True)

        self.assertRaises(InvalidConnection, job_interface.validate_connection, job_conn)

    def test_no_workspace_needed(self):
        """Tests calling JobInterface.validate_connection() without a workspace, but none is needed."""
        job_interface_dict = {
            'command': 'simple-command',
            'command_arguments': '',
            'version': '1.1',
            'input_data': [{
                'name': 'Input 1',
                'type': 'property',
            }, {
                'name': 'Input 2',
                'type': 'file',
                'media_types': ['text/plain'],
                'partial': True
            }],
            'output_data': [],
        }

        job_interface = JobInterface(job_interface_dict)

        job_conn = JobConnection()
        job_conn.add_property('Input 1')
        job_conn.add_input_file('Input 2', False, ['text/plain'], False, True)

        # No exception is success
        job_interface.validate_connection(job_conn)


class TestJobInterfaceValidation(TestCase):
    def setUp(self):
        django.setup()

    def test_minimal_input_validation(self):
        definition = {
            'command': 'test-command',
            'command_arguments': 'some_argument',
            'version': '1.0',
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('A valid definition should not raise an Exception')

    def test_interface_must_have_command(self):
        definition = {
            'version': '1.0',
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_command_string_allows_special_formats(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${-f :param-1}',
            'version': '1.0',
            'input_data': [{
                'name': 'param-1',
                'type': 'file',
            }]
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

    def test_command_string_special_formats_should_have_dollar_sign(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${param-1:-f param-1}',
            'version': '1.0',
            'input_data': [{
                'name': 'param-1',
                'type': 'file',
            }]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_command_param_will_fail_without_input(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${param-1}',
            'version': '1.0',
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_command_param_will_pass_with_input(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${param-1}',
            'version': '1.0',
            'input_data': [{
                'name': 'param-1',
                'type': 'file',
            }]
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

    def test_input_data_names_must_be_unique(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${param-1}',
            'version': '1.0',
            'input_data': [{
                'name': 'param-1',
                'type': 'file',
            }, {
                'name': 'param-1',
                'type': 'property',
            }]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_data_must_have_a_name(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${param-1}',
            'version': '1.0',
            'input_data': [{
                'type': 'file',
            }]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_data_must_have_a_type(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${param-1}',
            'version': '1.0',
            'input_data': [{
                'name': 'param-1',
            }]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_data_must_be_an_approved_type(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${param-1}',
            'version': '1.0',
            'input_data': [{
                'name': 'param-1',
                'type': 'book',
            }]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_data_required_must_be_true_or_false(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${param-1}',
            'version': '1.0',
            'input_data': [{
                'name': 'param-1',
                'type': 'file',
                'required': True,
            }]
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

        definition['input_data'][0]['required'] = False
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

        definition['input_data'][0]['required'] = 'some_string'
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_interface_with_share_resource_works(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '',
            'version': '1.0',
            'shared_resources': [{
                'name': 'resource-1',
                'type': 'db-connection',
            }]
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

    def test_share_resources_must_have_unque_names(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '',
            'version': '1.0',
            'shared_resources': [{
                'name': 'resource-1',
                'type': 'db-connection',
            }, {
                'name': 'resource-1',
                'type': 'db-connection',
            }]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_definition_with_unkown_field_fails(self):
        # This definition's shared resources attribute should be 'shared_resources' not 'shared-resources'
        definition = {
            'command': 'test-command',
            'command_arguments': '',
            'version': '1.0',
            'shared-resources': [{
                'name': 'resource-1',
                'type': 'db-connection',
            }]
        }
        try:
            JobInterface(definition)
            self.fail('Expected invalid job definition to throw an exception')
        except InvalidInterfaceDefinition:
            pass

    def test_input_name_appropriate(self):
        good_names = ['foo', 'bar', 'baz', 'a file with spaces', 'file_with_underscores']
        bad_names = [
            'ca$h_money',
            'do|do_not',
            'try!=found',
            'this_file_is_over_255_characters_long_12345678901234567890123456789012345678901234567890123456789012345678'
            '9012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234'
            '56789012345678901234567890123456789012345678901234567890!'
        ]
        definition = {
            'command': 'test-command',
            'command_arguments': '',
            'version': '1.0',
            'input_data': [{
                'name': 'foo',
                'type': 'file',
                'required': True,
            }],
            'output_data': [{
                'name': 'some_output',
                'type': 'file',
            }]
        }
        for input_name in good_names:
            definition['input_data'][0]['name'] = input_name
            try:
                JobInterface(definition)
            except InvalidInterfaceDefinition:
                self.fail('Unable to parse a good interface definition with input name: %s' % input_name)
        for input_name in bad_names:
            definition['input_data'][0]['name'] = input_name
            try:
                JobInterface(definition)
                self.fail('job interface with a bad input name (%s) was able to get past validation' % input_name)
            except InvalidInterfaceDefinition:
                pass

    def test_output_name_appropriate(self):
        good_names = ['foo', 'bar', 'baz', 'a file with spaces', 'file_with_underscores']
        bad_names = [
            'ca$h_money',
            'do|do_not',
            'try!=found',
            'this_file_is_over_255_characters_long_12345678901234567890123456789012345678901234567890123456789012345678'
            '9012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234'
            '56789012345678901234567890123456789012345678901234567890!'
        ]
        definition = {
            'command': 'test-command',
            'command_arguments': '',
            'version': '1.0',
            'input_data': [{
                'name': 'foo',
                'type': 'file',
                'required': True,
            }],
            'output_data': [{
                'name': 'some_output',
                'type': 'file',
            }]
        }

        for output_name in good_names:
            definition['output_data'][0]['name'] = output_name
            try:
                JobInterface(definition)
            except InvalidInterfaceDefinition:
                self.fail('Unable to parse a good interface definition with output name: %s' % output_name)
        for output_name in bad_names:
            definition['output_data'][0]['name'] = output_name
            try:
                JobInterface(definition)
                self.fail('job interface with a bad output name (%s) was able to get past validation' % output_name)
            except InvalidInterfaceDefinition:
                pass

    def test_bad_version(self):
        """Tests calling JobInterface constructor with good and bad versions.  Versions longer than 50 should fail."""

        definition = {
            'command': 'test-command',
            'command_arguments': '',
            'version': 'BAD Version',
            'input_data': [{
                'name': 'foo',
                'type': 'file',
                'required': True,
            }],
            'output_data': [{
                'name': 'some_output',
                'type': 'file',
            }]
        }

        self.assertRaises(InvalidInterfaceDefinition, JobInterface, definition)

    def test_settings_required(self):
        definition = {
            'command': 'test-command',
            'command_arguments': '${setting-1}',
            'version': '1.2',
            'settings': [{
                'name': 'setting-1',
                'required': True
            }]
        }
        try:
            JobInterface(definition)
        except InvalidInterfaceDefinition:
            self.fail('Valid definition raised a validation exception')

        definition['settings'][0]['name'] = 'not-setting-1'
        self.assertRaises(InvalidInterfaceDefinition, JobInterface, definition)

        definition['settings'][0]['required'] = 'some_string'
        self.assertRaises(InvalidInterfaceDefinition, JobInterface, definition)
