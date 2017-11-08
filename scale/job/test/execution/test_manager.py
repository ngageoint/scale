from __future__ import unicode_literals

from datetime import timedelta

import django
from django.test import TransactionTestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
import node.test.utils as node_test_utils
from error.models import reset_error_cache
from job.execution.manager import JobExecutionManager
from job.messages.job_exe_end import MAX_NUM
from job.models import Job
from job.tasks.update import TaskStatusUpdate


class TestJobExecutionManager(TransactionTestCase):
    """Tests the JobExecutionManager class"""

    fixtures = ['basic_errors.json', 'basic_job_errors.json']

    def setUp(self):
        django.setup()

        # Clear error cache so tests work correctly
        reset_error_cache()

        self.agent_id = 'agent'
        self.node_model_1 = node_test_utils.create_node()
        self.job_exe_1 = job_test_utils.create_running_job_exe(agent_id=self.agent_id, node=self.node_model_1)
        self.node_model_2 = node_test_utils.create_node()
        self.job_exe_2 = job_test_utils.create_running_job_exe(agent_id=self.agent_id, node=self.node_model_2)

        self.job_exe_mgr = JobExecutionManager()

    def test_generate_status_json(self):
        """Tests calling generate_status_json() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2], [])
        json_dict = [{'id': self.node_model_1.id}, {'id': self.node_model_2.id}]
        self.job_exe_mgr.generate_status_json(json_dict, now())

        for node_dict in json_dict:
            self.assertEqual(node_dict['job_executions']['running']['total'], 1)

    def test_get_messages_for_canceled_job_exes(self):
        """Tests calling get_messages() successfully when canceled job_exes have been added"""

        job_exe_ends = []
        for _ in range(int(MAX_NUM * 2.5)):  # Should result in 3 messages
            job_exe = job_test_utils.create_job_exe()
            job_exe_ends.append(job_exe.create_canceled_job_exe_end_model(now()))

        self.job_exe_mgr.add_canceled_job_exes(job_exe_ends)
        messages = self.job_exe_mgr.get_messages()

        self.assertEqual(len(messages), 3)

    def test_handle_task_timeout(self):
        """Tests calling handle_task_timeout() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2], [])

        task = self.job_exe_1.start_next_task()
        self.job_exe_mgr.handle_task_timeout(task, now())

        self.assertEqual(self.job_exe_1.status, 'FAILED')

    def test_handle_task_update(self):
        """Tests calling handle_task_update() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2], [])

        # Start task
        task_1 = self.job_exe_1.start_next_task()
        task_1_started = now() - timedelta(minutes=5)
        update = job_test_utils.create_task_status_update(task_1.id, 'agent', TaskStatusUpdate.RUNNING, task_1_started)

        # Job execution is not finished, so None should be returned and no message is available
        result = self.job_exe_mgr.handle_task_update(update)
        self.assertIsNone(result)
        self.assertListEqual(self.job_exe_mgr.get_messages(), [])

        # Fail task
        task_1_failed = task_1_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task_1.id, 'agent', TaskStatusUpdate.FAILED, task_1_failed,
                                                          exit_code=1)

        # Job execution is finished, so it should be returned and a create_job_exe_ends message and a failed_jobs
        # message is available
        result = self.job_exe_mgr.handle_task_update(update)
        self.assertEqual(self.job_exe_1.id, result.id)

        messages = self.job_exe_mgr.get_messages()
        self.assertEqual(len(messages), 2)
        job_exe_ends_msg = messages[0]
        self.assertEqual(job_exe_ends_msg.type, 'create_job_exe_ends')
        self.assertEqual(job_exe_ends_msg._job_exe_ends[0].job_exe_id, self.job_exe_1.id)
        failed_jobs_msg = messages[1]
        self.assertEqual(failed_jobs_msg.type, 'failed_jobs')
        self.assertEqual(failed_jobs_msg._failed_jobs.values()[0][0].job_id, self.job_exe_1.job_id)

    def test_init_with_database(self):
        """Tests calling init_with_database() successfully"""

        self.job_exe_mgr.init_with_database()

    def test_lost_node(self):
        """Tests calling lost_node() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2], [])

        task_1 = self.job_exe_1.start_next_task()
        task_1_started = now() - timedelta(minutes=5)
        update = job_test_utils.create_task_status_update(task_1.id, 'agent', TaskStatusUpdate.RUNNING, task_1_started)
        self.job_exe_mgr.handle_task_update(update)

        lost_job_exe = self.job_exe_mgr.lost_node(self.node_model_1.id, now())[0]
        self.assertEqual(lost_job_exe.id, self.job_exe_1.id)
        self.assertEqual(lost_job_exe.status, 'FAILED')
        self.assertEqual(lost_job_exe._error.name, 'node-lost')
        # Make sure a create_job_exe_ends message exists for the lost job execution
        message = self.job_exe_mgr.get_messages()[0]
        self.assertEqual(message.type, 'create_job_exe_ends')
        self.assertEqual(message._job_exe_ends[0].job_exe_id, lost_job_exe.id)

    def test_schedule_job_exes(self):
        """Tests calling schedule_job_exes() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2], [])

        # Both executions should be in the manager and ready
        self.assertEqual(len(self.job_exe_mgr.get_running_job_exes()), 2)
        self.assertIsNotNone(self.job_exe_mgr.get_running_job_exe(self.job_exe_1.cluster_id))
        self.assertIsNotNone(self.job_exe_mgr.get_running_job_exe(self.job_exe_2.cluster_id))

    def test_sync_with_database(self):
        """Tests calling sync_with_database() successfully"""

        self.job_exe_mgr.schedule_job_exes([self.job_exe_1, self.job_exe_2], [])

        task_1 = self.job_exe_1.start_next_task()
        task_1_started = now() - timedelta(minutes=5)
        update = job_test_utils.create_task_status_update(task_1.id, 'agent', TaskStatusUpdate.RUNNING, task_1_started)
        self.job_exe_mgr.handle_task_update(update)

        # Cancel job_exe_1 and have manager sync with database
        Job.objects.update_jobs_to_canceled([self.job_exe_1.job_id], now())
        tasks_to_kill = self.job_exe_mgr.sync_with_database()

        self.assertEqual(self.job_exe_1.status, 'CANCELED')
        self.assertEqual(len(tasks_to_kill), 1)
        self.assertEqual(tasks_to_kill[0].id, task_1.id)
        # No message yet since we wait for the canceled task to be killed
        self.assertListEqual(self.job_exe_mgr.get_messages(), [])

        # Task killed
        task_1_killed = task_1_started + timedelta(minutes=5)
        update = job_test_utils.create_task_status_update(task_1.id, 'agent', TaskStatusUpdate.KILLED, task_1_killed)
        self.job_exe_mgr.handle_task_update(update)

        # Make sure a create_job_exe_ends message exists for the canceled job execution
        message = self.job_exe_mgr.get_messages()[0]
        self.assertEqual(message.type, 'create_job_exe_ends')
        self.assertEqual(message._job_exe_ends[0].job_exe_id, self.job_exe_1.id)
