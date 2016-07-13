#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import os

import django
from django.test import TestCase

import storage.test.utils as storage_test_utils
from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from ingest.strike.configuration.strike_configuration import StrikeConfiguration


class TestStrikeConfigurationInit(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()

    def test_bare_min(self):
        '''Tests calling StrikeConfiguration constructor with bare minimum JSON.'''

        # No exception is success
        StrikeConfiguration({
            'version': '1.0',
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace.name,
            }],
        })

    def test_bad_version(self):
        '''Tests calling StrikeConfiguration constructor with bad version number.'''

        config = {
            'version': 'BAD VERSION',
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace.name,
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_blank_mount(self):
        '''Tests calling StrikeConfiguration constructor with blank mount.'''

        config = {
            'mount': '',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace.name,
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_blank_transfer_suffix(self):
        '''Tests calling StrikeConfiguration constructor with blank transfer_suffix.'''

        config = {
            'mount': 'host:/my/path',
            'transfer_suffix': '',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace.name,
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_blank_filename_regex(self):
        '''Tests calling StrikeConfiguration constructor with blank filename_regex.'''

        config = {
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': '',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace.name,
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_blank_workspace_path(self):
        '''Tests calling StrikeConfiguration constructor with blank workspace_path.'''

        config = {
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'workspace_path': '',
                'workspace_name': self.workspace.name,
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_absolute_workspace_path(self):
        '''Tests calling StrikeConfiguration constructor with absolute workspace_path.'''

        config = {
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'workspace_path': os.path.join('/my', 'path'),
                'workspace_name': self.workspace.name,
            }],
        }
        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_successful(self):
        '''Tests calling StrikeConfiguration constructor successfully with all information.'''

        config = {
            'version': '1.0',
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'data_types': ['one', 'two'],
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace.name,
            }],
        }
        # No exception is success
        StrikeConfiguration(config)


class TestStrikeConfigurationValidateWorkspaces(TestCase):

    def setUp(self):
        django.setup()

        self.workspace_1 = storage_test_utils.create_workspace()
        self.workspace_2 = storage_test_utils.create_workspace()
        self.workspace_3 = storage_test_utils.create_workspace(is_active=False)

    def test_workspace_not_active(self):
        '''Tests calling StrikeConfiguration() with a workspace that is not active.'''

        config = {
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace_1.name,
            }, {
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace_3.name,
            }],
        }

        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_invalid_workspace(self):
        '''Tests calling StrikeConfiguration() with an invalid workspace name.'''

        config = {
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace_1.name,
            }, {
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': 'BAD_NAME',
            }],
        }

        self.assertRaises(InvalidStrikeConfiguration, StrikeConfiguration, config)

    def test_successful(self):
        '''Tests calling StrikeConfiguration() successfully.'''

        config = {
            'version': '1.0',
            'mount': 'host:/my/path',
            'transfer_suffix': '_tmp',
            'files_to_ingest': [{
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace_1.name,
            }, {
                'filename_regex': 'hello',
                'workspace_path': os.path.join('my', 'path'),
                'workspace_name': self.workspace_2.name,
            }],
        }

        # No exception is success
        StrikeConfiguration(config)
