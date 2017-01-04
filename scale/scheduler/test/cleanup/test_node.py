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


class TestNodeCleanup(TestCase):

    def setUp(self):
        django.setup()

        self.node_agent = 'agent_1'
        self.node = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent)
        self.job_exe = job_test_utils.create_job_exe(node=self.node)
        self.task_mgr = TaskManager()

    def test_handle_failed_task(self):
        """Tests handling failed cleanup task"""

        node = Node(self.node_agent, self.node)
        node_cleanup = NodeCleanup(node)
        # Get initial cleanup task
        task = node_cleanup.get_next_task()
        task_1_id = task.id
        self.assertIsNotNone(task)

        # Fail task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        task = node_cleanup.get_next_task()
        self.assertIsNotNone(task)
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node.is_initial_cleanup_completed)

    def test_handle_initial_cleanup_task(self):
        """Tests handling the initial cleanup task"""

        node = Node(self.node_agent, self.node)
        node_cleanup = NodeCleanup(node)

        # Get initial cleanup task
        task = node_cleanup.get_next_task()
        self.assertIsNotNone(task)
        self.assertTrue(task.is_initial_cleanup)
        self.assertEqual(task.agent_id, self.node_agent)

        # Schedule initial cleanup and make sure no new task is ready
        self.task_mgr.launch_tasks([task], now())
        self.assertIsNone(node_cleanup.get_next_task())
        self.assertFalse(node.is_initial_cleanup_completed)

        # Complete initial clean up, verify no new task
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        self.assertIsNone(node_cleanup.get_next_task())
        self.assertTrue(node.is_initial_cleanup_completed)

    def test_handle_killed_task(self):
        """Tests handling killed cleanup task"""

        node = Node(self.node_agent, self.node)
        node_cleanup = NodeCleanup(node)
        # Get initial cleanup task
        task = node_cleanup.get_next_task()
        task_1_id = task.id
        self.assertIsNotNone(task)

        # Kill task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.KILLED, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        task = node_cleanup.get_next_task()
        self.assertIsNotNone(task)
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node.is_initial_cleanup_completed)

    def test_handle_lost_tasks(self):
        """Tests handling lost cleanup tasks"""

        node = Node(self.node_agent, self.node)
        node_cleanup = NodeCleanup(node)
        # Get initial cleanup task
        task = node_cleanup.get_next_task()
        task_1_id = task.id
        self.assertIsNotNone(task)

        # Lose task without scheduling and get same task again
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        node_cleanup.handle_task_update(update)
        task = node_cleanup.get_next_task()
        self.assertIsNotNone(task)
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node.is_initial_cleanup_completed)

        # Lose task with scheduling and get same task again
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        task = node_cleanup.get_next_task()
        self.assertIsNotNone(task)
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node.is_initial_cleanup_completed)

        # Lose task after running and get same task again
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        task = node_cleanup.get_next_task()
        self.assertIsNotNone(task)
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node.is_initial_cleanup_completed)

    def test_handle_regular_cleanup_task(self):
        """Tests handling a regular cleanup task"""

        node = Node(self.node_agent, self.node)
        node.initial_cleanup_completed()
        node_cleanup = NodeCleanup(node)

        # No task since there are no job executions to clean
        self.assertIsNone(node_cleanup.get_next_task())

        # Add job execution and complete task to clean it up
        job_exe = RunningJobExecution(self.job_exe)
        node_cleanup.add_job_execution(job_exe)
        task = node_cleanup.get_next_task()
        self.assertIsNotNone(task)
        self.assertFalse(task.is_initial_cleanup)
        self.assertListEqual(task.job_exes, [job_exe])
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node_cleanup.handle_task_update(update)

        # No task since all job executions have been cleaned
        self.assertIsNone(node_cleanup.get_next_task())

    def test_paused_node(self):
        """Tests not returning tasks when its node is paused"""

        paused_node = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent)
        paused_node.is_paused = True
        node = Node(self.node_agent, paused_node)
        node_cleanup = NodeCleanup(node)
        task = node_cleanup.get_next_task()
        # No task due to paused node
        self.assertIsNone(task)
