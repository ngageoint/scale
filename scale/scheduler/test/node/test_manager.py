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
from node.models import Node
from node.test import utils as node_test_utils
from scheduler.cleanup.manager import CleanupManager
from scheduler.models import Scheduler
from scheduler.node.agent import Agent
from scheduler.node.manager import NodeManager


class TestNodeManager(TestCase):

    def setUp(self):
        django.setup()

        self.scheduler = Scheduler()
        self.agent_1 = Agent('agent_1', 'host_1')
        self.agent_2 = Agent('agent_2', 'host_2')
        self.agent_3 = Agent('agent_3', 'host_2')  # Will represent a new agent ID for host 2
        self.node_1 = node_test_utils.create_node(hostname='host_1')

    def test_successful_update(self):
        """Tests doing a successful database update"""

        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)

        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 2)

    def test_sync_node_model(self):
        """Tests doing a successful database update when a node model has been updated in the database"""

        # Initial sync
        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)

        # Database model changes to inactive
        self.node_1.is_active = False
        self.node_1.save()

        # Sync with database
        manager.sync_with_database(self.scheduler)

        found_node_1 = False
        for node in manager.get_nodes():
            if node.hostname == self.node_1.hostname:
                found_node_1 = True
                self.assertFalse(node.is_active)
        self.assertTrue(found_node_1)

    def test_sync_and_remove_node_model(self):
        """Tests doing a successful database update when a node model should be removed from the scheduler"""

        # Initial sync
        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)

        # Database model changes to inactive
        self.node_1.is_active = False
        self.node_1.save()

        # Node is lost
        manager.lost_node(self.agent_1.agent_id)

        # Sync with database
        manager.sync_with_database(self.scheduler)

        # Make sure node 1 is gone
        found_node_1 = False
        for node in manager.get_nodes():
            if node.hostname == self.node_1.hostname:
                found_node_1 = True
        self.assertFalse(found_node_1)

    def test_sync_with_renamed_node(self):
        """Tests doing a successful database update when a node model has its hostname changed in the database"""

        # Initial sync
        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)

        self.node_1.hostname = 'new_host_1'
        self.node_1.save()

        # No exception is success
        manager.sync_with_database(self.scheduler)

    def test_lost_known_node(self):
        """Tests the NodeManager where a known node was lost"""

        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)
        manager.lost_node(self.agent_2.agent_id)

        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 2)
        node_1 = manager.get_node(self.agent_1.agent_id)
        self.assertTrue(node_1._is_online)
        node_2 = manager.get_node(self.agent_2.agent_id)
        self.assertFalse(node_2._is_online)

    def test_lost_unknown_node(self):
        """Tests the NodeManager where an unknown node was lost"""

        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.lost_node(self.agent_2.agent_id)
        manager.sync_with_database(self.scheduler)

        # Unknown node 2 was lost before syncing with database, it should not appear in the manager
        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 1)
        node_1 = manager.get_node(self.agent_1.agent_id)
        self.assertEqual(node_1.hostname, self.node_1.hostname)
        self.assertTrue(node_1._is_online)
        self.assertIsNone(manager.get_node(self.agent_2.agent_id))

    def test_change_agent_id(self):
        """Tests the NodeManager where a registered node changes its agent ID"""

        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)

        manager.lost_node(self.agent_2.agent_id)
        manager.register_agents([self.agent_3])
        manager.sync_with_database(self.scheduler)

        # Make sure two nodes are registered, one for agent 1 and one for agent 3, and both are online
        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 2)
        node_1 = manager.get_node(self.agent_1.agent_id)
        self.assertEqual(node_1.hostname, self.node_1.hostname)
        self.assertTrue(node_1._is_online)
        self.assertIsNone(manager.get_node(self.agent_2.agent_id))
        node_2 = manager.get_node(self.agent_3.agent_id)
        self.assertEqual(node_2.hostname, 'host_2')
        self.assertTrue(node_2._is_online)

    def test_change_agent_id_with_inactive_node(self):
        """Tests the NodeManager where a registered node changes its agent ID, and the node is inactive"""

        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)

        # Node 2 is now inactive
        Node.objects.filter(id=manager.get_node(self.agent_2.agent_id).id).update(is_active=False)
        manager.sync_with_database(self.scheduler)

        manager.lost_node(self.agent_2.agent_id)
        manager.register_agents([self.agent_3])
        manager.sync_with_database(self.scheduler)

        # Make sure two nodes are registered, one for agent 1 and one for agent 3, and both are online
        nodes = manager.get_nodes()
        self.assertEqual(len(nodes), 2)
        node_1 = manager.get_node(self.agent_1.agent_id)
        self.assertEqual(node_1.hostname, self.node_1.hostname)
        self.assertTrue(node_1._is_online)
        self.assertIsNone(manager.get_node(self.agent_2.agent_id))
        node_2 = manager.get_node(self.agent_3.agent_id)
        self.assertEqual(node_2.hostname, 'host_2')
        self.assertTrue(node_2._is_online)
        self.assertFalse(node_2._is_active)

    def test_get_pull_tasks(self):
        """Tests getting Docker pull tasks from the manager"""

        when = now()
        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)
        for node in manager.get_nodes():
            node._last_heath_task = when
            node._initial_cleanup_completed()
            node._update_state()

        tasks = manager.get_next_tasks(when)
        self.assertEqual(len(tasks), 2)
        for task in tasks:
            self.assertTrue(isinstance(task, PullTask))

    def test_pull_task_change_agent_id(self):
        """Tests the NodeManager where a node's agent ID changes during a pull task"""

        when = now()
        manager = NodeManager()
        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)
        for node in manager.get_nodes():
            node._last_heath_task = when
            node._initial_cleanup_completed()
            node._update_state()
        tasks = manager.get_next_tasks(when)

        task_mgr = TaskManager()
        task_2 = None
        for task in tasks:
            task_mgr.launch_tasks([task], when)
            if task.agent_id == self.agent_2.agent_id:
                task_2 = task

        # Node 2 changes agent ID to 3
        manager.lost_node(self.agent_2.agent_id)
        manager.register_agents([self.agent_3])
        manager.sync_with_database(self.scheduler)

        # Should get new Docker pull task for node 2
        tasks = manager.get_next_tasks(when)
        self.assertEqual(len(tasks), 1)
        new_task_2 = tasks[0]
        self.assertEqual(new_task_2.agent_id, self.agent_3.agent_id)

        # Task update comes back for original node 2 Docker pull task, manager should ignore with no exception
        update = job_test_utils.create_task_status_update(task_2.id, task_2.agent_id, TaskStatusUpdate.FAILED, when)
        task_mgr.handle_task_update(update)
        manager.handle_task_update(update)

    def test_get_initial_cleanup_tasks(self):
        """Tests getting initial cleanup tasks from the manager"""

        when = now()
        manager = NodeManager()
        tasks = manager.get_next_tasks(when)
        self.assertListEqual(tasks, [])  # No tasks yet due to no nodes

        manager.register_agents([self.agent_1, self.agent_2])
        manager.sync_with_database(self.scheduler)
        for node in manager.get_nodes():
            node._last_heath_task = when

        tasks = manager.get_next_tasks(when)
        self.assertEqual(len(tasks), 2)
        for task in tasks:
            self.assertTrue(task.is_initial_cleanup)

    def test_job_exe_clean_task(self):
        """Tests the NodeManager where a cleanup task is returned to clean up a job execution"""

        when = now()
        node_mgr = NodeManager()
        node_mgr.register_agents([self.agent_1, self.agent_2])
        node_mgr.sync_with_database(self.scheduler)
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
        self.assertEqual(task.agent_id, self.agent_1.agent_id)
        self.assertFalse(task.is_initial_cleanup)
        self.assertEqual(len(task.job_exes), 1)
