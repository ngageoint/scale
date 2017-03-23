from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch, MagicMock

from job.configuration.execution.exceptions import InvalidExecutionConfiguration
from job.configuration.execution.json.exe_config import ExecutionConfiguration
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

        job_config = ExecutionConfiguration()

        config_dict = {
            'version': '1.0',
            'default_settings': {
                'setting_name': 'some_val',
                'setting2': 'other_val'
            }
        }

        job_exe = MagicMock()
        job_exe.get_job_configuration.return_value = JobConfiguration(config_dict)

        job_config.populate_default_job_settings(job_exe)

        populated_config = job_config.get_dict()
        populated_settings = populated_config['job_task']['settings']

        populated_setting_values = [x.values() for x in populated_settings]
        results_dict = {x[0]: x[1] for x in populated_setting_values}

        self.assertTrue(results_dict == config_dict['settings'])


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
