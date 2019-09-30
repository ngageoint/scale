from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import patch, Mock

from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Mem, Disk
from scheduler.resources.manager import resource_mgr
from scheduler.node.agent import Agent
from scheduler.resources.offer import ResourceOffer
from util.host import HostAddress, host_address_from_mesos_url


class TestResourceManager(TestCase):

    def setUp(self):
        django.setup()
        resource_mgr.clear()
        self.agent_1 = Agent('agent_1', 'host_1')
        self.agent_2 = Agent('agent_2', 'host_2')
        self.framework_id = '1234'
        offer_1 = ResourceOffer('offer_1', self.agent_1.agent_id, self.framework_id,
                                NodeResources([Cpus(2.0), Mem(1024.0), Disk(1024.0)]), now(), None)
        offer_2 = ResourceOffer('offer_2', self.agent_2.agent_id, self.framework_id,
                                NodeResources([Cpus(25.0), Mem(2048.0), Disk(2048.0)]), now(), None)
        resource_mgr.add_new_offers([offer_1, offer_2])
        resource_mgr.refresh_agent_resources([], now())

    @patch('mesos_api.unversioned.agent.make_dcos_request')
    def test_successful_mesos_sync(self, mock_dcos):
        """Tests doing a successful sync with mesos"""
        mock_dcos.return_value.json.return_value = {'slaves': [
            {'id': 'agent_1', 'resources': {'cpus': 1.0, 'mem': 1024.0, 'disk': 1024.0}}
        ]}

        host = host_address_from_mesos_url('http://leader.mesos:80/mesos')
        resource_mgr.sync_with_mesos(host)
        self.assertTrue(resource_mgr._agent_resources['agent_1']._total_resources.is_equal(
                         NodeResources([Cpus(1.0), Mem(1024.0), Disk(1024.0)])))

    @patch('mesos_api.unversioned.agent.make_dcos_request')
    def test_mesos_sync_error(self, mock_dcos):
        """Tests doing a successful sync with mesos"""
        mock_dcos.return_value.json.return_value = {'slaves': [
            {'no_id_key': 'agent_1', 'resources': {'cpus': 1.0, 'mem': 1024.0, 'disk': 1024.0}}
        ]}

        host = host_address_from_mesos_url('http://leader.mesos:80/mesos')
        resource_mgr.sync_with_mesos(host)
        self.assertEqual(resource_mgr._mesos_error, 'Missing key u\'id\' in mesos response')
