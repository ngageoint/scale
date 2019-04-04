from __future__ import unicode_literals

import os

import django
from django.test import TestCase

import recipe.test.utils as recipe_test_utils
import storage.test.utils as storage_test_utils
from ingest.strike.configuration.strike_configuration import StrikeConfiguration
from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from ingest.strike.configuration.json.configuration_v6 import StrikeConfigurationV6
from storage.models import Workspace


class TestStrikeConfigurationV6(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.new_workspace = storage_test_utils.create_workspace()
        self.inactive_workspace = storage_test_utils.create_workspace(is_active=False)

    def test_bare_min(self):
        """Tests calling StrikeConfigurationV6 constructor with bare minimum JSON"""

        # No exception is success
        StrikeConfigurationV6({
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }, do_validate=True)

    def test_bad_version(self):
        """Tests calling StrikeConfigurationV6 constructor with bad version number."""

        config = {
            'version': 'BAD VERSION',
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfigurationV6, config, True)

    def test_missing_workspace(self):
        """Tests calling StrikeConfigurationV6 constructor with missing workspace"""

        config = {
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfigurationV6, config, True)

    def test_missing_monitor(self):
        """Tests calling StrikeConfigurationV6 constructor with missing monitor"""

        config = {
            'workspace': self.workspace.name,
            'files_to_ingest': [{
                'filename_regex': '.*txt'
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfigurationV6, config, True)

    def test_blank_filename_regex(self):
        """Tests calling StrikeConfigurationV6 constructor with blank filename_regex"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': ''
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfigurationV6, config, True)

    def test_bad_recipe(self):
        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': ''
            }],
            'recipe': {
                'name': 'recipe',
            },
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfigurationV6, config, True)

    def test_absolute_workspace_path(self):
        """Tests calling StrikeConfigurationV6 constructor with absolute new_file_path."""

        config = {
            'version': 'BAD VERSION',
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_file_path': '/absolute/path'
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfigurationV6, config, True)

    def test_successful_all(self):
        """Tests calling StrikeConfigurationV6 constructor successfully with all information"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['one', 'two'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': self.workspace.name,
            }],
            'recipe': {
                'name': 'test-recipe',
                'revision_num': 1,
            },
        }
        # No exception is success
        StrikeConfigurationV6(config, do_validate=True)

    def test_validate_bad_monitor_type(self):
        """Tests calling StrikeConfigurationV6.validate() with a bad monitor type"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'BAD',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
            }],
        }

        configuration = StrikeConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidStrikeConfiguration, configuration.validate)

    def test_validate_mismatched_monitor_type(self):
        """Tests calling StrikeConfigurationV6.validate() with a monitor type that does not match the broker type"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 's3',
                'sqs_name': 'my-sqs',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
            }],
        }

        configuration = StrikeConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidStrikeConfiguration, configuration.validate)

    def test_validate_bad_workspace(self):
        """Tests calling StrikeConfigurationV6.validate() with a bad workspace"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_workspace': 'BADWORKSPACE',
            }],
        }

        configuration = StrikeConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidStrikeConfiguration, configuration.validate)

    def test_validate_workspace_not_active(self):
        """Tests calling StrikeConfigurationV6.validate() with a new workspace that is not active"""

        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'new_workspace': self.inactive_workspace.name,
            }],
        }

        configuration = StrikeConfigurationV6(config).get_configuration()
        self.assertRaises(InvalidStrikeConfiguration, configuration.validate)

    def test_validate_successful_all(self):
        """Tests calling StrikeConfiguration.validate() successfully with all information"""

        recipe = recipe_test_utils.create_recipe_type_v6(definition=recipe_test_utils.RECIPE_DEFINITION)
        config = {
            'workspace': self.workspace.name,
            'monitor': {
                'type': 'dir-watcher',
                'transfer_suffix': '_tmp',
            },
            'files_to_ingest': [{
                'filename_regex': '.*txt',
                'data_types': ['one', 'two'],
                'new_file_path': os.path.join('my', 'path'),
                'new_workspace': self.new_workspace.name,
            }],
            'recipe': {
                'name': recipe.name,
                'revision_num': recipe.revision_num
            },
        }

        # No exception is success
        StrikeConfigurationV6(config).get_configuration().validate()
