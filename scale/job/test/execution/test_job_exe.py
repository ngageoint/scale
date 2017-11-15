from __future__ import unicode_literals

from datetime import timedelta

import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
from error.models import reset_error_cache
from job.tasks.manager import TaskManager
from job.tasks.update import TaskStatusUpdate
from scheduler.models import Scheduler
from util.parse import datetime_to_string


class TestRunningJobExecution(TestCase):
    """Tests the RunningJobExecution class"""

    fixtures = ['basic_errors.json', 'basic_job_errors.json']

    def setUp(self):
        django.setup()

        reset_error_cache()

        Scheduler.objects.initialize_scheduler()
        job_type = job_test_utils.create_job_type(max_tries=1)
        job = job_test_utils.create_job(job_type=job_type, num_exes=1)
        self.agent_id = 'agent'
        self.running_job_exe = job_test_utils.create_running_job_exe(agent_id=self.agent_id, job=job)

        self.task_mgr = TaskManager()

    def test_successful_normal_job_execution(self):
        """Tests running through a normal job execution successfully"""

        self.assertFalse(self.running_job_exe.is_finished())
        self.assertTrue(self.running_job_exe.is_next_task_ready())

        # Start pull-task
        task = self.running_job_exe.start_next_task()
        pull_task_launch = now()
        self.task_mgr.launch_tasks([task], pull_task_launch)
        pull_task_id = task.id
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Pull-task running
        # Lots of time so now() called at completion is in future
        pull_task_started = pull_task_launch - timedelta(minutes=5)
        update = job_test_utils.create_task_status_update(pull_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Complete pull-task
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pull_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed, exit_code=0)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertTrue(self.running_job_exe.is_next_task_ready())

        # Start pre-task
        task = self.running_job_exe.start_next_task()
        pre_task_launch = pull_task_completed + timedelta(seconds=1)
        self.task_mgr.launch_tasks([task], pre_task_launch)
        pre_task_id = task.id
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Pre-task running
        pre_task_started = pre_task_launch + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Complete pre-task
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed, exit_code=1)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertTrue(self.running_job_exe.is_next_task_ready())

        # Start job-task
        task = self.running_job_exe.start_next_task()
        job_task_launch = pre_task_completed + timedelta(seconds=1)
        self.task_mgr.launch_tasks([task], job_task_launch)
        job_task_id = task.id
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Job-task running
        job_task_started = job_task_launch + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          job_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Complete job-task
        job_task_completed = job_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          job_task_completed, exit_code=2)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertTrue(self.running_job_exe.is_next_task_ready())

        # Start post-task
        task = self.running_job_exe.start_next_task()
        post_task_launch = job_task_completed + timedelta(seconds=1)
        self.task_mgr.launch_tasks([task], post_task_launch)
        post_task_id = task.id
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Post-task running
        post_task_started = post_task_launch + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(post_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          post_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Complete post-task
        post_task_completed = post_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(post_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          post_task_completed, exit_code=3)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'COMPLETED')
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        job_exe_end = self.running_job_exe.create_job_exe_end_model()
        self.assertEqual(job_exe_end.status, 'COMPLETED')
        expected_task_results = {'version': '1.0',
                                 'tasks': [{'task_id': pull_task_id, 'type': 'pull', 'was_launched': True,
                                            str('launched'): datetime_to_string(pull_task_launch),
                                            str('was_started'): True,
                                            str('started'): datetime_to_string(pull_task_started),
                                            str('was_timed_out'): False,
                                            str('ended'): datetime_to_string(pull_task_completed),
                                            str('status'): 'FINISHED', str('exit_code'): 0},
                                           {'task_id': pre_task_id, 'type': 'pre', 'was_launched': True,
                                            str('launched'): datetime_to_string(pre_task_launch),
                                            str('was_started'): True,
                                            str('started'): datetime_to_string(pre_task_started),
                                            str('was_timed_out'): False,
                                            str('ended'): datetime_to_string(pre_task_completed),
                                            str('status'): 'FINISHED', str('exit_code'): 1},
                                           {'task_id': job_task_id, 'type': 'main', 'was_launched': True,
                                            str('launched'): datetime_to_string(job_task_launch),
                                            str('was_started'): True,
                                            str('started'): datetime_to_string(job_task_started),
                                            str('was_timed_out'): False,
                                            str('ended'): datetime_to_string(job_task_completed),
                                            str('status'): 'FINISHED', str('exit_code'): 2},
                                           {'task_id': post_task_id, 'type': 'post', 'was_launched': True,
                                            str('launched'): datetime_to_string(post_task_launch),
                                            str('was_started'): True,
                                            str('started'): datetime_to_string(post_task_started),
                                            str('was_timed_out'): False,
                                            str('ended'): datetime_to_string(post_task_completed),
                                            str('status'): 'FINISHED', str('exit_code'): 3}]}
        self.assertDictEqual(job_exe_end.get_task_results().get_dict(), expected_task_results)

    def test_failed_normal_job_execution(self):
        """Tests running through a normal job execution that fails with an unknown error"""

        self.assertFalse(self.running_job_exe.is_finished())
        self.assertTrue(self.running_job_exe.is_next_task_ready())

        # Start pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_id = task.id
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Pull-task running
        pull_task_started = now() - timedelta(minutes=5)  # Lots of time so now() called at completion is in future
        update = job_test_utils.create_task_status_update(pull_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Complete pull-task
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pull_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertTrue(self.running_job_exe.is_next_task_ready())

        # Start pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_id = task.id
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Pre-task running
        pre_task_started = pull_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Fail pre-task
        pre_task_failed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FAILED,
                                                          pre_task_failed, exit_code=1)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'unknown')
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_timed_out_launch(self):
        """Tests running through a job execution where a task launch times out"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start, run, and complete pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Launch job-task and then times out
        when_launched = pre_task_completed + timedelta(seconds=1)
        when_timed_out = when_launched + timedelta(seconds=1)
        job_task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([job_task], when_launched)
        self.running_job_exe.execution_timed_out(job_task, when_timed_out)
        self.assertFalse(self.running_job_exe.is_finished())  # Not finished until killed or lost task update arrives
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'launch-timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Lost task update arrives
        when_lost = when_timed_out + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.LOST, when_lost)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'launch-timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_timed_out_pull_task(self):
        """Tests running through a job execution where the pull task times out"""

        # Start pull-task and then task times out
        when_launched = now()
        pull_task_started = when_launched + timedelta(seconds=1)
        when_timed_out = pull_task_started + timedelta(seconds=1)
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], when_launched)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.running_job_exe.execution_timed_out(task, when_timed_out)
        self.assertFalse(self.running_job_exe.is_finished())  # Not finished until killed task update arrives
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'pull-timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Killed task update arrives
        pull_task_kill = when_timed_out + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.KILLED, pull_task_kill)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'pull-timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_timed_out_pre_task(self):
        """Tests running through a job execution where the pre task times out"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start pre-task and then task times out
        when_launched = pull_task_completed + timedelta(seconds=1)
        pre_task_started = when_launched + timedelta(seconds=1)
        when_timed_out = pre_task_started + timedelta(seconds=1)
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], when_launched)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.running_job_exe.execution_timed_out(task, when_timed_out)
        self.assertFalse(self.running_job_exe.is_finished())  # Not finished until killed task update arrives
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'pre-timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Killed task update arrives
        pre_task_kill = when_timed_out + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.KILLED, pre_task_kill)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'pre-timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_timed_out_job_task(self):
        """Tests running through a job execution where the job task times out"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start, run, and complete pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_started = pull_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start job-task and then task times out
        when_launched = pre_task_completed + timedelta(seconds=1)
        job_task_started = when_launched + timedelta(seconds=1)
        when_timed_out = job_task_started + timedelta(seconds=1)
        job_task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([job_task], when_launched)
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.RUNNING,
                                                          job_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.running_job_exe.execution_timed_out(job_task, when_timed_out)
        self.assertFalse(self.running_job_exe.is_finished())  # Not finished until killed task update arrives
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'ALGORITHM')
        self.assertEqual(self.running_job_exe.error.name, 'timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Killed task update arrives
        job_task_kill = when_timed_out + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.KILLED, job_task_kill)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'ALGORITHM')
        self.assertEqual(self.running_job_exe.error.name, 'timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_timed_out_system_job_task(self):
        """Tests running through a job execution where a system job task times out"""

        job_type = job_test_utils.create_job_type(max_tries=1)
        job_type.is_system = True
        job_type.save()
        job = job_test_utils.create_job(job_type=job_type, num_exes=1)
        running_job_exe = job_test_utils.create_running_job_exe(self.agent_id, job=job)

        # Start job-task and then task times out
        when_launched = now() + timedelta(seconds=1)
        job_task_started = when_launched + timedelta(seconds=1)
        when_timed_out = job_task_started + timedelta(seconds=1)
        job_task = running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([job_task], when_launched)
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.RUNNING,
                                                          job_task_started)
        self.task_mgr.handle_task_update(update)
        running_job_exe.task_update(update)
        running_job_exe.execution_timed_out(job_task, when_timed_out)
        self.assertFalse(running_job_exe.is_finished())  # Not finished until killed task update returns
        self.assertEqual(running_job_exe.status, 'FAILED')
        self.assertEqual(running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(running_job_exe.error.name, 'system-timeout')
        self.assertEqual(running_job_exe.finished, when_timed_out)
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Killed task update arrives
        job_task_kill = when_timed_out + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.KILLED, job_task_kill)
        self.task_mgr.handle_task_update(update)
        running_job_exe.task_update(update)
        self.assertTrue(running_job_exe.is_finished())
        self.assertEqual(running_job_exe.status, 'FAILED')
        self.assertEqual(running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(running_job_exe.error.name, 'system-timeout')
        self.assertEqual(running_job_exe.finished, when_timed_out)
        self.assertFalse(running_job_exe.is_next_task_ready())

    def test_timed_out_post_task(self):
        """Tests running through a job execution where the post task times out"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start, run, and complete pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_started = pull_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start, run, and complete job-task
        when_launched = pre_task_completed + timedelta(seconds=1)
        job_task_started = when_launched + timedelta(seconds=1)
        job_task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([job_task], when_launched)
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.RUNNING,
                                                          job_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        job_task_completed = job_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          job_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start post-task and then task times out
        when_launched = job_task_completed + timedelta(seconds=1)
        post_task_started = when_launched + timedelta(seconds=1)
        when_timed_out = post_task_started + timedelta(seconds=1)
        post_task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([post_task], when_launched)
        update = job_test_utils.create_task_status_update(post_task.id, 'agent', TaskStatusUpdate.RUNNING,
                                                          post_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.running_job_exe.execution_timed_out(post_task, when_timed_out)
        self.assertFalse(self.running_job_exe.is_finished())  # Not finished until killed task update arrives
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'post-timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Killed task update arrives
        post_task_kill = when_timed_out + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(post_task.id, 'agent', TaskStatusUpdate.KILLED,
                                                          post_task_kill)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'post-timeout')
        self.assertEqual(self.running_job_exe.finished, when_timed_out)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_lost_job_execution(self):
        """Tests running through a job execution that gets lost"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start, run, and complete pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_started = pull_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start job-task and then execution gets lost
        when_lost = pre_task_completed + timedelta(seconds=1)
        job_task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([job_task], now())
        self.running_job_exe.execution_lost(when_lost)
        self.assertFalse(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'node-lost')
        self.assertEqual(self.running_job_exe.finished, when_lost)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Task update comes back for lost task
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.LOST, now())
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(self.running_job_exe.is_finished())

    def test_lost_task(self):
        """Tests running through a job execution that has a task that gets lost"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start, run, and complete pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_started = pull_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start job-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        job_task_id = task.id
        job_task_started = pre_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, job_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(task.has_started)

        # Lose task and make sure the "same" task is the next one to schedule again with a new ID this time
        when_lost = job_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.LOST, when_lost)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertFalse(task.has_started)
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        self.assertTrue(task.id.startswith(job_task_id))
        self.assertNotEqual(job_task_id, task.id)

    def test_canceled_job_execution(self):
        """Tests running through a job execution that gets canceled"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start, run, and complete pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_started = pull_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start job-task and then execution gets canceled
        job_task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([job_task], now())
        when_canceled = pre_task_completed + timedelta(seconds=1)
        self.running_job_exe.execution_canceled(when_canceled)
        self.assertTrue(job_task.needs_killed())
        self.assertFalse(self.running_job_exe.is_finished())  # Not finished until killed task update arrives
        self.assertEqual(self.running_job_exe.status, 'CANCELED')
        self.assertEqual(self.running_job_exe.finished, when_canceled)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

        # Killed task update arrives
        when_task_kill = when_canceled + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.KILLED, when_task_kill)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'CANCELED')
        self.assertEqual(self.running_job_exe.finished, when_canceled)
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_pre_task_launch_error(self):
        """Tests running through a job execution where a pre-task fails to launch"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_id = task.id

        # Pre-task fails to launch
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Check results
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'docker-task-launch')
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_job_task_launch_error(self):
        """Tests running through a job execution where a Docker-based job-task fails to launch"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_id = task.id

        # Pre-task running
        pre_task_started = pull_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Complete pre-task
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start job-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        job_task_id = task.id

        # Job-task fails to launch
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Check results
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'docker-task-launch')
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_post_task_launch_error(self):
        """Tests running through a job execution where a post-task fails to launch"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_id = task.id

        # Pre-task running
        pre_task_started = pull_task_completed + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Complete pre-task
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start job-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        job_task_id = task.id

        # Job-task running
        job_task_started = now()
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          job_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Complete job-task
        job_task_completed = job_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          job_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start post-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        post_task_id = task.id

        # Post-task fails to launch
        update = job_test_utils.create_task_status_update(post_task_id, 'agent', TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Check results
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'docker-task-launch')
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_docker_pull_error(self):
        """Tests running through a job execution where the Docker image pull fails"""

        # Start pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_id = task.id

        # Pull-task running
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(pull_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Pull-task fails
        update = job_test_utils.create_task_status_update(pull_task_id, 'agent', TaskStatusUpdate.FAILED, now())
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Check results
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'pull')
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_general_algorithm_error(self):
        """Tests running through a job execution where the job-task has a general algorithm error (non-zero exit code)
        """

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_id = task.id

        # Pre-task running
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Complete pre-task
        pre_task_completed = pre_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pre_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start job-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        job_task_id = task.id

        # Job-task running
        job_task_started = now()
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          job_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Fail job-task
        job_task_failed = job_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task_id, 'agent', TaskStatusUpdate.FAILED,
                                                          job_task_failed, exit_code=1)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Check results
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'ALGORITHM')
        self.assertEqual(self.running_job_exe.error.name, 'algorithm-unknown')
        self.assertFalse(self.running_job_exe.is_next_task_ready())

    def test_docker_terminated_error(self):
        """Tests running through a job execution where a Docker container terminates"""

        # Start, run, and complete pull-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pull_task_started = now()
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.RUNNING, pull_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)
        pull_task_completed = pull_task_started + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(task.id, 'agent', TaskStatusUpdate.FINISHED,
                                                          pull_task_completed)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Start pre-task
        task = self.running_job_exe.start_next_task()
        self.task_mgr.launch_tasks([task], now())
        pre_task_id = task.id

        # Pre-task running
        pre_task_started = now()
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.RUNNING,
                                                          pre_task_started)
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Pre-task Docker container terminates
        update = job_test_utils.create_task_status_update(pre_task_id, 'agent', TaskStatusUpdate.FAILED, now(),
                                                          reason='REASON_EXECUTOR_TERMINATED')
        self.task_mgr.handle_task_update(update)
        self.running_job_exe.task_update(update)

        # Check results
        self.assertTrue(self.running_job_exe.is_finished())
        self.assertEqual(self.running_job_exe.status, 'FAILED')
        self.assertEqual(self.running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(self.running_job_exe.error.name, 'docker-terminated')
        self.assertFalse(self.running_job_exe.is_next_task_ready())
