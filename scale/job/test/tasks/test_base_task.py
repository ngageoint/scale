from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now
from job.tasks.base_task import Task

import job.test.utils as job_test_utils
from job.resources import NodeResources
from job.tasks.update import TaskStatusUpdate


# Non-abstract class to test implementation of base Task class
class ImplementedTask(Task):

    def get_resources(self):
        """Returns the resources that are required/have been scheduled for this task

        :returns: The scheduled resources for this task
        :rtype: :class:`job.resources.NodeResources`
        """

        return NodeResources()


class TestTask(TestCase):
    """Tests the base Task class"""

    def setUp(self):
        django.setup()

    def test_parsing_container_name(self):
        """Tests that a task successfully parses container name from a RUNNING task update"""

        task_id = 'task_1'
        task_name = 'My Task'
        agent_id = 'agent_1'
        container_name = 'container_1234'
        data = {'Config': {'Env': ['DUMMY_ENV=DUMMY', 'MESOS_CONTAINER_NAME=' + container_name]}}

        task = ImplementedTask(task_id, task_name, agent_id)
        update = job_test_utils.create_task_status_update(task_id, agent_id, TaskStatusUpdate.RUNNING, now(), data=data)
        task.update(update)

        self.assertEqual(task.container_name, container_name)

    def test_check_timeout(self):
        """Tests calling Task.check_timeout()"""

        task_id = 'task_1'
        task_name = 'My Task'
        agent_id = 'agent_1'
        time_1 = now()
        threshold = datetime.timedelta(minutes=30)
        time_before_threshold = time_1 + datetime.timedelta(minutes=15)
        time_after_threshold = time_1 + threshold + datetime.timedelta(minutes=1)

        # Check that new task is not timed out
        task = ImplementedTask(task_id, task_name, agent_id)
        timed_out = task.check_timeout(time_1)
        self.assertFalse(timed_out)
        self.assertFalse(task.has_ended)
        self.assertIsNone(task._ended)
        self.assertFalse(task._has_timed_out)

        # Check that launched (still staging) task is not timed out before threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = None
        task._staging_timeout_threshold = threshold
        task.launch(time_1)
        timed_out = task.check_timeout(time_before_threshold)
        self.assertFalse(timed_out)
        self.assertFalse(task.has_ended)
        self.assertIsNone(task._ended)
        self.assertFalse(task._has_timed_out)

        # Check that launched (still staging) task is timed out after threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = None
        task._staging_timeout_threshold = threshold
        task.launch(time_1)
        timed_out = task.check_timeout(time_after_threshold)
        self.assertTrue(timed_out)
        self.assertTrue(task.has_ended)
        self.assertEquals(task._ended, time_after_threshold)
        self.assertTrue(task._has_timed_out)

        # Check that launched (still staging) task is not timed out if there is no threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = None
        task._staging_timeout_threshold = None
        task.launch(time_1)
        timed_out = task.check_timeout(time_after_threshold)
        self.assertFalse(timed_out)
        self.assertFalse(task.has_ended)
        self.assertIsNone(task._ended)
        self.assertFalse(task._has_timed_out)

        # Check that running task is not timed out before threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = threshold
        task._staging_timeout_threshold = None
        task.launch(time_1)
        update = job_test_utils.create_task_status_update(task_id, agent_id, TaskStatusUpdate.RUNNING, time_1)
        task.update(update)
        timed_out = task.check_timeout(time_before_threshold)
        self.assertFalse(timed_out)
        self.assertFalse(task.has_ended)
        self.assertIsNone(task._ended)
        self.assertFalse(task._has_timed_out)

        # Check that running task is timed out after threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = threshold
        task._staging_timeout_threshold = None
        task.launch(time_1)
        update = job_test_utils.create_task_status_update(task_id, agent_id, TaskStatusUpdate.RUNNING, time_1)
        task.update(update)
        timed_out = task.check_timeout(time_after_threshold)
        self.assertTrue(timed_out)
        self.assertTrue(task.has_ended)
        self.assertEquals(task._ended, time_after_threshold)
        self.assertTrue(task._has_timed_out)

        # Check that running task is not timed out if there is no threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = None
        task._staging_timeout_threshold = None
        task.launch(time_1)
        update = job_test_utils.create_task_status_update(task_id, agent_id, TaskStatusUpdate.RUNNING, time_1)
        task.update(update)
        timed_out = task.check_timeout(time_after_threshold)
        self.assertFalse(timed_out)
        self.assertFalse(task.has_ended)
        self.assertIsNone(task._ended)
        self.assertFalse(task._has_timed_out)
