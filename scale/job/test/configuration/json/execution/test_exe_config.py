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
