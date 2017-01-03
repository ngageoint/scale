from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
from job.execution.running.tasks.base_task import Task
from job.execution.running.tasks.update import TaskStatusUpdate
from job.resources import NodeResources


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
