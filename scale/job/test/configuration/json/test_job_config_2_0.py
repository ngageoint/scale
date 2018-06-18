from __future__ import unicode_literals

import django
from django.test import TestCase

from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.json.job_config_2_0 import JobConfigurationV2


class TestJobConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_successful_validation(self):
        """Tests successful validation done in __init__"""

        # Try minimal acceptable configuration
        JobConfigurationV2()

        # Test all configuration elements
        config = {'mounts': {'mount_1': {'type': 'volume', 'driver': 'x-driver', 'driver_opts': {'opt_1': 'x',
                                                                                                 'opt_2': 'y'}},
                             'mount_2': {'type': 'host', 'host_path': '/host/path'}},
                  'settings': {'setting_1': 'value_1', 'setting_2': 'value_2'}}
        job_configuration = JobConfigurationV2(config)
        self.assertEqual(job_configuration.get_dict()['version'], '2.0')

    def test_invalid_mounts(self):
        """Tests validation done in __init__ where the mounts are invalid"""

        # Invalid mount type
        config = {'mounts': {'mount_1': {'type': 'bad-type', 'host_path': '/host/path'}}}
        self.assertRaises(InvalidJobConfiguration, JobConfigurationV2, config)

        # Host mount missing host_path
        config = {'mounts': {'mount_1': {'type': 'host'}}}
        self.assertRaises(InvalidJobConfiguration, JobConfigurationV2, config)

        # Host mount with relative host path
        config = {'mounts': {'mount_1': {'type': 'host', 'host_path': 'host/path'}}}
        self.assertRaises(InvalidJobConfiguration, JobConfigurationV2, config)

        # Host mount with driver
        config = {'mounts': {'mount_1': {'type': 'host', 'host_path': '/host/path', 'driver': 'x-driver'}}}
        self.assertRaises(InvalidJobConfiguration, JobConfigurationV2, config)

        # Host mount with driver-opts
        config = {'mounts': {'mount_1': {'type': 'host', 'host_path': '/host/path', 'driver-opts': {'x': 'y'}}}}
        self.assertRaises(InvalidJobConfiguration, JobConfigurationV2, config)

        # Volume mount missing driver
        config = {'mounts': {'mount_1': {'type': 'volume'}}}
        self.assertRaises(InvalidJobConfiguration, JobConfigurationV2, config)

        # Volume mount with driver
        config = {'mounts': {'mount_1': {'type': 'volume', 'host_path': '/host/path', 'driver': 'x-driver'}}}
        self.assertRaises(InvalidJobConfiguration, JobConfigurationV2, config)

    def test_invalid_settings(self):
        """Tests validation done in __init__ where the settings are invalid"""

        # Blank setting
        config = {'settings': {'setting_1': ''}}
        self.assertRaises(InvalidJobConfiguration, JobConfigurationV2, config)

    def test_convert_from_1_0(self):
        """Tests the conversion from version 1.0 of the schema"""

        name_1 = 'setting_name'
        value_1 = 'some_val'
        name_2 = 'setting2'
        value_2 = 'other_val'

        config = {
            'version': '1.0',
            'default_settings': {
                name_1: value_1,
                name_2: value_2
            }
        }

        job_configuration = JobConfigurationV2(config)
        self.assertEqual(job_configuration.get_setting_value(name_1), value_1)
        self.assertEqual(job_configuration.get_setting_value(name_2), value_2)
