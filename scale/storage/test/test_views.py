from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from rest_framework import status

import storage.test.utils as storage_test_utils
import util.rest as rest_util
from storage.models import Workspace


class TestWorkspacesView(TestCase):

    def setUp(self):
        django.setup()

        self.workspace1 = storage_test_utils.create_workspace(name='ws1')
        self.workspace2 = storage_test_utils.create_workspace(name='ws2')

    def test_successful(self):
        """Tests successfully calling the get all workspaces view."""

        url = rest_util.get_url('/workspaces/')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
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

        url = rest_util.get_url('/workspaces/?name=%s' % self.workspace1.name)
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)

    def test_sorting(self):
        """Tests custom sorting."""

        url = rest_util.get_url('/workspaces/?order=name')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace1.name)
        self.assertEqual(result['results'][0]['title'], self.workspace1.title)

    def test_reverse_sorting(self):
        """Tests custom sorting in reverse."""

        url = rest_util.get_url('/workspaces/?order=-name')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['name'], self.workspace2.name)
        self.assertEqual(result['results'][0]['title'], self.workspace2.title)


class TestWorkspaceCreateView(TestCase):

    def setUp(self):
        django.setup()

    def test_missing_configuration(self):
        """Tests calling the create Workspace view with missing configuration."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
        }

        url = rest_util.get_url('/workspaces/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests calling the create Workspace view with configuration that is not a dict."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': 123,
        }

        url = rest_util.get_url('/workspaces/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests calling the create Workspace view with invalid configuration."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': {
                'broker': 123,
            }
        }

        url = rest_util.get_url('/workspaces/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_successful(self):
        """Tests calling the create Workspace view successfully."""

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

        url = rest_util.get_url('/workspaces/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        workspaces = Workspace.objects.filter(name='ws-name')
        self.assertEqual(len(workspaces), 1)

        result = json.loads(response.content)
        self.assertEqual(result['title'], workspaces[0].title)
        self.assertEqual(result['description'], workspaces[0].description)
        self.assertDictEqual(result['json_config'], workspaces[0].json_config)
        self.assertEqual(result['base_url'], workspaces[0].base_url)
        self.assertEqual(result['is_active'], workspaces[0].is_active)
        self.assertFalse(workspaces[0].is_active)


class TestWorkspaceDetailsView(TestCase):

    def setUp(self):
        django.setup()

        self.config = {
            'broker': {
                'type': 'host',
                'host_path': '/host/path',
            },
        }

        self.workspace = storage_test_utils.create_workspace(json_config=self.config)

    def test_not_found(self):
        """Tests successfully calling the get workspace details view with a workspace id that does not exist."""

        url = rest_util.get_url('/workspaces/100/')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_successful(self):
        """Tests successfully calling the get workspace details view."""

        url = rest_util.get_url('/workspaces/%d/' % self.workspace.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.workspace.id)
        self.assertEqual(result['name'], self.workspace.name)
        self.assertEqual(result['title'], self.workspace.title)

    def test_edit_simple(self):
        """Tests editing only the basic attributes of a workspace"""

        json_data = {
            'title': 'Title EDIT',
            'description': 'Description EDIT',
            'is_active': False,
        }

        url = rest_util.get_url('/workspaces/%d/' % self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), 'result  must be a dictionary')
        self.assertEqual(result['id'], self.workspace.id)
        self.assertEqual(result['title'], 'Title EDIT')
        self.assertEqual(result['description'], 'Description EDIT')
        self.assertDictEqual(result['json_config'], self.workspace.json_config)
        self.assertFalse(result['is_active'])

        workspace = Workspace.objects.get(pk=self.workspace.id)
        self.assertEqual(workspace.title, 'Title EDIT')
        self.assertEqual(workspace.description, 'Description EDIT')
        self.assertFalse(result['is_active'])

    def test_edit_config(self):
        """Tests editing the configuration of a workspace"""

        config = {
            'version': '1.0',
            'broker': {
                'type': 'nfs',
                'nfs_path': 'host:/dir',
            },
        }

        json_data = {
            'json_config': config,
        }

        url = rest_util.get_url('/workspaces/%d/' % self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['id'], self.workspace.id)
        self.assertEqual(result['title'], self.workspace.title)
        self.assertDictEqual(result['json_config'], config)

        workspace = Workspace.objects.get(pk=self.workspace.id)
        self.assertEqual(workspace.title, self.workspace.title)
        self.assertDictEqual(workspace.json_config, config)

    def test_edit_bad_config(self):
        """Tests attempting to edit a workspace using an invalid configuration"""

        config = {
            'version': 'BAD',
            'broker': {
                'type': 'nfs',
                'host_path': 'host:/dir',
            },
        }

        json_data = {
            'json_config': config,
        }

        url = rest_util.get_url('/workspaces/%d/' % self.workspace.id)
        response = self.client.generic('PATCH', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)


class TestWorkspacesValidationView(TestCase):
    """Tests related to the workspaces validation endpoint"""

    def setUp(self):
        django.setup()

    def test_successful(self):
        """Tests validating a new workspace."""
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

        url = rest_util.get_url('/workspaces/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertDictEqual(results, {'warnings': []}, 'JSON result was incorrect')

    def test_missing_configuration(self):
        """Tests validating a new workspace with missing configuration."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
        }

        url = rest_util.get_url('/workspaces/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_configuration_bad_type(self):
        """Tests validating a new workspace with configuration that is not a dict."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': 123,
        }

        url = rest_util.get_url('/workspaces/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_invalid_configuration(self):
        """Tests validating a new workspace with invalid configuration."""

        json_data = {
            'name': 'ws-name',
            'title': 'Workspace Title',
            'description': 'Workspace description',
            'json_config': {
                'broker': 123,
            },
        }

        url = rest_util.get_url('/workspaces/validation/')
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

        json_data = {
            'name': 'ws-test',
            'json_config': {
                'broker': {
                    'type': 'nfs',
                    'nfs_path': 'host:/dir',
                },
            },
        }

        url = rest_util.get_url('/workspaces/validation/')
        response = self.client.generic('POST', url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['warnings']), 1)
        self.assertEqual(results['warnings'][0]['id'], 'broker_type')
