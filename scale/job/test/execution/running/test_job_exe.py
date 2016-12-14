from __future__ import unicode_literals

from datetime import timedelta

import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
from error.models import Error, CACHED_BUILTIN_ERRORS
from job.execution.running.job_exe import RunningJobExecution
from job.execution.running.tasks.update import TaskStatusUpdate
from job.models import JobExecution
from scheduler.models import Scheduler


class TestRunningJobExecution(TestCase):
    """Tests the RunningJobExecution class"""

    fixtures = ['basic_errors.json', 'basic_job_errors.json']

    def setUp(self):
        django.setup()

        Scheduler.objects.initialize_scheduler()
        job_type = job_test_utils.create_job_type(max_tries=1)
        job = job_test_utils.create_job(job_type=job_type, num_exes=1)
        job_exe = job_test_utils.create_job_exe(job=job, status='RUNNING')
        self._job_exe_id = job_exe.id

    def test_successful_normal_job_execution(self):
        """Tests running through a normal job execution successfully"""

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)
        self.assertFalse(running_job_exe.is_finished())
        self.assertTrue(running_job_exe.is_next_task_ready())

        # Start pre-task
        task = running_job_exe.start_next_task()
        pre_task_id = task.id
        self.assertFalse(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Pre-task running
        pre_task_started = now() - timedelta(minutes=5)  # Lots of time so now() called at completion is in future
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        running_job_exe.task_update(update)
        self.assertFalse(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Pre-task sets updated command arguments
        updated_commands_args = '-arg updated'
        JobExecution.objects.filter(id=self._job_exe_id).update(command_arguments=updated_commands_args)

        # Complete pre-task
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed, exit_code=1)
        running_job_exe.task_update(update)
        self.assertFalse(running_job_exe.is_finished())
        self.assertTrue(running_job_exe.is_next_task_ready())

        # Start job-task
        task = running_job_exe.start_next_task()
        job_task_id = task.id
        self.assertEqual(task._command_arguments, updated_commands_args)  # Make sure job task has updated command args
        self.assertFalse(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Job-task running
        job_task_started = pre_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          job_task_started)
        running_job_exe.task_update(update)
        self.assertFalse(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Complete job-task
        job_task_completed = job_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          job_task_completed, exit_code=2)
        running_job_exe.task_update(update)
        self.assertFalse(running_job_exe.is_finished())
        self.assertTrue(running_job_exe.is_next_task_ready())

        # Start post-task
        task = running_job_exe.start_next_task()
        post_task_id = task.id
        self.assertFalse(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Post-task running
        post_task_started = job_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(post_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          post_task_started)
        running_job_exe.task_update(update)
        self.assertFalse(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Complete post-task
        post_task_completed = post_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(post_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          post_task_completed, exit_code=3)
        running_job_exe.task_update(update)
        self.assertTrue(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        job_exe = JobExecution.objects.get(id=self._job_exe_id)
        self.assertEqual(pre_task_started, job_exe.pre_started)
        self.assertEqual(pre_task_completed, job_exe.pre_completed)
        self.assertEqual(1, job_exe.pre_exit_code)
        self.assertEqual(job_task_started, job_exe.job_started)
        self.assertEqual(job_task_completed, job_exe.job_completed)
        self.assertEqual(2, job_exe.job_exit_code)
        self.assertEqual(post_task_started, job_exe.post_started)
        self.assertEqual(post_task_completed, job_exe.post_completed)
        self.assertEqual(3, job_exe.post_exit_code)
        self.assertEqual('COMPLETED', job_exe.status)
        self.assertGreater(job_exe.ended, post_task_completed)

    def test_failed_normal_job_execution(self):
        """Tests running through a normal job execution that fails"""

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)
        self.assertFalse(running_job_exe.is_finished())
        self.assertTrue(running_job_exe.is_next_task_ready())

        # Start pre-task
        task = running_job_exe.start_next_task()
        pre_task_id = task.id
        self.assertFalse(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Pre-task running
        pre_task_started = now() - timedelta(minutes=5)  # Lots of time so now() called at completion is in future
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        running_job_exe.task_update(update)
        self.assertFalse(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Fail pre-task
        pre_task_failed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FAILED,
                                                          pre_task_failed, exit_code=1)
        running_job_exe.task_update(update)
        self.assertTrue(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        job_exe = JobExecution.objects.get(id=self._job_exe_id)
        self.assertEqual(pre_task_started, job_exe.pre_started)
        self.assertEqual(pre_task_failed, job_exe.pre_completed)
        self.assertEqual(1, job_exe.pre_exit_code)
        self.assertEqual('FAILED', job_exe.status)
        self.assertIsNotNone(job_exe.error_id)
        self.assertGreater(job_exe.ended, pre_task_failed)

    def test_timed_out_job_execution(self):
        """Tests running through a job execution that times out"""

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)

        # Start, run, and complete pre-task
        task = running_job_exe.start_next_task()
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        running_job_exe.task_update(update)

        # Start job-task and then execution times out
        when_timed_out = pre_task_completed + timedelta(seconds=1)
        job_task = running_job_exe.start_next_task()
        timed_out_task = running_job_exe.execution_timed_out(when_timed_out)
        self.assertEqual(job_task.id, timed_out_task.id)
        self.assertTrue(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        job_exe = JobExecution.objects.get(id=self._job_exe_id)
        self.assertEqual('FAILED', job_exe.status)
        self.assertEqual(Error.objects.get_builtin_error('timeout').id, job_exe.error_id)
        self.assertEqual(when_timed_out, job_exe.ended)

    def test_lost_job_execution(self):
        """Tests running through a job execution that gets lost"""

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)

        # Start, run, and complete pre-task
        task = running_job_exe.start_next_task()
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        running_job_exe.task_update(update)

        # Start job-task and then execution gets lost
        when_lost = pre_task_completed + timedelta(seconds=1)
        job_task = running_job_exe.start_next_task()
        lost_task = running_job_exe.execution_lost(when_lost)
        self.assertEqual(job_task.id, lost_task.id)
        self.assertTrue(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        job_exe = JobExecution.objects.get(id=self._job_exe_id)
        self.assertEqual('FAILED', job_exe.status)
        self.assertEqual(Error.objects.get_builtin_error('node-lost').id, job_exe.error_id)
        self.assertEqual(when_lost, job_exe.ended)

    def test_lost_task(self):
        """Tests running through a job execution that has a task that gets lost"""

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)

        # Start, run, and complete pre-task
        task = running_job_exe.start_next_task()
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        running_job_exe.task_update(update)

        # Start job-task
        task = running_job_exe.start_next_task()
        job_task_id = task.id
        job_task_started = pre_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, job_task_started)
        running_job_exe.task_update(update)
        self.assertTrue(task.has_started)

        # Lose task and make sure the same task is the next one to schedule again
        when_lost = job_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.LOST, when_lost)
        running_job_exe.task_update(update)
        self.assertFalse(task.has_started)
        task = running_job_exe.start_next_task()
        self.assertEqual(job_task_id, task.id)

    def test_canceled_job_execution(self):
        """Tests running through a job execution that gets canceled"""

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)

        # Start, run, and complete pre-task
        task = running_job_exe.start_next_task()
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        running_job_exe.task_update(update)

        # Start job-task and then execution gets canceled
        job_task = running_job_exe.start_next_task()
        canceled_task = running_job_exe.execution_canceled()
        self.assertEqual(job_task.id, canceled_task.id)
        self.assertTrue(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

    def test_pre_task_launch_error(self):
        """Tests running through a job execution where a pre-task fails to launch"""

        # Clear error cache so test works correctly
        CACHED_BUILTIN_ERRORS.clear()

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)

        # Start pre-task
        task = running_job_exe.start_next_task()
        pre_task_id = task.id

        # Pre-task fails to launch
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FAILED, now())
        running_job_exe.task_update(update)

        # Check results
        job_exe = JobExecution.objects.select_related().get(id=self._job_exe_id)
        self.assertEqual(job_exe.status, 'FAILED')
        self.assertEqual(job_exe.error.name, 'docker-task-launch')

    def test_job_task_launch_error(self):
        """Tests running through a job execution where a Docker-based job-task fails to launch"""

        # Clear error cache so test works correctly
        CACHED_BUILTIN_ERRORS.clear()

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)

        # Start pre-task
        task = running_job_exe.start_next_task()
        pre_task_id = task.id

        # Pre-task running
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        running_job_exe.task_update(update)

        # Complete pre-task
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        running_job_exe.task_update(update)

        # Start job-task
        task = running_job_exe.start_next_task()
        job_task_id = task.id

        # Job-task fails to launch
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.FAILED, now())
        running_job_exe.task_update(update)

        # Check results
        job_exe = JobExecution.objects.select_related().get(id=self._job_exe_id)
        self.assertEqual(job_exe.status, 'FAILED')
        self.assertEqual(job_exe.error.name, 'docker-task-launch')

    def test_post_task_launch_error(self):
        """Tests running through a job execution where a post-task fails to launch"""

        # Clear error cache so test works correctly
        CACHED_BUILTIN_ERRORS.clear()

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)

        # Start pre-task
        task = running_job_exe.start_next_task()
        pre_task_id = task.id

        # Pre-task running
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        running_job_exe.task_update(update)

        # Complete pre-task
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        running_job_exe.task_update(update)

        # Start job-task
        task = running_job_exe.start_next_task()
        job_task_id = task.id

        # Job-task running
        job_task_started = now()
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          job_task_started)
        running_job_exe.task_update(update)

        # Complete job-task
        job_task_completed = job_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          job_task_completed)
        running_job_exe.task_update(update)

        # Start post-task
        task = running_job_exe.start_next_task()
        post_task_id = task.id

        # Post-task fails to launch
        update = job_test_utils.create_task_status_update(post_task_id, 'agent', TaskStatusUpdate.FAILED, now())
        running_job_exe.task_update(update)

        # Check results
        job_exe = JobExecution.objects.select_related().get(id=self._job_exe_id)
        self.assertEqual(job_exe.status, 'FAILED')
        self.assertEqual(job_exe.error.name, 'docker-task-launch')

    def test_general_algorithm_error(self):
        """Tests running through a job execution where the job-task has a general algorithm error (non-zero exit code)
        """

        # Clear error cache so test works correctly
        CACHED_BUILTIN_ERRORS.clear()

        job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(self._job_exe_id)
        running_job_exe = RunningJobExecution(job_exe)

        # Start pre-task
        task = running_job_exe.start_next_task()
        pre_task_id = task.id

        # Pre-task running
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        running_job_exe.task_update(update)

        # Complete pre-task
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        running_job_exe.task_update(update)

        # Start job-task
        task = running_job_exe.start_next_task()
        job_task_id = task.id

        # Job-task running
        job_task_started = now()
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          job_task_started)
        running_job_exe.task_update(update)

        # Fail job-task
        job_task_failed = job_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.FAILED,
                                                          job_task_failed, exit_code=1)
        running_job_exe.task_update(update)

        # Check results
        job_exe = JobExecution.objects.select_related().get(id=self._job_exe_id)
        self.assertEqual(job_exe.status, 'FAILED')
        self.assertEqual(job_exe.error.name, 'algorithm-unknown')
