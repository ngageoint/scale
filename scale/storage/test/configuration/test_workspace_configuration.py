from __future__ import unicode_literals

import django
from django.test import TestCase

from storage.configuration.exceptions import InvalidWorkspaceConfiguration
from storage.configuration.json.workspace_config_1_0 import WorkspaceConfigurationV1
from storage.configuration.json.workspace_config_v6 import WorkspaceConfigurationV6


class TestWorkspaceConfigurationInit(TestCase):

    def setUp(self):
        django.setup()

    def test_bare_min(self):
        """Tests calling WorkspaceConfiguration constructor with bare minimum JSON."""

        # No exception is success
        config = WorkspaceConfigurationV1({
            'broker': {
                'type': 'host',
                'host_path': '/the/path',
            },
        }, do_validate=True).get_configuration()
        config.validate_broker()

        config = WorkspaceConfigurationV6({
            'broker': {
                'type': 'host',
                'host_path': '/the/path',
            },
        }, do_validate=True).get_configuration()
        config.validate_broker()

    def test_bad_version(self):
        """Tests calling WorkspaceConfiguration constructor with bad version number."""

        config = {
            'version': 'BAD VERSION',
            'broker': {
                'type': 'host',
            },
        }
        self.assertRaises(InvalidWorkspaceConfiguration, WorkspaceConfigurationV1, config)

        self.assertRaises(InvalidWorkspaceConfiguration, WorkspaceConfigurationV6, config)

    def test_bad_type(self):
        """Tests calling WorkspaceConfiguration constructor with bad broker type."""

        config = {
            'broker': {
                'type': 'BAD',
            },
        }
        self.assertRaises(InvalidWorkspaceConfiguration, WorkspaceConfigurationV1, config, True)

        self.assertRaises(InvalidWorkspaceConfiguration, WorkspaceConfigurationV6, config, True)

    def test_bad_host_config(self):
        """Tests calling WorkspaceConfiguration constructor with bad host broker configuration."""

        config = WorkspaceConfigurationV1({
            'broker': {
                'type': 'host',
            },
        }).get_configuration()
        self.assertRaises(InvalidWorkspaceConfiguration, config.validate_broker)

        config = WorkspaceConfigurationV6({
            'broker': {
                'type': 'host',
            },
        }).get_configuration()
        self.assertRaises(InvalidWorkspaceConfiguration, config.validate_broker)

    def test_successful(self):
        """Tests calling WorkspaceConfiguration constructor successfully with all information."""

        # No exception is success
        config = WorkspaceConfigurationV1({
            'broker': {
                'type': 'host',
                'host_path': '/host/path',
            },
        }, do_validate=True).get_configuration()
        config.validate_broker()

        config = WorkspaceConfigurationV6({
            'broker': {
                'type': 'host',
                'host_path': '/host/path',
            },
        }, do_validate = True).get_configuration()
        config.validate_broker()
