from __future__ import unicode_literals

import os

import django
from django.test import TestCase

from job.configuration.configurators import QueuedExecutionConfigurator
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH
from job.test import utils as job_test_utils
from storage.test import utils as storage_test_utils


class TestQueuedExecutionConfigurator(TestCase):

    def setUp(self):
        django.setup()

    def test_configure_queued_job_regular(self):
        """Tests successfully calling configure_queued_job() on a regular (non-system) job"""

        file_1 = storage_test_utils.create_file()
        file_2 = storage_test_utils.create_file()
        file_3 = storage_test_utils.create_file()
        input_files = {file_1.id: file_1, file_2.id: file_2, file_3.id: file_3}
        interface_dict = {'version': '1.4', 'command': 'foo',
                          'command_arguments': '${a:input_1} ${b:input_2} ${input_3} ${job_output_dir}',
                          'input_data': [{'name': 'input_1', 'type': 'property'}, {'name': 'input_2', 'type': 'file'},
                                         {'name': 'input_3', 'type': 'files'}]}
        data_dict = {'input_data': [{'name': 'input_1', 'value': 'my_val'}, {'name': 'input_2', 'file_id': file_1.id},
                                    {'name': 'input_3', 'file_ids': [file_2.id, file_3.id]}]}
        input_2_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_2', file_1.file_name)
        input_3_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_3')
        expected_args = '-a my_val -b %s %s ${job_output_dir}' % (input_2_val, input_3_val)
        expected_env_vars = {'INPUT_1': 'my_val', 'INPUT_2': input_2_val, 'INPUT_3': input_3_val,
                             'job_output_dir': SCALE_JOB_EXE_OUTPUT_PATH, 'OUTPUT_DIR': SCALE_JOB_EXE_OUTPUT_PATH}
        job_type = job_test_utils.create_job_type(interface=interface_dict)
        job = job_test_utils.create_job(job_type=job_type, data=data_dict, status='QUEUED')
        configurator = QueuedExecutionConfigurator(input_files)

        # Test method
        exe_config = configurator.configure_queued_job(job)

        config_dict = exe_config.get_dict()
        self.assertSetEqual(set(config_dict['input_files'].keys()), {'input_2', 'input_3'})
        self.assertEqual(len(config_dict['input_files']['input_2']), 1)
        self.assertEqual(len(config_dict['input_files']['input_3']), 2)
        self.assertEqual(len(config_dict['tasks']), 1)
        main_task = config_dict['tasks'][0]
        self.assertEqual(main_task['type'], 'main')
        self.assertEqual(main_task['args'], expected_args)
        self.assertDictEqual(main_task['env_vars'], expected_env_vars)
