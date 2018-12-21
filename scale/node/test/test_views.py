from __future__ import unicode_literals

import json
from datetime import timedelta

import django
from django.test import TransactionTestCase
from django.utils.timezone import now
from mock import patch
from rest_framework import status

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import node.test.utils as node_test_utils
import util.rest as rest_util
from mesos_api.api import SlaveInfo, HardwareResources
from scheduler.models import Scheduler


class TestNodesViewV5(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.node1 = node_test_utils.create_node()
        self.node2 = node_test_utils.create_node()

    def test_nodes_view(self):
        """Test the REST call to retrieve a list of nodes"""

        url = '/v5/nodes/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['results']), 2)

        for entry in results['results']:
            if entry['id'] == self.node1.id:
                self.assertEqual(entry['hostname'], self.node1.hostname)
            elif entry['id'] == self.node2.id:
                self.assertEqual(entry['hostname'], self.node2.hostname)
            else:
                self.fail('Unexpected node in results: %i' % entry['id'])

class TestNodesViewV6(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.node1 = node_test_utils.create_node()
        self.node2 = node_test_utils.create_node()

    def test_nodes_view(self):
        """Test the REST call to retrieve a list of nodes"""

        url = '/v6/nodes/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['results']), 2)

        for entry in results['results']:
            if entry['id'] == self.node1.id:
                self.assertEqual(entry['hostname'], self.node1.hostname)
            elif entry['id'] == self.node2.id:
                self.assertEqual(entry['hostname'], self.node2.hostname)
            else:
                self.fail('Unexpected node in results: %i' % entry['id'])

class TestNodesViewEmptyV5(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_nodes_view(self):
        """ test the REST call to retrieve an empty list of nodes"""
        url = '/v5/nodes/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['results']), 0)

class TestNodesViewEmptyV6(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_nodes_view(self):
        """ test the REST call to retrieve an empty list of nodes"""
        url = '/v6/nodes/'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        results = json.loads(response.content)
        self.assertEqual(len(results['results']), 0)
        
class TestNodeDetailsViewV5(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.node1 = node_test_utils.create_node()
        self.node2 = node_test_utils.create_node()
        self.node3 = node_test_utils.create_node()

        Scheduler.objects.create(id=1)

    def test_get_node_success(self):
        """Test successfully calling the Get Node method."""

        url = '/v5/nodes/%d/' % self.node2.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertIn('hostname', result)
        self.assertEqual(result['hostname'], self.node2.hostname)

    def test_get_node_not_found(self):
        """Test calling the Get Node method with a bad node id."""

        url = '/v5/nodes/9999/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_update_node_success(self):
        """Test successfully calling the Update Node method."""

        json_data = {
            'is_paused': True,
            'pause_reason': 'Test reason',
        }

        url = '/v5/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['is_paused'], True)
        self.assertEqual(result['pause_reason'], json_data['pause_reason'])
        self.assertIn('hostname', result)
        self.assertEqual(result['hostname'], self.node2.hostname)

    def test_update_node_unpause(self):
        """Tests unpausing the node and specifying a reason."""

        json_data = {'is_paused': False, 'pause_reason': 'Test reason'}

        url = '/v5/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['is_paused'], False)
        self.assertIsNone(result['pause_reason'])
        self.assertIn('hostname', result)
        self.assertEqual(result['hostname'], self.node2.hostname)

    def test_update_node_not_found(self):
        """Test calling the Update Node method with a bad node id."""

        json_data = {
            'is_paused': False,
        }

        url = '/v5/nodes/9999/'
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_update_node_no_fields(self):
        """Test calling the Update Node method with no fields."""

        json_data = {}
        url = '/v5/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_update_node_extra_fields(self):
        """Test calling the Update Node method with extra fields."""

        json_data = {
            'foo': 'bar',
        }

        url = '/v5/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_update_active(self):
        """Test successfully deactivating a node."""

        json_data = {
            'is_active': False,
        }

        url = '/v5/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertEqual(result['is_active'], False)
        self.assertIn('deprecated', result)

class TestNodeDetailsViewV6(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.node1 = node_test_utils.create_node()
        self.node2 = node_test_utils.create_node()
        self.node3 = node_test_utils.create_node()

        Scheduler.objects.create(id=1)

    def test_get_node_success(self):
        """Test successfully calling the Get Node method."""

        url = '/v6/nodes/%d/' % self.node2.id
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

        result = json.loads(response.content)
        self.assertIn('hostname', result)
        self.assertEqual(result['hostname'], self.node2.hostname)

    def test_get_node_not_found(self):
        """Test calling the Get Node method with a bad node id."""

        url = '/v6/nodes/9999/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_update_node_success(self):
        """Test successfully calling the Update Node method."""

        json_data = {
            'is_paused': True,
            'pause_reason': 'Test reason',
        }

        url = '/v6/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_update_node_unpause(self):
        """Tests unpausing the node and specifying a reason."""

        json_data = {'is_paused': False, 'pause_reason': 'Test reason'}

        url = '/v6/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)

    def test_update_node_not_found(self):
        """Test calling the Update Node method with a bad node id."""

        json_data = {
            'is_paused': False,
        }

        url = '/v6/nodes/9999/'
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)

    def test_update_node_no_fields(self):
        """Test calling the Update Node method with no fields."""

        json_data = {}
        url = '/v6/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_update_node_extra_fields(self):
        """Test calling the Update Node method with extra fields."""

        json_data = {
            'foo': 'bar',
        }

        url = '/v6/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)

    def test_update_active(self):
        """Test successfully deactivating a node."""

        json_data = {
            'is_active': False,
        }

        url = '/v6/nodes/%d/' % self.node2.id
        response = self.client.patch(url, json.dumps(json_data), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, response.content)
