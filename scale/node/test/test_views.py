#@PydevCodeAnalysisIgnore
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
from mesos_api.api import SlaveInfo, HardwareResources
from scheduler.models import Scheduler


class TestNodesView(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.node1 = node_test_utils.create_node()
        self.node2 = node_test_utils.create_node()

    def test_nodes_view(self):
        '''Test the REST call to retrieve a list of nodes'''

        url = u'/nodes/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results[u'results']), 2)

        for entry in results[u'results']:
            if entry[u'hostname'] == self.node1.hostname:
                self.assertEqual(entry[u'slave_id'], self.node1.slave_id)
            elif entry[u'hostname'] == self.node2.hostname:
                self.assertEqual(entry[u'slave_id'], self.node2.slave_id)
            else:
                self.fail('Unexpected node in results: %i', entry[u'hostname'])


class TestNodesViewEmpty(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_nodes_view(self):
        ''' test the REST call to retrieve an empty list of nodes'''
        url = u'/nodes/'
        response = self.client.generic('GET', url)
        results = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results[u'results']), 0)


class TestNodeDetailsView(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.node1 = node_test_utils.create_node()
        self.node2 = node_test_utils.create_node()
        self.node3 = node_test_utils.create_node()

        Scheduler.objects.create(id=1, master_hostname='localhost', master_port=5050)

    @patch('mesos_api.api.get_slave')
    def test_get_node_success(self, mock_get_slave):
        '''Test successfully calling the Get Node method.'''
        mock_get_slave.return_value = SlaveInfo(self.node2.hostname, self.node2.port,
                                                HardwareResources(4., 2048., 40000.))

        url = '/nodes/%d/' % self.node2.id
        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('hostname', data)
        self.assertEqual(data['hostname'], self.node2.hostname)
        self.assertEqual(data['resources']['total']['cpus'], 4.)
        self.assertEqual(data['resources']['total']['mem'], 2048.)
        self.assertEqual(data['resources']['total']['disk'], 40000.)
        self.assertEqual(data['job_exes_running'], [])
        self.assertNotIn('disconnected', data)

    @patch('mesos_api.api.get_slave')
    def test_get_node_master_disconnected(self, mock_get_slave):
        '''Test calling the Get Node method with a disconnected master.'''
        mock_get_slave.return_value = SlaveInfo(self.node2.hostname, self.node2.port)

        url = '/nodes/%d/' % self.node2.id
        response = self.client.get(url)
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('resources', data)
        self.assertEqual(data['disconnected'], True)

    def test_get_node_not_found(self):
        '''Test calling the Get Node method with a bad node id.'''

        url = '/nodes/9999/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('mesos_api.api.get_slave')
    def test_update_node_success(self, mock_get_slave):
        '''Test successfully calling the Update Node method.'''
        mock_get_slave.return_value = SlaveInfo(self.node2.hostname, self.node2.port,
                                                HardwareResources(4., 2048., 40000.))

        url = '/nodes/%d/' % self.node2.id
        data = {'is_paused': True, 'pause_reason': 'Test reason'}
        response = self.client.patch(url, json.dumps(data), "application/json")
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(data['is_paused'], True)
        self.assertEqual(data['pause_reason'], data['pause_reason'])
        self.assertIn('hostname', data)
        self.assertEqual(data['hostname'], self.node2.hostname)
        self.assertEqual(data['resources']['total']['cpus'], 4.)
        self.assertEqual(data['resources']['total']['mem'], 2048.)
        self.assertEqual(data['resources']['total']['disk'], 40000.)
        self.assertEqual(data['job_exes_running'], [])
        self.assertNotIn('disconnected', data)

    @patch('mesos_api.api.get_slave')
    def test_update_node_unpause(self, mock_get_slave):
        '''Tests unpausing the node and specifying a reason.'''
        mock_get_slave.return_value = SlaveInfo(self.node2.hostname, self.node2.port,
                                                HardwareResources(4., 2048., 40000.))
        
        url = '/nodes/%d/' % self.node2.id
        data = {'is_paused': False, 'pause_reason': 'Test reason'}
        response = self.client.patch(url, json.dumps(data), "application/json")
        data = json.loads(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(data['is_paused'], False)
        self.assertIsNone(data['pause_reason'])
        self.assertIn('hostname', data)
        self.assertEqual(data['hostname'], self.node2.hostname)
        self.assertEqual(data['resources']['total']['cpus'], 4.)
        self.assertEqual(data['resources']['total']['mem'], 2048.)
        self.assertEqual(data['resources']['total']['disk'], 40000.)
        self.assertEqual(data['job_exes_running'], [])
        self.assertNotIn('disconnected', data)

    def test_update_node_not_found(self):
        '''Test calling the Update Node method with a bad node id.'''

        url = '/nodes/9999/'
        data = {'is_paused': False}
        response = self.client.patch(url, json.dumps(data), "application/json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_node_no_fields(self):
        '''Test calling the Update Node method with no fields.'''

        url = '/nodes/%d/' % self.node2.id
        data = {}
        response = self.client.patch(url, json.dumps(data), "application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, '"No fields specified for update."')

    def test_update_node_extra_fields(self):
        '''Test calling the Update Node method with extra fields.'''

        url = '/nodes/%d/' % self.node2.id
        data = {'foo': 'bar'}
        response = self.client.patch(url, json.dumps(data), "application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, '"Unexpected fields: foo"')

    def test_update_active(self):
        '''Test successfully deactivating a node.'''

        url = '/nodes/%d/' % self.node2.id
        data = {'is_active': False}
        response = self.client.patch(url, json.dumps(data), "application/json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        data = json.loads(response.content)
        self.assertEqual(data['is_active'], False)
        self.assertIn('archived', data)


class TestNodesStatusView(TransactionTestCase):
    ''' Test class to test the REST service to retrieve the node status for all the nodes in the cluster.'''

    def setUp(self):
        django.setup()

        self.scheduler = Scheduler.objects.create(id=1, master_hostname='master', master_port=5050)

        self.node1 = node_test_utils.create_node()
        self.node2 = node_test_utils.create_node()
        self.node3 = node_test_utils.create_node()

        self.job = job_test_utils.create_job(status=u'COMPLETED')

        data_error = error_test_utils.create_error(category=u'DATA')
        system_error = error_test_utils.create_error(category=u'SYSTEM')

        job_test_utils.create_job_exe(job=self.job, status=u'FAILED', error=data_error, node=self.node2,
                                          created=now() - timedelta(hours=3), job_completed=now() - timedelta(hours=2))
        job_test_utils.create_job_exe(job=self.job, status=u'FAILED', error=system_error, node=self.node2,
                                          created=now() - timedelta(hours=3), job_completed=now() - timedelta(hours=2))
        job_test_utils.create_job_exe(job=self.job, status=u'FAILED', error=system_error, node=self.node1,
                                          created=now() - timedelta(hours=2), job_completed=now() - timedelta(hours=1))
        job_test_utils.create_job_exe(job=self.job, status=u'COMPLETED', node=self.node1,
                                          created=now() - timedelta(hours=1), job_completed=now())
        job_test_utils.create_job_exe(job=self.job, status=u'RUNNING', node=self.node3,
                                          created=now())

    @patch('mesos_api.api.get_slaves')
    def test_nodes_system_stats(self, mock_get_slaves):
        '''This method tests for when a node has not processed any jobs for the duration of time requested.'''
        mock_get_slaves.return_value = [
            SlaveInfo(self.node1.hostname, self.node1.port, HardwareResources(1, 2, 3)),
            SlaveInfo(self.node3.hostname, self.node3.port, HardwareResources(4, 5, 6)),
        ]

        url = u'/nodes/status/?started=PT1H30M0S'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), u'result  must be a dictionary')

        assert_message = u'({0} != 3) Expected to get the 3 nodes'.format(len(result[u'results']))
        self.assertEqual(len(result[u'results']), 3, assert_message)

        for entry in result[u'results']:
            hostname = entry[u'node'][u'hostname']
            self.assertIn(hostname, [self.node1.hostname, self.node2.hostname, self.node3.hostname])

            if hostname == self.node1.hostname:
                self.assertTrue(entry[u'is_online'])
                self.assertEqual(len(entry[u'job_exe_counts']), 2)
                for status_count in entry[u'job_exe_counts']:
                    if status_count[u'status'] == u'COMPLETED':
                        self.assertEqual(status_count[u'count'], 1)
                    elif status_count[u'status'] == u'FAILED':
                        self.assertEqual(status_count[u'count'], 1)
                    else:
                        self.fail(u'Unexpected job execution status found: %s' % status_count[u'status'])
            elif hostname == self.node2.hostname:
                self.assertFalse(entry[u'is_online'])
                for status_count in entry[u'job_exe_counts']:
                    if status_count[u'status'] == u'FAILED' and status_count[u'category'] == u'DATA':
                        self.assertEqual(status_count[u'count'], 1)
                    elif status_count[u'status'] == u'FAILED' and status_count[u'category'] == u'SYSTEM':
                        self.assertEqual(status_count[u'count'], 1)
                    else:
                        self.fail(u'Unexpected job execution status found: %s' % status_count[u'status'])
            elif hostname == self.node3.hostname:
                self.assertTrue(entry[u'is_online'])
                self.assertEqual(len(entry[u'job_exes_running']), 1)
                for status_count in entry[u'job_exe_counts']:
                    if status_count[u'status'] == u'RUNNING':
                        self.assertEqual(status_count[u'count'], 1)

    @patch('mesos_api.api.get_slaves')
    def test_nodes_stats(self, mock_get_slaves):
        '''This method tests retrieving all the nodes statistics
        for the three hour duration requested'''
        mock_get_slaves.return_value = [
            SlaveInfo(self.node1.hostname, self.node1.port, HardwareResources(1, 2, 3)),
            SlaveInfo(self.node3.hostname, self.node3.port, HardwareResources(4, 5, 6)),
        ]

        url = u'/nodes/status/?started=PT3H00M0S'
        response = self.client.generic('GET', url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = json.loads(response.content)
        self.assertTrue(isinstance(result, dict), u'result  must be a dictionary')

        assert_message = u'({0} != 3) Expected to get the 3 nodes'.format(len(result[u'results']))
        self.assertEqual(len(result[u'results']), 3, assert_message)

        for entry in result[u'results']:
            hostname = entry[u'node'][u'hostname']
            self.assertIn(hostname, [self.node1.hostname, self.node2.hostname, self.node3.hostname])

            if hostname == self.node1.hostname:
                self.assertTrue(entry[u'is_online'])
                self.assertEqual(len(entry[u'job_exe_counts']), 2)
                for status_count in entry[u'job_exe_counts']:
                    if status_count[u'status'] == u'COMPLETED':
                        self.assertEqual(status_count[u'count'], 1)
                    elif status_count[u'status'] == u'FAILED':
                        self.assertEqual(status_count[u'count'], 1)
                    else:
                        self.fail(u'Unexpected job execution status found: %s' % status_count[u'status'])
            elif hostname == self.node2.hostname:
                self.assertFalse(entry[u'is_online'])
                for status_count in entry[u'job_exe_counts']:
                    if status_count[u'status'] == u'FAILED' and status_count[u'category'] == u'DATA':
                        self.assertEqual(status_count[u'count'], 1)
                    elif status_count[u'status'] == u'FAILED' and status_count[u'category'] == u'SYSTEM':
                        self.assertEqual(status_count[u'count'], 1)
                    else:
                        self.fail(u'Unexpected job execution status found: %s' % status_count[u'status'])
            elif hostname == self.node3.hostname:
                self.assertTrue(entry[u'is_online'])
                self.assertEqual(len(entry[u'job_exes_running']), 1)
                for status_count in entry[u'job_exe_counts']:
                    if status_count[u'status'] == u'RUNNING':
                        self.assertEqual(status_count[u'count'], 1)
