from __future__ import unicode_literals

import django
from django.test import TestCase

from job.configuration.exceptions import InvalidExecutionConfiguration
from job.configuration.json.execution.exe_config import ExecutionConfiguration


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

    def test_create_copy(self):
        """Tests the create_copy() method"""

        config = {
            'version': '2.0',
            'input_files': {
                'INPUT_1': [{
                    'id': 1234,
                    'type': 'PRODUCT',
                    'workspace_id': 123,
                    'workspace_path': 'the/workspace/path/file.json',
                    'local_file_name': 'file_abcdfeg.json',
                    'is_deleted': False,
                }]
            },
            'output_workspaces': {
                'OUTPUT_1': 'WORKSPACE_1'
            },
            'tasks': [
                {
                    'task_id': 'task-1234',
                    'type': 'main',
                    'resources': {'cpu': 1.0},
                    'args': 'foo ${INPUT_1} ${JOB_OUTPUT_DIR}',
                    'env_vars': {'ENV_VAR_NAME': 'ENV_VAR_VALUE'},
                    'workspaces': {'WORKSPACE_NAME': {'mode': 'RO', 'volume_name': None}},
                    'mounts': {'MOUNT_NAME': 'MOUNT_VOLUME_NAME'},
                    'settings': {'SETTING_NAME': 'SETTING_VALUE'},
                    'volumes': {
                        'VOLUME_NAME_1': {
                            'container_path': '/the/container/path',
                            'mode': 'RO',
                            'type': 'host',
                            'host_path': '/the/host/path'
                        },
                        'VOLUME_NAME_2': {
                            'container_path': '/the/other/container/path',
                            'mode': 'RW',
                            'type': 'volume',
                            'driver': 'SUPER_DRIVER_5000',
                            'driver_opts': {'turbo': 'yes-pleez'}
                        }
                    },
                    'docker_params': [{'flag': 'hello', 'value': 'scale'}]
                }
            ]
        }
        exe_config = ExecutionConfiguration(config)

        copy = exe_config.create_copy()
        self.assertDictEqual(copy.get_dict(), config)


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
