from __future__ import unicode_literals

import os

import django
from django.test import TestCase

from job.configuration.exceptions import InvalidExecutionConfiguration
from job.configuration.json.execution.exe_config import ExecutionConfiguration
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH
from job.test import utils as job_test_utils
from storage.test import utils as storage_test_utils


class TestExecutionConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        ExecutionConfiguration()

        # Invalid version
        config = {'version': 'BAD'}
        self.assertRaises(InvalidExecutionConfiguration, ExecutionConfiguration, config)

    def test_configure_for_queued_job(self):
        """Tests successfully calling configure_for_queued_job()"""

        file_1 = storage_test_utils.create_file()
        file_2 = storage_test_utils.create_file()
        file_3 = storage_test_utils.create_file()
        input_files = {file_1.id: file_1, file_2.id: file_2, file_3.id: file_3}
        data_dict = {'input_data': [{'name': 'input_1', 'value': 'my_val'}, {'name': 'input_2', 'file_id': file_1.id},
                                    {'name': 'input_3', 'file_ids': [file_2.id, file_3.id]}]}
        expected_env_vars = {'INPUT_1': 'my_val', 'INPUT_2': os.path.join(SCALE_JOB_EXE_INPUT_PATH,
                                                                          'input_2', file_1.file_name),
                             'INPUT_3': os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_3'),
                             'job_output_dir': SCALE_JOB_EXE_OUTPUT_PATH, 'OUTPUT_DIR': SCALE_JOB_EXE_OUTPUT_PATH}
        job = job_test_utils.create_job(data=data_dict, status='QUEUED')
        exe_config = ExecutionConfiguration()

        # Test method
        exe_config.configure_for_queued_job(job, input_files)

        config_dict = exe_config.get_dict()
        self.assertSetEqual(set(config_dict['input_files'].keys()), {'input_2', 'input_3'})
        self.assertEqual(len(config_dict['input_files']['input_2']), 1)
        self.assertEqual(len(config_dict['input_files']['input_3']), 2)
        self.assertEqual(len(config_dict['tasks']), 1)
        main_task = config_dict['tasks'][0]
        self.assertEqual(main_task['type'], 'main')
        self.assertEqual(main_task['args'], job.get_job_interface().get_command_args())
        self.assertDictEqual(main_task['env_vars'], expected_env_vars)


class TestExecutionConfigurationConvert(TestCase):
    """Tests performing conversion from lower to higher minor versions of configuration schema."""

    def setUp(self):
        django.setup()

    def test_convert_1_0_to_current(self):
        """Tests converting execution configuration 1.0 to current"""

        old_dict = {'version': '1.0', 'job_task': {'workspaces': [{'name': 'name1', 'mode': 'ro'}]}}
        exe_config = ExecutionConfiguration(old_dict)
        new_dict = exe_config.get_dict()
        self.assertEqual(new_dict['version'], '2.0')
        self.assertEqual(3, len(new_dict['tasks']))  # Version 1.0 will auto-create pre and post tasks
        self.assertEqual('main', new_dict['tasks'][1]['type'])

    def test_convert_1_1_to_current(self):
        """Tests converting execution configuration 1.1 to current"""

        old_dict = {'version': '1.1', 'job_task': {'settings': [{'name': 'setting_1', 'value': 'value_1'}],
                                                   'workspaces': [{'name': 'name1', 'mode': 'ro'}]}}
        exe_config = ExecutionConfiguration(old_dict)
        new_dict = exe_config.get_dict()
        self.assertEqual(new_dict['version'], '2.0')
        self.assertEqual(3, len(new_dict['tasks']))  # Version 1.1 will auto-create pre and post tasks
        self.assertEqual('main', new_dict['tasks'][1]['type'])
        self.assertEqual(1, len(new_dict['tasks'][1]['settings']))
        self.assertEqual('value_1', new_dict['tasks'][1]['settings']['setting_1'])
