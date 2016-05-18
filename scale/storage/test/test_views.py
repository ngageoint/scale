from __future__ import unicode_literals

import json

import django
from mock import MagicMock
from django.test import TestCase, TransactionTestCase
from rest_framework import status

import storage.brokers.factory as broker_factory
import storage.test.utils as storage_test_utils
from storage.brokers.broker import Broker
from storage.models import Workspace


class TestWorkspacesView(TestCase):

    def setUp(self):
        django.setup()

        self.workspace1 = storage_test_utils.create_workspace(name='ws1')
        self.workspace2 = storage_test_utils.create_workspace(name='ws2')

    def test_successful(self):
        """Tests successfully calling the get all workspaces view."""

        url = '/workspaces/'
        response = self.client.get(url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)
        for entry in result['results']:
            expected = None
            if entry['id'] == self.workspace1.id:
                expected = self.workspace1
            elif entry['id'] == self.workspace2.id:
                expected = self.workspace2
            else:
                self.fail('Found unexpected result: %s' % entry['id'])
            self.assertEqual(entry['name'], expected.name)
            self.assertEqual(entry['title'], expected.title)

    def test_name(self):
        """Tests successfully calling the workspaces view filtered by workspace name."""

        url = '/workspaces/?name=%s' % self.workspace1.name
        response = self.client.generic('GET', url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)

    def test_sorting(self):
        """Tests custom sorting."""

        url = '/workspaces/?order=name'
        response = self.client.get(url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)
        self.assertEqual(result['results'][0]['title'], self.workspace1.title)

    def test_reverse_sorting(self):
        """Tests custom sorting in reverse."""

        url = '/workspaces/?order=-name'
        response = self.client.get(url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace2.name)
        self.assertEqual(result['results'][0]['title'], self.workspace2.title)


class TestWorkspaceCreateView(TestCase):

    def setUp(self):
        django.setup()

    def test_missing_configuration(self):
        """Tests calling the create Workspace view with missing configuration."""

        url = '/workspaces/'
        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests calling the create Workspace view with configuration that is not a dict."""

        url = '/workspaces/'
        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': 123,
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests calling the create Workspace view with invalid configuration."""

        url = '/workspaces/'
        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': {
                'broker': 123,
            }
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the create Workspace view successfully."""

        url = '/workspaces/'
        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'base_url': 'http://host/my/path/',
            'is_active': False,
            'json_config': {
                'broker': {
                    'type': 'host',
                    'host_path': '/host/path',
                },
            },
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        result = json.loads(response.content)

        workspaces = Workspace.objects.filter(name='ws-name')

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(workspaces), 1)

        self.assertEqual(result['title'], workspaces[0].title)
        self.assertEqual(result['description'], workspaces[0].description)
        self.assertDictEqual(result['json_config'], workspaces[0].json_config)
        self.assertEqual(result['base_url'], workspaces[0].base_url)
        self.assertEqual(result['is_active'], workspaces[0].is_active)
        self.assertFalse(workspaces[0].is_active)


class TestWorkspaceDetailsView(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()

    def test_not_found(self):
        """Tests successfully calling the get workspace details view with a workspace id that does not exist."""

        url = '/workspaces/100/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_successful(self):
        """Tests successfully calling the get workspace details view."""

        url = '/workspaces/%d/' % self.workspace.id
        response = self.client.get(url)
        result = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.workspace.id)
        self.assertEqual(result['name'], self.workspace.name)
        self.assertEqual(result['title'], self.workspace.title)


class TestWorkspacesValidationView(TransactionTestCase):
    """Tests related to the workspaces validation endpoint"""

    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests validating a new workspace."""
        url = '/workspaces/validation/'
        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'base_url': 'http://host/my/path/',
            'is_active': False,
            'json_config': {
                'broker': {
                    'type': 'host',
                    'host_path': '/host/path',
                },
            },
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_missing_configuration(self):
        """Tests validating a new workspace with missing configuration."""

        url = '/workspaces/validation/'
        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests validating a new workspace with configuration that is not a dict."""

        url = '/workspaces/validation/'
        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': 123,
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests validating a new workspace with invalid configuration."""

        url = '/workspaces/validation/'
        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': {
                'broker': 123,
            },
        }
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_warnings(self):
        """Tests validating a new workspace where the broker type is changed."""

        json_config = {
            'broker': {
                'type': 'host',
                'host_path': '/host/path',
            },
        }
        storage_test_utils.create_workspace(name='ws-test', json_config=json_config)

        url = '/workspaces/validation/'
        json_data = {
            'name': 'ws-test',
            'json_config': {
                'broker': {
                    'type': 'nfs',
                    'nfs_path': 'host:/dir',
                },
            },
        }

        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0]['id'], 'broker_type')
