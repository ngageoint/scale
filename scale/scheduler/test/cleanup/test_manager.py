from __future__ import unicode_literals

import django
from django.test import TestCase
from django.utils.timezone import now

from job.execution.job_exe import RunningJobExecution
from job.tasks.manager import TaskManager
from job.tasks.update import TaskStatusUpdate
from job.test import utils as job_test_utils
from node.test import utils as node_test_utils
from scheduler.cleanup.manager import CleanupManager
from scheduler.node.node_class import Node


class TestCleanupManager(TestCase):

    def setUp(self):
        django.setup()

        self.task_mgr = TaskManager()
        self.node_agent_1 = 'agent_1'
        self.node_agent_2 = 'agent_2'
        self.node_agent_3 = 'agent_3'
        self.node_1 = node_test_utils.create_node(hostname='host_1', slave_id=self.node_agent_1)
        self.node_2 = node_test_utils.create_node(hostname='host_2', slave_id=self.node_agent_2)
        self.job_exe_1 = job_test_utils.create_job_exe(node=self.node_1)

    def test_get_initial_cleanup_tasks(self):
        """Tests getting initial cleanup tasks from the manager"""

        manager = CleanupManager()
        tasks = manager.get_next_tasks()
        self.assertListEqual(tasks, [])  # No tasks yet due to no nodes

        node_1 = Node(self.node_agent_1, self.node_1)
        node_2 = Node(self.node_agent_2, self.node_2)
        manager.update_nodes([node_1, node_2])

        tasks = manager.get_next_tasks()
        self.assertEqual(len(tasks), 2)
        for task in tasks:
            self.assertTrue(task.is_initial_cleanup)

    def test_no_job_exes_to_clean(self):
        """Tests the NodeManager where no cleanup tasks are returned due to no job executions to clean"""

        manager = CleanupManager()
        node_1 = Node(self.node_agent_1, self.node_1)
        node_2 = Node(self.node_agent_2, self.node_2)
        manager.update_nodes([node_1, node_2])
        tasks = manager.get_next_tasks()

        # Complete initial cleanup tasks
        for task in tasks:
            self.task_mgr.launch_tasks([task], now())
            update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
            self.task_mgr.handle_task_update(update)
            manager.handle_task_update(update)

        tasks = manager.get_next_tasks()
        self.assertListEqual(tasks, [])  # No tasks since there are no job executions to clean up

    def test_change_agent_id(self):
        """Tests the NodeManager where a node's agent ID changes"""

        manager = CleanupManager()
        node_1 = Node(self.node_agent_1, self.node_1)
        node_2 = Node(self.node_agent_2, self.node_2)
        manager.update_nodes([node_1, node_2])
        tasks = manager.get_next_tasks()

        task_1 = None
        for task in tasks:
            self.task_mgr.launch_tasks([task], now())
            if task.agent_id == self.node_agent_1:
                task_1 = task

        # Node 1 changes agent ID
        node_1.update_from_mesos(agent_id=self.node_agent_3)
        manager.update_nodes([node_1, node_2])

        # Should get new initial cleanup task for node 1
        tasks = manager.get_next_tasks()
        self.assertEqual(len(tasks), 1)
        new_task_1 = tasks[0]
        self.assertEqual(new_task_1.agent_id, self.node_agent_3)

        # Task update comes back for original node 1 initial cleanup task, manager should ignore with no exception
        update = job_test_utils.create_task_status_update(task_1.id, task_1.agent_id, TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        manager.handle_task_update(update)

    def test_job_exe_clean_task(self):
        """Tests the NodeManager where a cleanup task is returned to clean up a job execution"""

        manager = CleanupManager()
        node_1 = Node(self.node_agent_1, self.node_1)
        node_2 = Node(self.node_agent_2, self.node_2)
        manager.update_nodes([node_1, node_2])
        tasks = manager.get_next_tasks()

        # Complete initial cleanup tasks
        for task in tasks:
            self.task_mgr.launch_tasks([task], now())
            update = job_test_utils.create_task_status_update(task.id, task.agent_id, TaskStatusUpdate.FINISHED, now())
            self.task_mgr.handle_task_update(update)
            manager.handle_task_update(update)

        # Add a job execution to clean up and get the cleanup task for it
        manager.add_job_execution(RunningJobExecution(self.job_exe_1))
        tasks = manager.get_next_tasks()
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task.agent_id, self.node_agent_1)
        self.assertFalse(task.is_initial_cleanup)
        self.assertEqual(len(task.job_exes), 1)
