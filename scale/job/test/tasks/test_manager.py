from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now
from job.tasks.base_task import Task

import job.test.utils as job_test_utils
from job.tasks.manager import TaskManager
from job.tasks.update import TaskStatusUpdate
from node.resources.node_resources import NodeResources


# Non-abstract class to test implementation of base Task class
class ImplementedTask(Task):

    def get_resources(self):
        """Returns the resources that are required/have been scheduled for this task

        :returns: The scheduled resources for this task
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        return NodeResources()


class TestTaskManager(TestCase):
    """Tests the TaskManager class"""

    def setUp(self):
        django.setup()

    def test_handle_task_update(self):
        """Tests calling TaskManager.handle_task_update()"""

        task_id = 'task_1'
        task_name = 'My Task'
        agent_id = 'agent_1'
        task_1 = ImplementedTask(task_id, task_name, agent_id)

        when_launched = now()
        manager = TaskManager()
        manager.launch_tasks([task_1], when_launched)

        when_finished = datetime.timedelta(seconds=1)
        update_1 = job_test_utils.create_task_status_update(task_1.id, task_1.agent_id, TaskStatusUpdate.FINISHED,
                                                            when=when_finished)
        manager.handle_task_update(update_1)

        self.assertTrue(task_1.has_ended)
        self.assertEqual(task_1._ended, when_finished)

        update_2 = job_test_utils.create_task_status_update('task_2', 'New Agent', TaskStatusUpdate.RUNNING, when=now())
        manager.handle_task_update(update_2)  # Should ignore, no error

    def test_launch_tasks(self):
        """Tests calling TaskManager.launch_tasks()"""

        task_id = 'task_1'
        task_name = 'My Task'
        agent_id = 'agent_1'
        task_1 = ImplementedTask(task_id, task_name, agent_id)

        task_id = 'task_2'
        task_name = 'My Task'
        agent_id = 'agent_1'
        task_2 = ImplementedTask(task_id, task_name, agent_id)

        task_id = 'task_3'
        task_name = 'My Task'
        agent_id = 'agent_2'
        task_3 = ImplementedTask(task_id, task_name, agent_id)

        when = now()
        manager = TaskManager()
        # Duplicate task_3 to test re-launching duplicate tasks
        manager.launch_tasks([task_1, task_2, task_3, task_3], when)

        self.assertTrue(task_1.has_been_launched)
        self.assertEqual(task_1._launched, when)
        self.assertTrue(task_2.has_been_launched)
        self.assertEqual(task_2._launched, when)
        self.assertTrue(task_3.has_been_launched)
        self.assertEqual(task_3._launched, when)
