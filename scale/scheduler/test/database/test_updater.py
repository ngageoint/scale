from __future__ import unicode_literals

import django
from django.test import TestCase

from job.models import JobExecution, TaskUpdate
from job.test import utils as job_test_utils
from scheduler.database.updater import DatabaseUpdater


class TestDatabaseUpdater(TestCase):

    def setUp(self):
        django.setup()

    def test_update(self):
        """Tests running the database update"""

        # Create jobs with duplicate job executions
        job_type = job_test_utils.create_job_type()
        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=2)
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=3)
        job_3 = job_test_utils.create_job(job_type=job_type, num_exes=2)

        # Job 1
        job_exe_1 = job_test_utils.create_job_exe(job=job_1, status='COMPLETED', exe_num=1)
        job_exe_2 = job_test_utils.create_job_exe(job=job_1, status='COMPLETED', exe_num=1)
        job_exe_3 = job_test_utils.create_job_exe(job=job_1, status='COMPLETED', exe_num=2)
        job_exe_4 = job_test_utils.create_job_exe(job=job_1, status='COMPLETED', exe_num=2)

        # Job 2
        job_exe_5 = job_test_utils.create_job_exe(job=job_2, status='COMPLETED', exe_num=1)
        job_exe_6 = job_test_utils.create_job_exe(job=job_2, status='COMPLETED', exe_num=2)
        job_exe_7 = job_test_utils.create_job_exe(job=job_2, status='COMPLETED', exe_num=2)
        job_exe_8 = job_test_utils.create_job_exe(job=job_2, status='COMPLETED', exe_num=3)

        # Job 3
        job_exe_9 = job_test_utils.create_job_exe(job=job_3, status='COMPLETED', exe_num=1)

        # Create some task updates to make sure they get deleted as well
        task_updates = []
        task_updates.append(TaskUpdate(job_exe=job_exe_1, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_1, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_2, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_2, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_3, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_3, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_4, task_id='1234', status='foo'))
        task_updates.append(TaskUpdate(job_exe=job_exe_4, task_id='1234', status='foo'))
        TaskUpdate.objects.bulk_create(task_updates)

        # Run update
        updater = DatabaseUpdater()
        updater.update()

        expected_job_exe_ids = {job_exe_1.id, job_exe_3.id, job_exe_5.id, job_exe_6.id, job_exe_8.id, job_exe_9.id}
        actual_job_exe_ids = set()
        for job_exe in JobExecution.objects.all().only('id'):
            actual_job_exe_ids.add(job_exe.id)
        self.assertSetEqual(expected_job_exe_ids, actual_job_exe_ids)
