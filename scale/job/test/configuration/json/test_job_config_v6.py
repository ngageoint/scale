from __future__ import unicode_literals

import django
from django.test import TestCase

from job.configuration.configuration import JobConfiguration
from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.json.job_config_v6 import convert_config_to_v6_json, JobConfigurationV6
from job.configuration.mount import HostMountConfig, VolumeMountConfig


class TestJobConfigurationV6(TestCase):

    def setUp(self):
        django.setup()

    def test_convert_config_to_v6_json(self):
        """Tests calling convert_config_to_v6_json()"""

        # Try configuration with nothing set
        config = JobConfiguration()
        json = convert_config_to_v6_json(config)
        JobConfigurationV6(config=json.get_dict(), do_validate=True)  # Revalidate

        # Try configuration with a variety of values
        config = JobConfiguration()
        config.add_mount(HostMountConfig('mount_1', '/the/host/path'))
        config.add_mount(VolumeMountConfig('mount_2', 'driver', {'opt_1': 'foo', 'opt_2': 'bar'}))
        config.default_output_workspace = 'workspace_1'
        config.add_output_workspace('output_2', 'workspace_2')
        config.priority = 999
        config.add_setting('setting_1', 'Hello')
        config.add_setting('setting_2', 'Scale!')
        json = convert_config_to_v6_json(config)
        JobConfigurationV6(config=json.get_dict(), do_validate=True)  # Revalidate
        self.assertSetEqual(set(json.get_dict()['mounts'].keys()), {'mount_1', 'mount_2'})
        self.assertEqual(json.get_dict()['priority'], 999)
        self.assertSetEqual(set(json.get_dict()['settings'].keys()), {'setting_1', 'setting_2'})

    def test_init_validation(self):
        """Tests the validation done in __init__"""

        # Try minimal acceptable configuration
        JobConfigurationV6(do_validate=True)

        # Invalid version
        config_dict = {'version': 'BAD'}
        with self.assertRaises(InvalidJobConfiguration) as context:
            JobConfigurationV6(config_dict, do_validate=True)
            self.assertEqual(context.exception.error.name, 'INVALID_VERSION')

        # Valid v6 configuration
        config_dict = {'version': '6', 'mounts': {'mount_1': {'type': 'host', 'host_path': '/the/host/path'},
                                                  'mount_2': {'type': 'volume', 'driver': 'driver',
                                                              'driver_opts': {'opt_1': 'foo', 'opt_2': 'bar'}}},
                       'output_workspaces': {'default': 'workspace_1', 'outputs': {'output': 'workspace_2'}},
                       'priority': 999, 'settings': {'setting_1': '1234', 'setting_2': '5678'}}
        existing = JobConfigurationV6(config=config_dict, do_validate=True)
        jc = existing.get_configuration()
        vol1 = jc.get_mount_volume('mount_1', 'test1', '/test/path', 'ro')
        self.assertEqual(vol1.name, 'test1')
        self.assertEqual(vol1.container_path, '/test/path')
        self.assertEqual(vol1.mode, 'ro')
        self.assertEqual(vol1.is_host, True)
        self.assertEqual(vol1.host_path, '/the/host/path')
        vol2 = jc.get_mount_volume('mount_2', 'test2', '/test/path', 'ro')
        self.assertEqual(vol2.name, 'test2')
        self.assertEqual(vol2.container_path, '/test/path')
        self.assertEqual(vol2.mode, 'ro')
        self.assertEqual(vol2.is_host, False)
        self.assertEqual(vol2.host_path, None)
        self.assertEqual(vol2.driver, 'driver')
        self.assertDictEqual(vol2.driver_opts, {'opt_1': 'foo', 'opt_2': 'bar'})
        self.assertEqual(jc.get_output_workspace('test'), 'workspace_1')
        self.assertEqual(jc.get_output_workspace('output'), 'workspace_2')
        self.assertEqual(jc.priority, 999)
        self.assertEqual(jc.get_setting_value('setting_1'), '1234')
        self.assertEqual(jc.get_setting_value('setting_2'), '5678')

        # Overriding some settings from an existing config
        config_dict = {'version': '6', 'priority': 888, 'settings': {'setting_1': '123', 'setting_2': '678'}}
        jc = JobConfigurationV6(config=config_dict, existing=existing, do_validate=True).get_configuration()
        vol1 = jc.get_mount_volume('mount_1', 'test1', '/test/path', 'ro')
        self.assertEqual(vol1.name, 'test1')
        self.assertEqual(vol1.container_path, '/test/path')
        self.assertEqual(vol1.mode, 'ro')
        self.assertEqual(vol1.is_host, True)
        self.assertEqual(vol1.host_path, '/the/host/path')
        vol2 = jc.get_mount_volume('mount_2', 'test2', '/test/path', 'ro')
        self.assertEqual(vol2.name, 'test2')
        self.assertEqual(vol2.container_path, '/test/path')
        self.assertEqual(vol2.mode, 'ro')
        self.assertEqual(vol2.is_host, False)
        self.assertEqual(vol2.host_path, None)
        self.assertEqual(vol2.driver, 'driver')
        self.assertDictEqual(vol2.driver_opts, {'opt_1': 'foo', 'opt_2': 'bar'})
        self.assertEqual(jc.get_output_workspace('test'), 'workspace_1')
        self.assertEqual(jc.get_output_workspace('output'), 'workspace_2')
        self.assertEqual(jc.priority, 888)
        self.assertEqual(jc.get_setting_value('setting_1'), '123')
        self.assertEqual(jc.get_setting_value('setting_2'), '678')

