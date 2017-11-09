from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
from job.tasks.base_task import Task, RUNNING_RECON_THRESHOLD
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


class TestTask(TestCase):
    """Tests the base Task class"""

    def setUp(self):
        django.setup()

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
        self.assertFalse(task.has_timed_out)

        # Check that launched (still staging) task is not timed out before threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = None
        task._staging_timeout_threshold = threshold
        task.launch(time_1)
        timed_out = task.check_timeout(time_before_threshold)
        self.assertFalse(timed_out)
        self.assertFalse(task.has_timed_out)

        # Check that launched (still staging) task is timed out after threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = None
        task._staging_timeout_threshold = threshold
        task.launch(time_1)
        timed_out = task.check_timeout(time_after_threshold)
        self.assertTrue(timed_out)
        self.assertTrue(task.has_timed_out)

        # Check that launched (still staging) task is not timed out if there is no threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = None
        task._staging_timeout_threshold = None
        task.launch(time_1)
        timed_out = task.check_timeout(time_after_threshold)
        self.assertFalse(timed_out)
        self.assertFalse(task.has_timed_out)

        # Check that running task is not timed out before threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = threshold
        task._staging_timeout_threshold = None
        task.launch(time_1)
        update = job_test_utils.create_task_status_update(task_id, agent_id, TaskStatusUpdate.RUNNING, time_1)
        task.update(update)
        timed_out = task.check_timeout(time_before_threshold)
        self.assertFalse(timed_out)
        self.assertFalse(task.has_timed_out)

        # Check that running task is timed out after threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = threshold
        task._staging_timeout_threshold = None
        task.launch(time_1)
        update = job_test_utils.create_task_status_update(task_id, agent_id, TaskStatusUpdate.RUNNING, time_1)
        task.update(update)
        timed_out = task.check_timeout(time_after_threshold)
        self.assertTrue(timed_out)
        self.assertTrue(task.has_timed_out)

        # Check that running task is not timed out if there is no threshold
        task = ImplementedTask(task_id, task_name, agent_id)
        task._running_timeout_threshold = None
        task._staging_timeout_threshold = None
        task.launch(time_1)
        update = job_test_utils.create_task_status_update(task_id, agent_id, TaskStatusUpdate.RUNNING, time_1)
        task.update(update)
        timed_out = task.check_timeout(time_after_threshold)
        self.assertFalse(timed_out)
        self.assertFalse(task.has_timed_out)

    def test_need_reconciliation(self):
        """Tests calling Task.need_reconciliation()"""

        task_1 = ImplementedTask('task_1', 'Task 1', 'agent_id')
        task_2 = ImplementedTask('task_2', 'Task 2', 'agent_id')
        task_3 = ImplementedTask('task_3', 'Task 3', 'agent_id')
        task_4 = ImplementedTask('task_4', 'Task 4', 'agent_id')
        task_5 = ImplementedTask('task_5', 'Task 5', 'agent_id')

        task_1_and_2_launch_time = now()
        task_3_and_5_launch_time = task_1_and_2_launch_time + RUNNING_RECON_THRESHOLD
        check_time = task_3_and_5_launch_time + datetime.timedelta(seconds=1)
        check_time_2 = check_time + datetime.timedelta(seconds=1)

        # Task 1 and 2 launch
        task_1.launch(task_1_and_2_launch_time)
        task_2.launch(task_1_and_2_launch_time)

        # The reconciliation threshold has now expired
        # Task 3 and 5 launches and a task update comes for task 2
        task_3.launch(task_3_and_5_launch_time)
        task_5.launch(task_3_and_5_launch_time)
        update = job_test_utils.create_task_status_update(task_2.id, 'agent_id', TaskStatusUpdate.RUNNING,
                                                          task_3_and_5_launch_time)
        task_2.update(update)

        # Task 5 gets force reconciliation call
        task_5.force_reconciliation()

        # A second later, we check for tasks needing reconciliation
        # Task 1 was launched a while ago (exceeding threshold) so it should be reconciled
        self.assertTrue(task_1.needs_reconciliation(check_time))
        # Task 2 received an update 1 second ago so it should not be reconciled
        self.assertFalse(task_2.needs_reconciliation(check_time))
        # Task 3 was launched 1 second ago so it should not be reconciled
        self.assertFalse(task_3.needs_reconciliation(check_time))
        # Task 4 did not even launch so it should not be reconciled
        self.assertFalse(task_4.needs_reconciliation(check_time))
        # Task 5 had force_reconciliation() called so it should be reconciled
        self.assertTrue(task_5.needs_reconciliation(check_time))

        # Task 5 gets task update to clear force recon
        update = job_test_utils.create_task_status_update(task_5.id, 'agent_id', TaskStatusUpdate.RUNNING,
                                                          check_time)
        task_5.update(update)
        # Task 5 received an update so force recon should be cleared and it should be not reconciled
        self.assertFalse(task_5.needs_reconciliation(check_time_2))

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
