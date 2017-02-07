from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now

from job.execution.job_exe import RunningJobExecution
from job.execution.tasks.cleanup_task import CLEANUP_TASK_ID_PREFIX
from job.tasks.manager import TaskManager
from job.tasks.pull_task import PULL_TASK_ID_PREFIX
from job.tasks.update import TaskStatusUpdate
from job.test import utils as job_test_utils
from node.test import utils as node_test_utils
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

        when = now()
        node = Node(self.node_agent, self.node)
        node._initial_cleanup_completed()
        node._update_state()
        # Get Docker pull task
        task = node.get_next_tasks(when)[0]
        task_1_id = task.id
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))

        # Fail task after running
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # No new pull task right away
        tasks = node.get_next_tasks(when + datetime.timedelta(seconds=5))
        self.assertListEqual([], tasks)
        self.assertFalse(node._is_image_pulled)

        # After error threshold, we should get new pull task
        task = node.get_next_tasks(when + Node.IMAGE_PULL_ERR_THRESHOLD + datetime.timedelta(seconds=5))[0]
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))

    def test_handle_successful_pull_task(self):
        """Tests handling the Docker pull task successfully"""

        when = now()
        node = Node(self.node_agent, self.node)
        node._initial_cleanup_completed()
        node._update_state()

        # Get Docker pull task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        self.assertEqual(task.agent_id, self.node_agent)

        # Schedule pull task and make sure no new task is ready
        self.task_mgr.launch_tasks([task], now())
        self.assertListEqual([], node.get_next_tasks(when))
        self.assertFalse(node._is_image_pulled)

        # Complete pull task, verify no new task
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        self.assertListEqual([], node.get_next_tasks(when))
        self.assertTrue(node._is_image_pulled)
        # Node should now be ready
        self.assertEqual(node.READY, Node.READY)

    def test_handle_killed_pull_task(self):
        """Tests handling killed cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node)
        node._initial_cleanup_completed()
        node._update_state()
        # Get pull task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        task_1_id = task.id

        # Kill task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.KILLED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

    def test_handle_lost_pull_task(self):
        """Tests handling lost pull task"""

        when = now()
        node = Node(self.node_agent, self.node)
        node._initial_cleanup_completed()
        node._update_state()
        # Get pull task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        task_1_id = task.id
        self.assertIsNotNone(task)

        # Lose task without scheduling and get same task again
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

        # Lose task with scheduling and get same task again
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
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
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(PULL_TASK_ID_PREFIX))
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node._is_image_pulled)

    def test_paused_node_pull_task(self):
        """Tests not returning pull task when its node is paused"""

        when = now()
        paused_node = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent)
        paused_node.is_paused = True
        node = Node(self.node_agent, paused_node)
        node._initial_cleanup_completed()
        node._update_state()
        tasks = node.get_next_tasks(when)
        # No task due to paused node
        self.assertListEqual([], tasks)

    def test_node_that_is_not_cleaned_yet_no_pull_task(self):
        """Tests not returning pull task when the node hasn't been cleaned up yet"""

        when = now()
        node = Node(self.node_agent, self.node)
        tasks = node.get_next_tasks(when)
        # No pull task due to node not cleaned yet
        for task in tasks:
            self.assertFalse(task.id.startswith(PULL_TASK_ID_PREFIX))

    def test_handle_failed_cleanup_task(self):
        """Tests handling failed cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node)
        # Get initial cleanup task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        task_1_id = task.id

        # Fail task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # No new cleanup task right away
        tasks = node.get_next_tasks(when + datetime.timedelta(seconds=5))
        self.assertListEqual([], tasks)
        self.assertFalse(node._is_initial_cleanup_completed)

        # After error threshold, we should get new cleanup task
        task = node.get_next_tasks(when + Node.CLEANUP_ERR_THRESHOLD + datetime.timedelta(seconds=5))[0]
        self.assertNotEqual(task.id, task_1_id)
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))

    def test_handle_initial_cleanup_task(self):
        """Tests handling the initial cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node)

        # Get initial cleanup task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertTrue(task.is_initial_cleanup)
        self.assertEqual(task.agent_id, self.node_agent)

        # Schedule initial cleanup and make sure no new task is ready
        self.task_mgr.launch_tasks([task], now())
        self.assertListEqual([], node.get_next_tasks(when))
        self.assertFalse(node._is_initial_cleanup_completed)

        # Complete initial clean up, verify no new cleanup task
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        for task in node.get_next_tasks(when):
            self.assertFalse(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertTrue(node._is_initial_cleanup_completed)

    def test_handle_killed_cleanup_task(self):
        """Tests handling killed cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node)
        # Get initial cleanup task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        task_1_id = task.id

        # Kill task after running and get different task next time
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.KILLED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertNotEqual(task.id, task_1_id)
        self.assertFalse(node._is_initial_cleanup_completed)

    def test_handle_lost_cleanup_tasks(self):
        """Tests handling lost cleanup tasks"""

        when = now()
        node = Node(self.node_agent, self.node)
        # Get initial cleanup task
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        task_1_id = task.id

        # Lose task without scheduling and get same task again
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node._is_initial_cleanup_completed)

        # Lose task with scheduling and get same task again
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node._is_initial_cleanup_completed)

        # Lose task after running and get same task again
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertEqual(task.id, task_1_id)
        self.assertFalse(node._is_initial_cleanup_completed)

    def test_handle_regular_cleanup_task(self):
        """Tests handling a regular cleanup task"""

        when = now()
        node = Node(self.node_agent, self.node)
        node._initial_cleanup_completed()
        node._image_pull_completed()
        node._update_state()

        # No task since there are no job executions to clean
        self.assertListEqual([], node.get_next_tasks(when))

        # Add job execution and complete task to clean it up
        job_exe = RunningJobExecution(self.job_exe)
        node.add_job_execution(job_exe)
        task = node.get_next_tasks(when)[0]
        self.assertTrue(task.id.startswith(CLEANUP_TASK_ID_PREFIX))
        self.assertFalse(task.is_initial_cleanup)
        self.assertListEqual(task.job_exes, [job_exe])
        self.task_mgr.launch_tasks([task], now())
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.RUNNING, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)
        update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
        self.task_mgr.handle_task_update(update)
        node.handle_task_update(update)

        # No task since all job executions have been cleaned
        self.assertListEqual([], node.get_next_tasks(when))

    def test_paused_node_cleanup_task(self):
        """Tests not returning cleanup task when its node is paused"""

        paused_node = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent)
        paused_node.is_paused = True
        node = Node(self.node_agent, paused_node)
        # No task due to paused node
        self.assertListEqual([], node.get_next_tasks(now()))
