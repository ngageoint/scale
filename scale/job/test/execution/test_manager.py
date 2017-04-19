from __future__ import unicode_literals

from datetime import timedelta

import django
from django.test import TransactionTestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
import node.test.utils as node_test_utils
from error.models import CACHED_BUILTIN_ERRORS
from job.execution.job_exe import RunningJobExecution
from job.execution.manager import JobExecutionManager
from job.models import JobExecution
from job.tasks.update import TaskStatusUpdate


class TestJobExecutionManager(TransactionTestCase):
    """Tests the JobExecutionManager class"""

    fixtures = ['basic_errors.json', 'basic_job_errors.json']

    def setUp(self):
        django.setup()

        # Clear error cache so test works correctly
        CACHED_BUILTIN_ERRORS.clear()

        self.node_model_1 = node_test_utils.create_node()
        self.job_exe_model_1 = job_test_utils.create_job_exe(status='RUNNING', node=self.node_model_1)
        self.job_exe_1 = RunningJobExecution(self.job_exe_model_1)
        self.node_model_2 = node_test_utils.create_node()
        self.job_exe_model_2 = job_test_utils.create_job_exe(status='RUNNING', node=self.node_model_2)
        self.job_exe_2 = RunningJobExecution(self.job_exe_model_2)

        self.job_exe_mgr = JobExecutionManager()

    def test_generate_status_json(self):
        """Tests calling generate_status_json() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2])
        json_dict = [{'id': self.node_model_1.id}, {'id': self.node_model_2.id}]
        self.job_exe_mgr.generate_status_json(json_dict)

        for node_dict in json_dict:
            self.assertEqual(node_dict['job_executions']['running']['total'], 1)

    def test_schedule_job_exes(self):
        """Tests calling schedule_job_exes() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2])

        # Both executions should be in the manager and ready
        self.assertEqual(len(self.job_exe_mgr.get_running_job_exes()), 2)
        self.assertEqual(len(self.job_exe_mgr.get_ready_job_exes()), 2)
        self.assertIsNotNone(self.job_exe_mgr.get_running_job_exe(self.job_exe_1.id))
        self.assertIsNotNone(self.job_exe_mgr.get_running_job_exe(self.job_exe_2.id))

    def test_handle_task_timeout(self):
        """Tests calling handle_task_timeout() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2])

        task = self.job_exe_1.start_next_task()
        self.job_exe_mgr.handle_task_timeout(task, now())

        self.assertEqual(self.job_exe_1.status, 'FAILED')

    def test_handle_task_update(self):
        """Tests calling handle_task_update() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2])

        # Start task
        task_1 = self.job_exe_1.start_next_task()
        task_1_started = now() - timedelta(minutes=5)
        update = job_test_utils.create_task_status_update(task_1.id, 'agent', TaskStatusUpdate.RUNNING, task_1_started)

        # Job execution is not finished, so None should be returned
        result = self.job_exe_mgr.handle_task_update(update)
        self.assertIsNone(result)

        # Fail task
        task_1_failed = task_1_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task_1.id, 'agent', TaskStatusUpdate.FAILED, task_1_failed,
                                                          exit_code=1)

        # Job execution is finished, so it should be returned
        result = self.job_exe_mgr.handle_task_update(update)
        self.assertEqual(self.job_exe_1.id, result.id)

    def test_init_with_database(self):
        """Tests calling init_with_database() successfully"""

        self.job_exe_mgr.init_with_database()

    def test_lost_node(self):
        """Tests calling lost_node() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2])

        task_1 = self.job_exe_1.start_next_task()
        task_1_started = now() - timedelta(minutes=5)
        update = job_test_utils.create_task_status_update(task_1.id, 'agent', TaskStatusUpdate.RUNNING, task_1_started)
        self.job_exe_mgr.handle_task_update(update)

        lost_job_exe = self.job_exe_mgr.lost_node(self.node_model_1.id, now())[0]
        self.assertEqual(lost_job_exe.id, self.job_exe_1.id)
        self.assertEqual(lost_job_exe.status, 'FAILED')
        self.assertEqual(lost_job_exe._error.name, 'node-lost')

    def test_sync_with_database(self):
        """Tests calling sync_with_database() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2])

        task_1 = self.job_exe_1.start_next_task()
        task_1_started = now() - timedelta(minutes=5)
        update = job_test_utils.create_task_status_update(task_1.id, 'agent', TaskStatusUpdate.RUNNING, task_1_started)
        self.job_exe_mgr.handle_task_update(update)

        # Cancel job_exe_1 and have manager sync with database
        JobExecution.objects.update_status([self.job_exe_model_1], 'CANCELED', now())
        tasks_to_kill = self.job_exe_mgr.sync_with_database()

        self.assertEqual(self.job_exe_1.status, 'CANCELED')
        self.assertEqual(len(tasks_to_kill), 1)
        self.assertEqual(tasks_to_kill[0].id, task_1.id)
