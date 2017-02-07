from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import patch

from job.execution.job_exe import RunningJobExecution
from job.tasks.manager import TaskManager
from job.tasks.pull_task import PullTask
from job.tasks.update import TaskStatusUpdate
from job.test import utils as job_test_utils
from mesos_api.api import SlaveInfo
from node.test import utils as node_test_utils
from scheduler.cleanup.manager import CleanupManager
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
        node_1 = manager.get_node(self.node_agent_1)
        self.assertTrue(node_1.is_online)
        node_2 = manager.get_node(self.node_agent_2)
        self.assertFalse(node_2.is_online)

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
        node_1 = manager.get_node(self.node_agent_1)
        self.assertEqual(node_1.hostname, self.node_1.hostname)
        self.assertTrue(node_1.is_online)
        self.assertIsNone(manager.get_node(self.node_agent_2))

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
        node_1 = manager.get_node(self.node_agent_1)
        self.assertEqual(node_1.hostname, self.node_1.hostname)
        self.assertTrue(node_1.is_online)
        self.assertIsNone(manager.get_node(self.node_agent_2))
        node_2 = manager.get_node(self.node_agent_3)
        self.assertEqual(node_2.hostname, 'host_2')
        self.assertTrue(node_2.is_online)

    @patch('scheduler.node.manager.api.get_slaves')
    def test_get_pull_tasks(self, mock_get_slaves):
        """Tests getting Docker pull tasks from the manager"""

        mock_get_slaves.return_value = self.slave_infos

        manager = NodeManager()
        manager.register_agent_ids([self.node_agent_1, self.node_agent_2])
        manager.sync_with_database('master_host', 5050)
        for node in manager.get_nodes():
            node._initial_cleanup_completed()
            node._update_state()

        tasks = manager.get_next_tasks(now())
        self.assertEqual(len(tasks), 2)
        for task in tasks:
            self.assertTrue(isinstance(task, PullTask))

    @patch('scheduler.node.manager.api.get_slaves')
    def test_pull_task_change_agent_id(self, mock_get_slaves):
        """Tests the NodeManager where a node's agent ID changes during a pull task"""

        mock_get_slaves.return_value = self.slave_infos

        manager = NodeManager()
        manager.register_agent_ids([self.node_agent_1, self.node_agent_2])
        manager.sync_with_database('master_host', 5050)
        for node in manager.get_nodes():
            node._initial_cleanup_completed()
            node._update_state()
        tasks = manager.get_next_tasks(now())

        task_mgr = TaskManager()
        task_2 = None
        for task in tasks:
            task_mgr.launch_tasks([task], now())
            if task.agent_id == self.node_agent_2:
                task_2 = task

        # Node 2 changes agent ID to 3
        mock_get_slaves.return_value = self.slave_infos_updated
        manager.lost_node(self.node_agent_2)
        manager.register_agent_ids([self.node_agent_3])
        manager.sync_with_database('master_host', 5050)

        # Should get new Docker pull task for node 2
        tasks = manager.get_next_tasks(now())
        self.assertEqual(len(tasks), 1)
        new_task_2 = tasks[0]
        self.assertEqual(new_task_2.agent_id, self.node_agent_3)

        # Task update comes back for original node 2 Docker pull task, manager should ignore with no exception
        update = job_test_utils.create_task_status_update(task_2.id, task_2.agent_id, TaskStatusUpdate.FAILED, now())
        task_mgr.handle_task_update(update)
        manager.handle_task_update(update)

    @patch('scheduler.node.manager.api.get_slaves')
    def test_get_initial_cleanup_tasks(self, mock_get_slaves):
        """Tests getting initial cleanup tasks from the manager"""

        mock_get_slaves.return_value = self.slave_infos

        when = now()
        manager = NodeManager()
        tasks = manager.get_next_tasks(when)
        self.assertListEqual(tasks, [])  # No tasks yet due to no nodes

        manager.register_agent_ids([self.node_agent_1, self.node_agent_2])
        manager.sync_with_database('master_host', 5050)

        tasks = manager.get_next_tasks(when)
        self.assertEqual(len(tasks), 2)
        for task in tasks:
            self.assertTrue(task.is_initial_cleanup)

    @patch('scheduler.node.manager.api.get_slaves')
    def test_job_exe_clean_task(self, mock_get_slaves):
        """Tests the NodeManager where a cleanup task is returned to clean up a job execution"""

        mock_get_slaves.return_value = self.slave_infos

        when = now()
        node_mgr = NodeManager()
        node_mgr.register_agent_ids([self.node_agent_1, self.node_agent_2])
        node_mgr.sync_with_database('master_host', 5050)
        cleanup_mgr = CleanupManager()
        cleanup_mgr.update_nodes(node_mgr.get_nodes())
        tasks = node_mgr.get_next_tasks(when)

        task_mgr = TaskManager()
        # Complete initial cleanup tasks
        for task in tasks:
            task_mgr.launch_tasks([task], now())
            update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
            task_mgr.handle_task_update(update)
            node_mgr.handle_task_update(update)

        # Mark image pull done to get rid of image tasks
        for node in node_mgr.get_nodes():
            node._image_pull_completed()
            node._update_state()

        job_exe = job_test_utils.create_job_exe(node=self.node_1)
        # Add a job execution to clean up and get the cleanup task for it
        cleanup_mgr.add_job_execution(RunningJobExecution(job_exe))
        tasks = node_mgr.get_next_tasks(when)
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task.agent_id, self.node_agent_1)
        self.assertFalse(task.is_initial_cleanup)
        self.assertEqual(len(task.job_exes), 1)
