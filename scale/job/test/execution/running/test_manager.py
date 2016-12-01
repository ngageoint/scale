from __future__ import unicode_literals

import datetime
import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
from job.execution.running.job_exe import RunningJobExecution
from job.execution.running.manager import RunningJobExecutionManager
from job.execution.running.tasks.base_task import RECONCILIATION_THRESHOLD
from job.execution.running.tasks.update import TaskStatusUpdate


class TestRunningJobExecutionManager(TestCase):
    """Tests the RunningJobExecutionManager class"""

    def setUp(self):
        django.setup()

        self.job_exe_1 = job_test_utils.create_job_exe(status='RUNNING')
        self.job_exe_2 = job_test_utils.create_job_exe(status='RUNNING')
        self.job_exe_3 = job_test_utils.create_job_exe(status='RUNNING')
        self.job_exe_4 = job_test_utils.create_job_exe(status='RUNNING')

    def test_get_task_ids_for_reconciliation(self):
        """Tests calling RunningJobExecutionManager.get_task_ids_for_reconciliation() successfully"""

        running_job_exe_1 = RunningJobExecution(self.job_exe_1)
        task_1 = running_job_exe_1.start_next_task()
        running_job_exe_2 = RunningJobExecution(self.job_exe_2)
        task_2 = running_job_exe_2.start_next_task()
        running_job_exe_3 = RunningJobExecution(self.job_exe_3)
        task_3 = running_job_exe_3.start_next_task()
        running_job_exe_4 = RunningJobExecution(self.job_exe_4)
        running_job_exe_4.start_next_task()
        manager = RunningJobExecutionManager()
        manager.add_job_exes([running_job_exe_1, running_job_exe_2, running_job_exe_3, running_job_exe_4])

        task_1_and_2_launch_time = now()
        task_3_launch_time = task_1_and_2_launch_time + RECONCILIATION_THRESHOLD
        check_time = task_3_launch_time + datetime.timedelta(seconds=1)

        # Task 1 and 2 launch
        task_1.launch(task_1_and_2_launch_time)
        task_2.launch(task_1_and_2_launch_time)

        # The reconciliation threshold has now expired
        # Task 3 launches and a task update comes for task 2
        task_3.launch(task_3_launch_time)
        update = TaskStatusUpdate(task_2.id, 'agent_id', TaskStatusUpdate.RUNNING, task_3_launch_time)
        task_2.update(update)

        # A second later, we check for tasks needing reconciliation
        task_ids = manager.get_task_ids_for_reconciliation(check_time)

        # Task 1 was launched a while ago (exceeding threshold) so it should be reconciled
        # Task 2 received an update 1 second ago so it should not be reconciled
        # Task 3 was launched 1 second ago so it should not be reconciled
        # Task 4 did not even launch so it should not be reconciled
        self.assertListEqual(task_ids, [task_1.id])
