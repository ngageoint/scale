from __future__ import unicode_literals

import django
from django.test import TestCase
from mock import patch

from mesos_api.api import SlaveInfo
from node.test import utils as node_test_utils
from scheduler.sync.node_manager import NodeManager


class TestNodeManager(TestCase):

    def setUp(self):
        django.setup()

        self.node_agent_1 = 'agent_1'
        self.node_agent_2 = 'agent_2'
        self.node_1 = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent_1)

        self.slave_infos = [SlaveInfo('host_1', slave_id=self.node_agent_1),
                            SlaveInfo('host_2', slave_id=self.node_agent_2)]

    @patch('scheduler.sync.node_manager.api.get_slaves')
    def test_successful_update(self, mock_get_slaves):
        """Tests doing a successful database update"""

        mock_get_slaves.return_value = self.slave_infos

        manager = NodeManager()
        manager.add_agent_ids([self.node_agent_1, self.node_agent_2])
        manager.lost_node(self.node_agent_2)
        manager.sync_with_database('master_host', 5050)

        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 2)
        for node in nodes:
            if node.slave_id == self.node_agent_1:
                self.assertTrue(node.is_online)
            else:
                self.assertFalse(node.is_online)
