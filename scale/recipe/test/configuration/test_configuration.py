from __future__ import unicode_literals

import django
from django.test import TestCase

from job.configuration.mount import HostMountConfig, VolumeMountConfig
from job.seed.manifest import SeedManifest
from recipe.configuration.configuration import RecipeConfiguration
from recipe.configuration.exceptions import InvalidRecipeConfiguration


class TestRecipeConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_add_mount(self):
        """Tests calling RecipeConfiguration.add_mount()"""

        configuration = RecipeConfiguration()
        host_mount = HostMountConfig('mount_1', '/the/host/path')
        configuration.add_mount(host_mount)

        vol_mount = VolumeMountConfig('mount_1', driver='driver', driver_opts={})
        with self.assertRaises(InvalidRecipeConfiguration) as context:
            configuration.add_mount(vol_mount)
        self.assertEqual(context.exception.error.name, 'DUPLICATE_MOUNT')

    def test_add_output_workspace(self):
        """Tests calling RecipeConfiguration.add_output_workspace()"""

        configuration = RecipeConfiguration()
        configuration.add_output_workspace('output_1', 'workspace_1')

        with self.assertRaises(InvalidRecipeConfiguration) as context:
            configuration.add_output_workspace('output_1', 'workspace_2')
        self.assertEqual(context.exception.error.name, 'DUPLICATE_WORKSPACE')

    def test_add_setting(self):
        """Tests calling RecipeConfiguration.add_setting()"""

        configuration = RecipeConfiguration()
        configuration.add_setting('setting_1', 'value_1')

        with self.assertRaises(InvalidRecipeConfiguration) as context:
            configuration.add_setting('setting_1', 'value_2')
        self.assertEqual(context.exception.error.name, 'DUPLICATE_SETTING')

        with self.assertRaises(InvalidRecipeConfiguration) as context:
            configuration.add_setting('setting_2', None)
        self.assertEqual(context.exception.error.name, 'INVALID_SETTING')

    def test_remove_secret_settings(self):
        """Tests calling RecipeConfiguration.remove_secret_settings()"""

        manifest_dict = {
            'seedVersion': '1.0.0',
            'job': {
                'name': 'random-number-gen',
                'jobVersion': '0.1.0',
                'packageVersion': '0.1.0',
                'title': 'Random Number Generator',
                'description': 'Generates a random number and outputs on stdout',
                'maintainer': {
                    'name': 'John Doe',
                    'email': 'jdoe@example.com'
                },
                'timeout': 10,
                'interface': {
                    'settings': [{'name': 'setting_a'}, {'name': 'secret_setting_a', 'secret': True},
                                 {'name': 'secret_setting_b', 'secret': True},
                                 {'name': 'secret_setting_c', 'secret': True}]
                }
            }
        }
        manifest = SeedManifest(manifest_dict)

        configuration = RecipeConfiguration()
        configuration.add_setting('setting_a', 'value_1')
        configuration.add_setting('secret_setting_a', 'secret_value_1')
        configuration.add_setting('secret_setting_b', 'secret_value_2')
        configuration.add_setting('setting_d', 'value_4')

        secret_settings = configuration.remove_secret_settings(manifest)

        self.assertDictEqual(secret_settings, {'secret_setting_a': 'secret_value_1',
                                               'secret_setting_b': 'secret_value_2'})
        self.assertDictEqual(configuration.settings, {'setting_a': 'value_1', 'setting_d': 'value_4'})

