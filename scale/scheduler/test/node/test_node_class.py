from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

from job.execution.job_exe import RunningJobExecution
from job.tasks.manager import TaskManager
from job.tasks.update import TaskStatusUpdate
from job.test import utils as job_test_utils
from node.test import utils as node_test_utils
from scheduler.cleanup.node import NodeCleanup
from scheduler.node.node_class import Node


class TestNode(TestCase):

    def setUp(self):
        django.setup()

        self.node_agent = 'agent_1'
        self.node = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent)
        self.job_exe = job_test_utils.create_job_exe(node=self.node)
        self.task_mgr = TaskManager()

    def test_handle_failed_pull_task(self):
        """Tests handling failed Docker pull task"""

        node = Node(self.node_agent, self.node)
        node.initial_cleanup_completed()
        # Get Docker pull task
        task = node.get_next_task()
        task_1_id = task.id
        self.assertIsNotNone(task)

        # Fail task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_task()
        self.assertIsNotNone(task)
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

    def test_handle_successful_pull_task(self):
        """Tests handling the Docker pull task successfully"""

        node = Node(self.node_agent, self.node)
        node.initial_cleanup_completed()

        # Get Docker pull task
        task = node.get_next_task()
        self.assertIsNotNone(task)
        self.assertEqual(task.agent_id, self.node_agent)

        # Schedule pull task and make sure no new task is ready
        self.task_mgr.launch_tasks([task], now())
        self.assertIsNone(node.get_next_task())
        self.assertFalse(node._is_image_pulled)

        # Complete pull task, verify no new task
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        self.assertIsNone(node.get_next_task())
        self.assertTrue(node._is_image_pulled)
        # Node should now be ready
        self.assertEqual(node.READY, Node.READY)

    def test_handle_killed_pull_task(self):
        """Tests handling killed cleanup task"""

        node = Node(self.node_agent, self.node)
        node.initial_cleanup_completed()
        # Get pull task
        task = node.get_next_task()
        task_1_id = task.id
        self.assertIsNotNone(task)

        # Kill task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.KILLED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_task()
        self.assertIsNotNone(task)
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

    def test_handle_lost_pull_task(self):
        """Tests handling lost pull task"""

        node = Node(self.node_agent, self.node)
        node.initial_cleanup_completed()
        # Get pull task
        task = node.get_next_task()
        task_1_id = task.id
        self.assertIsNotNone(task)

        # Lose task without scheduling and get same task again
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        node.handle_task_update(update)
        task = node.get_next_task()
        self.assertIsNotNone(task)
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

        # Lose task with scheduling and get same task again
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_task()
        self.assertIsNotNone(task)
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

        # Lose task after running and get same task again
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_task()
        self.assertIsNotNone(task)
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

    def test_paused_node(self):
        """Tests not returning tasks when its node is paused"""

        paused_node = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent)
        paused_node.is_paused = True
        node = Node(self.node_agent, paused_node)
        node.initial_cleanup_completed()
        task = node.get_next_task()
        # No task due to paused node
        self.assertIsNone(task)

    def test_node_that_is_not_cleaned_yet(self):
        """Tests not returning tasks when the node hasn't been cleaned up yet"""

        node = Node(self.node_agent, self.node)
        task = node.get_next_task()
        # No task due to node not cleaned yet
        self.assertIsNone(task)
