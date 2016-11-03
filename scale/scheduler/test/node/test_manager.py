from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch

from mesos_api.api import SlaveInfo
from node.test import utils as node_test_utils
from scheduler.node.manager import NodeManager


class TestNodeManager(TestCase):

    def setUp(self):
        django.setup()

        self.node_agent_1 = 'agent_1'
        self.node_agent_2 = 'agent_2'
        self.node_agent_3 = 'agent_3'
        self.node_1 = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent_1)

        self.slave_infos = [SlaveInfo('host_1', slave_id=self.node_agent_1),
                            SlaveInfo('host_2', slave_id=self.node_agent_2)]
        self.slave_infos_updated = [SlaveInfo('host_1', slave_id=self.node_agent_1),
                                    SlaveInfo('host_2', slave_id=self.node_agent_3)]

    @patch('scheduler.node.manager.api.get_slaves')
    def test_successful_update(self, mock_get_slaves):
        """Tests doing a successful database update"""

        mock_get_slaves.return_value = self.slave_infos

        manager = NodeManager()
        manager.register_agent_ids([self.node_agent_1, self.node_agent_2])
        manager.sync_with_database('master_host', 5050)

        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 2)

    @patch('scheduler.node.manager.api.get_slaves')
    def test_lost_known_node(self, mock_get_slaves):
        """Tests the NodeManager where a known node was lost"""

        mock_get_slaves.return_value = self.slave_infos

        manager = NodeManager()
        manager.register_agent_ids([self.node_agent_1, self.node_agent_2])
        manager.sync_with_database('master_host', 5050)
        manager.lost_node(self.node_agent_2)

        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            if node.agent_id == self.node_agent_1:
                self.assertTrue(node.is_online)
            else:
                self.assertFalse(node.is_online)

    @patch('scheduler.node.manager.api.get_slaves')
    def test_lost_unknown_node(self, mock_get_slaves):
        """Tests the NodeManager where an unknown node was lost"""

        mock_get_slaves.return_value = self.slave_infos

        manager = NodeManager()
        manager.register_agent_ids([self.node_agent_1, self.node_agent_2])
        manager.lost_node(self.node_agent_2)
        manager.sync_with_database('master_host', 5050)

        # Unknown node 2 was lost before syncing with database, it should not appear in the manager
        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].hostname, self.node_1.hostname)
        self.assertTrue(nodes[0].is_online)

    @patch('scheduler.node.manager.api.get_slaves')
    def test_change_agent_id(self, mock_get_slaves):
        """Tests the NodeManager where a registered node changes its agent ID"""

        mock_get_slaves.return_value = self.slave_infos

        manager = NodeManager()
        manager.register_agent_ids([self.node_agent_1, self.node_agent_2])
        manager.sync_with_database('master_host', 5050)

        mock_get_slaves.return_value = self.slave_infos_updated
        manager.lost_node(self.node_agent_2)
        manager.register_agent_ids([self.node_agent_3])
        manager.sync_with_database('master_host', 5050)

        # Make sure two nodes are registered, one for agent 1 and one for agent 3, and both are online
        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            if node.hostname == self.node_1.hostname:
                self.assertEqual(node.agent_id, self.node_agent_1)
            else:
                self.assertEqual(node.agent_id, self.node_agent_3)
            self.assertTrue(node.is_online)
