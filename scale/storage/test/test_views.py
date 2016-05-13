from __future__ import unicode_literals

import json

import django
from django.test import TestCase
from rest_framework import status

import storage.test.utils as storage_test_utils
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
            'configuration': 123,
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
            'configuration': {
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
            'configuration': {
                'broker': {
                    'type': 'host',
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
