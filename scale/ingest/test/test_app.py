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
        job = job_test_utils.create_job(job_type=ingest_job_type, num_exes=1)
        job_exe = job_test_utils.create_job_exe(job=job)
        running_job_exe = RunningJobExecution(job_exe)

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
        timed_out_task = running_job_exe.execution_timed_out(job_task, when_timed_out)
        self.assertEqual(job_task.id, timed_out_task.id)
        self.assertTrue(running_job_exe.is_finished())
        self.assertFalse(running_job_exe.is_next_task_ready())

        job_exe = JobExecution.objects.get(id=job_exe.id)
        self.assertEqual('FAILED', job_exe.status)
        self.assertEqual('ingest-timeout', job_exe.error.name)
        self.assertEqual(when_timed_out, job_exe.ended)
