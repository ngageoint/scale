from __future__ import unicode_literals

import django
from django.test import TestCase

from job.configuration.configuration import JobConfiguration
from job.configuration.exceptions import InvalidJobConfiguration
from job.configuration.mount import HostMountConfig, VolumeMountConfig
from job.seed.manifest import SeedManifest
from storage.test import utils as storage_test_utils


class TestJobConfiguration(TestCase):

    def setUp(self):
        django.setup()

    def test_add_mount(self):
        """Tests calling JobConfiguration.add_mount()"""

        configuration = JobConfiguration()
        host_mount = HostMountConfig('mount_1', '/the/host/path')
        configuration.add_mount(host_mount)

        vol_mount = VolumeMountConfig('mount_1', driver='driver', driver_opts={})
        with self.assertRaises(InvalidJobConfiguration) as context:
            configuration.add_mount(vol_mount)
        self.assertEqual(context.exception.error.name, 'DUPLICATE_MOUNT')

    def test_add_output_workspace(self):
        """Tests calling JobConfiguration.add_output_workspace()"""

        configuration = JobConfiguration()
        configuration.add_output_workspace('output_1', 'workspace_1')

        with self.assertRaises(InvalidJobConfiguration) as context:
            configuration.add_output_workspace('output_1', 'workspace_2')
        self.assertEqual(context.exception.error.name, 'DUPLICATE_WORKSPACE')

    def test_add_setting(self):
        """Tests calling JobConfiguration.add_setting()"""

        configuration = JobConfiguration()
        configuration.add_setting('setting_1', 'value_1')

        with self.assertRaises(InvalidJobConfiguration) as context:
            configuration.add_setting('setting_1', 'value_2')
        self.assertEqual(context.exception.error.name, 'DUPLICATE_SETTING')

        with self.assertRaises(InvalidJobConfiguration) as context:
            configuration.add_setting('setting_2', None)
        self.assertEqual(context.exception.error.name, 'INVALID_SETTING')

    def test_remove_secret_settings(self):
        """Tests calling JobConfiguration.remove_secret_settings()"""

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

        configuration = JobConfiguration()
        configuration.add_setting('setting_a', 'value_1')
        configuration.add_setting('secret_setting_a', 'secret_value_1')
        configuration.add_setting('secret_setting_b', 'secret_value_2')
        configuration.add_setting('setting_d', 'value_4')

        secret_settings = configuration.remove_secret_settings(manifest)

        self.assertDictEqual(secret_settings, {'secret_setting_a': 'secret_value_1',
                                               'secret_setting_b': 'secret_value_2'})
        self.assertDictEqual(configuration.settings, {'setting_a': 'value_1', 'setting_d': 'value_4'})

    def test_validate_mounts(self):
        """Tests calling JobConfiguration.validate() to validate mount configuration"""

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
                    'mounts': [{'name': 'mount_a', 'path': '/the/a/path'}, {'name': 'mount_b', 'path': '/the/b/path'},
                               {'name': 'mount_c', 'path': '/the/c/path'}]
                }
            }
        }
        manifest = SeedManifest(manifest_dict)

        configuration = JobConfiguration()
        configuration.add_mount(HostMountConfig('mount_a', '/the/host/a/path'))
        configuration.add_mount(HostMountConfig('mount_b', '/the/host/b/path'))
        configuration.add_mount(HostMountConfig('mount_c', '/the/host/c/path'))
        configuration.add_mount(HostMountConfig('mount_d', '/the/host/d/path'))

        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].name, 'UNKNOWN_MOUNT')

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
                    'mounts': [{'name': 'mount_a', 'path': '/the/a/path'}, {'name': 'mount_b', 'path': '/the/b/path'},
                               {'name': 'mount_c', 'path': '/the/c/path'}]
                }
            }
        }
        manifest = SeedManifest(manifest_dict)

        configuration = JobConfiguration()
        configuration.add_mount(HostMountConfig('mount_a', '/the/host/a/path'))
        configuration.add_mount(HostMountConfig('mount_b', '/the/host/b/path'))

        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].name, 'MISSING_MOUNT')

    def test_validate_output_workspaces(self):
        """Tests calling JobConfiguration.validate() to validate output workspaces"""

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
                    'outputs': {'files': [{'name': 'output_a', 'mediaType': 'image/gif', 'pattern': '*_a.gif'},
                                          {'name': 'output_b', 'mediaType': 'image/gif', 'pattern': '*_a.gif'}]}
                }
            }
        }
        manifest = SeedManifest(manifest_dict)

        configuration = JobConfiguration()

        # No workspaces defined
        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 2)
        self.assertEqual(warnings[0].name, 'MISSING_WORKSPACE')
        self.assertEqual(warnings[1].name, 'MISSING_WORKSPACE')

        # Workspace does not exist
        configuration.default_output_workspace = 'workspace_1'
        with self.assertRaises(InvalidJobConfiguration) as context:
            configuration.validate(manifest)
        self.assertEqual(context.exception.error.name, 'INVALID_WORKSPACE')

        # Default workspace defined with valid workspace
        workspace_1 = storage_test_utils.create_workspace(name='workspace_1')
        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 0)

        # Workspace is only defined for output_a
        configuration.default_output_workspace = None
        configuration.add_output_workspace('output_a', 'workspace_1')
        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].name, 'MISSING_WORKSPACE')

        # Workspace defined for both outputs
        storage_test_utils.create_workspace(name='workspace_2')
        configuration.add_output_workspace('output_b', 'workspace_2')
        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 0)

        # Workspace is deprecated
        workspace_1.is_active = False
        workspace_1.save()
        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].name, 'DEPRECATED_WORKSPACE')
        
    def test_no_default_workspace(self):
        """Tests calling JobConfiguration.validate() to validate output workspaces"""

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
                    'outputs': {'files': [{'name': 'output_a', 'mediaType': 'image/gif', 'pattern': '*_a.gif'},
                                          {'name': 'output_b', 'mediaType': 'image/gif', 'pattern': '*_a.gif'}]}
                }
            }
        }
        manifest = SeedManifest(manifest_dict)
        configuration = JobConfiguration()

        # No workspaces defined for outputs
        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 2)
        self.assertEqual(warnings[0].name, 'MISSING_WORKSPACE')
        self.assertEqual(warnings[1].name, 'MISSING_WORKSPACE')

    def test_validate_priority(self):
        """Tests calling JobConfiguration.validate() to validate priority"""

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
                'timeout': 10
            }
        }
        manifest = SeedManifest(manifest_dict)

        configuration = JobConfiguration()
        configuration.priority = 100

        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 0)

        configuration.priority = 0
        with self.assertRaises(InvalidJobConfiguration) as context:
            configuration.validate(manifest)
        self.assertEqual(context.exception.error.name, 'INVALID_PRIORITY')

        configuration.priority = -1
        with self.assertRaises(InvalidJobConfiguration) as context:
            configuration.validate(manifest)
        self.assertEqual(context.exception.error.name, 'INVALID_PRIORITY')

    def test_validate_settings(self):
        """Tests calling JobConfiguration.validate() to validate settings configuration"""

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

        configuration = JobConfiguration()
        configuration.add_setting('setting_a', 'value_1')
        configuration.add_setting('secret_setting_a', 'secret_value_1')
        configuration.add_setting('secret_setting_b', 'secret_value_2')
        configuration.add_setting('secret_setting_c', 'secret_value_3')
        configuration.add_setting('setting_4', 'value_4')

        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].name, 'UNKNOWN_SETTING')

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

        configuration = JobConfiguration()
        configuration.add_setting('setting_a', 'value_1')
        configuration.add_setting('secret_setting_a', 'secret_value_1')
        configuration.add_setting('secret_setting_b', 'secret_value_2')

        warnings = configuration.validate(manifest)
        self.assertEqual(len(warnings), 1)
        self.assertEqual(warnings[0].name, 'MISSING_SETTING')
