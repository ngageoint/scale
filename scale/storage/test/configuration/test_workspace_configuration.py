from __future__ import unicode_literals

import django
from django.test import TestCase

from storage.configuration.exceptions import InvalidWorkspaceConfiguration
from storage.configuration.workspace_configuration import WorkspaceConfiguration


class TestWorkspaceConfigurationInit(TestCase):

    def setUp(self):
        django.setup()

    def test_bare_min(self):
        """Tests calling WorkspaceConfiguration constructor with bare minimum JSON."""

        # No exception is success
        config = WorkspaceConfiguration({
            'broker': {
                'type': 'host',
                'host_path': '/the/path',
            },
        })
        config.validate_broker()

    def test_bad_version(self):
        """Tests calling WorkspaceConfiguration constructor with bad version number."""

        config = {
            'version': 'BAD VERSION',
            'broker': {
                'type': 'host',
            },
        }
        self.assertRaises(InvalidWorkspaceConfiguration, WorkspaceConfiguration, config)

    def test_bad_type(self):
        """Tests calling WorkspaceConfiguration constructor with bad broker type."""

        config = {
            'broker': {
                'type': 'BAD',
            },
        }
        self.assertRaises(InvalidWorkspaceConfiguration, WorkspaceConfiguration, config)

    def test_bad_host_config(self):
        """Tests calling WorkspaceConfiguration constructor with bad host broker configuration."""

        config = WorkspaceConfiguration({
            'broker': {
                'type': 'host',
            },
        })
        self.assertRaises(InvalidWorkspaceConfiguration, config.validate_broker)

    def test_successful(self):
        """Tests calling WorkspaceConfiguration constructor successfully with all information."""

        # No exception is success
        config = WorkspaceConfiguration({
            'broker': {
                'type': 'host',
                'host_path': '/host/path',
            },
        })
        config.validate_broker()
