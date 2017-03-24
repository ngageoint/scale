from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch, MagicMock

from job.configuration.execution.exceptions import InvalidExecutionConfiguration
from job.configuration.execution.json.exe_config import ExecutionConfiguration
from job.configuration.interface.job_interface import JobInterface
from job.configuration.job.json.job_config import JobConfiguration


class TestExecutionConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        ExecutionConfiguration()

        # Duplicate workspace name in pre-task
        config = {'pre_task': {'workspaces': [{'name': 'name1', 'mode': 'ro'}, {'name': 'name1', 'mode': 'ro'}]},
                  'job_task': {'workspaces': []}}
        self.assertRaises(InvalidExecutionConfiguration, ExecutionConfiguration, config)

        # Duplicate workspace name in job-task
        config = {'job_task': {'workspaces': [{'name': 'name1', 'mode': 'ro'}, {'name': 'name1', 'mode': 'ro'}]}}
        self.assertRaises(InvalidExecutionConfiguration, ExecutionConfiguration, config)

        # Duplicate workspace name in post-task
        config = {'post_task': {'workspaces': [{'name': 'name1', 'mode': 'ro'}, {'name': 'name1', 'mode': 'ro'}]},
                  'job_task': {'workspaces': []}}
        self.assertRaises(InvalidExecutionConfiguration, ExecutionConfiguration, config)

    def test_populate_default_job_settings(self):
        """Tests the addition of default settings to the configuration."""

        exe_config = ExecutionConfiguration()

        config_dict = {
            'version': '1.0',
            'default_settings': {
                'setting_name': 'some_val',
                'setting2': 'other_val'
            }
        }

        interface_dict = {
            'version': '1.4',
            'command': 'the cmd',
            'command_arguments': 'foo',
            'settings': [{'name': 'setting_name'}, {'name': 'setting2'}]
        }

        job_exe = MagicMock()
        job_exe.get_job_configuration.return_value = JobConfiguration(config_dict)
        job_exe.get_job_interface.return_value = JobInterface(interface_dict)

        exe_config.populate_default_job_settings(job_exe)

        populated_config = exe_config.get_dict()
        populated_settings = populated_config['job_task']['settings']

        populated_setting_values = [x.values() for x in populated_settings]
        results_dict = {x[0]: x[1] for x in populated_setting_values}

        self.assertDictEqual(results_dict, config_dict['settings'])

    def test_populate_mounts(self):
        """Tests the addition of mount volumes to the configuration."""

        exe_config = ExecutionConfiguration()

        config_dict = {
            'version': '2.0',
            'mounts': {
                'mount_1': {'type': 'host', 'host_path': '/host/path'},
                'mount_2': {'type': 'volume', 'driver': 'x-driver', 'driver_opts': {'foo': 'bar'}}
            }
        }

        interface_dict = {
            'version': '1.4',
            'command': 'the cmd',
            'command_arguments': 'foo',
            'mounts': [{'name': 'mount_1', 'path': '/mount_1', 'mode': 'ro'},
                       {'name': 'mount_2', 'path': '/mount_2', 'mode': 'rw'}]
        }

        job_exe = MagicMock()
        job_exe.get_job_configuration.return_value = JobConfiguration(config_dict)
        job_exe.get_job_interface.return_value = JobInterface(interface_dict)
        job_exe.get_cluster_id.return_value = 'scale_1234'

        exe_config.populate_mounts(job_exe)

        docker_params = exe_config.get_job_task_docker_params()
        self.assertEqual(docker_params[0].flag, 'volume')
        self.assertEqual(docker_params[0].value, '/host/path:/mount_1:ro')
        self.assertEqual(docker_params[1].flag, 'volume')
        mount_2 = '$(docker volume create --name scale_1234_mount_mount_2 --driver x-driver --opt foo=bar):/mount_2:rw'
        self.assertEqual(docker_params[1].value, mount_2)


class TestExecutionConfigurationConvert(TestCase):
    """Tests performing conversion from lower to higher minor versions of configuration schema."""

    def setUp(self):
        self.job_configuration_dict = {
            'version': '1.0',
            'job_task': {
                'workspaces': [{
                    'name': 'name1',
                    'mode': 'ro'
                    }]
                }
            }

        django.setup()

    @patch('job.configuration.execution.json.exe_config_1_0.ExecutionConfiguration.get_dict')
    def test_successful(self, mock_get_dict):
        """Tests calling ExecutionConfiguration.convert_configuration() successfully."""
        mock_get_dict.return_value = self.job_configuration_dict
        job_configuration = ExecutionConfiguration.convert_configuration(self.job_configuration_dict)
        self.assertEqual(job_configuration['version'], '1.1')
        self.assertFalse(job_configuration['job_task']['settings'])
