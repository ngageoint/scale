from __future__ import unicode_literals

from datetime import timedelta

import django
from django.test import TestCase
from django.utils.timezone import now

import job.test.utils as job_test_utils
from ingest.models import Ingest
from job.execution.job_exe import RunningJobExecution
from job.models import JobExecution
from job.tasks.manager import TaskManager
from job.tasks.update import TaskStatusUpdate


class TestIngestJobType(TestCase):
    """Tests things related to the ingest job type"""

    fixtures = ['basic_errors.json', 'basic_job_errors.json', 'ingest_job_types.json', 'ingest_errors.json']

    def setUp(self):
        django.setup()

        self.task_mgr = TaskManager()

    def test_timed_out_system_job_task(self):
        """Tests running through a job execution where a system job task times out"""

        ingest_job_type = Ingest.objects.get_ingest_job_type()
        ingest_job_type.max_tries = 1
        ingest_job_type.save()
        running_job_exe = job_test_utils.create_running_job_exe(agent_id='agent_1', job_type=ingest_job_type,
                                                                num_exes=1)

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

        self.assertFalse(running_job_exe.is_finished())  # Not finished until killed task update arrives
        self.assertEqual(running_job_exe.status, 'FAILED')
        self.assertEqual(running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(running_job_exe.error.name, 'ingest-timeout')
        self.assertEqual(running_job_exe.finished, when_timed_out)
        self.assertFalse(running_job_exe.is_next_task_ready())

        # Killed task update arrives, job execution is now finished
        job_task_kill = when_timed_out + timedelta(seconds=1)
        update = job_test_utils.create_task_status_update(job_task.id, 'agent', TaskStatusUpdate.KILLED, job_task_kill)
        self.task_mgr.handle_task_update(update)
        running_job_exe.task_update(update)
        self.assertTrue(running_job_exe.is_finished())
        self.assertEqual(running_job_exe.status, 'FAILED')
        self.assertEqual(running_job_exe.error_category, 'SYSTEM')
        self.assertEqual(running_job_exe.error.name, 'ingest-timeout')
        self.assertEqual(running_job_exe.finished, when_timed_out)
        self.assertFalse(running_job_exe.is_next_task_ready())
