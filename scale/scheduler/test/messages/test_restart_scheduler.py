from __future__ import unicode_literals

import datetime

import django
from django.test import TestCase
from django.utils.timezone import now

from error.models import get_builtin_error, reset_error_cache
from job.messages.failed_jobs import FailedJob
from job.models import Job
from job.test import utils as job_test_utils
from scheduler.messages.restart_scheduler import RestartScheduler


class TestRestartScheduler(TestCase):

    fixtures = ['scheduler_errors.json']

    def setUp(self):
        django.setup()

        reset_error_cache()

    def test_json(self):
        """Tests coverting a RestartScheduler message to and from JSON"""

        started = now()
        scheduler_restarted = started + datetime.timedelta(seconds=30)
        running_job_exe = job_test_utils.create_running_job_exe(started=started)

        # Create message
        message = RestartScheduler()
        message.when = scheduler_restarted

        # Convert message to JSON and back, and then execute
        message_json_dict = message.to_json()
        new_message = RestartScheduler.from_json(message_json_dict)
        result = new_message.execute()

        self.assertTrue(result)
        failed_jobs_msg = None
        job_exe_end_msg = None
        self.assertEqual(len(new_message.new_messages), 2)
        for msg in new_message.new_messages:
            if msg.type == 'failed_jobs':
                failed_jobs_msg = msg
            elif msg.type == 'create_job_exe_ends':
                job_exe_end_msg = msg
        self.assertEqual(failed_jobs_msg._failed_jobs.values()[0][0].job_id, running_job_exe.job_id)
        self.assertEqual(job_exe_end_msg._job_exe_ends[0].job_exe_id, running_job_exe.id)

    def test_execute(self):
        """Tests calling RestartScheduler.execute() successfully"""

        started = now()
        scheduler_restarted = started + datetime.timedelta(seconds=30)
        started_later = scheduler_restarted + datetime.timedelta(seconds=30)
        running_job_exe_1 = job_test_utils.create_running_job_exe(started=started)
        running_job_exe_2 = job_test_utils.create_running_job_exe(started=started)
        running_job_exe_3 = job_test_utils.create_running_job_exe(started=started)
        running_job_exe_4 = job_test_utils.create_running_job_exe(started=started_later)  # After scheduler restart

        # Set job 1 so it is still QUEUED
        Job.objects.filter(id=running_job_exe_1.job_id).update(status='QUEUED')

        # Set job 3 to COMPLETED, so it should not be failed by scheduler restart
        Job.objects.filter(id=running_job_exe_3.job_id).update(status='COMPLETED')

        # Create message
        message = RestartScheduler()
        message.when = scheduler_restarted

        # Execute message
        result = message.execute()
        self.assertTrue(result)

        failed_jobs_msg = None
        job_exe_end_msg = None
        self.assertEqual(len(message.new_messages), 2)
        for msg in message.new_messages:
            if msg.type == 'failed_jobs':
                failed_jobs_msg = msg
            elif msg.type == 'create_job_exe_ends':
                job_exe_end_msg = msg

        error = get_builtin_error('scheduler-lost')
        # Jobs 1 and 2 should be in messages to be failed, Jobs 3 and 4 should not be included
        expected_failed_jobs = {FailedJob(running_job_exe_1.job_id, running_job_exe_1.exe_num, error.id),
                                FailedJob(running_job_exe_2.job_id, running_job_exe_2.exe_num, error.id)}
        expected_failed_job_exe_ids = {running_job_exe_1.id, running_job_exe_2.id}
        self.assertSetEqual(set(failed_jobs_msg._failed_jobs.values()[0]), expected_failed_jobs)
        failed_job_exe_ids = set()
        for job_exe_end_model in job_exe_end_msg._job_exe_ends:
            failed_job_exe_ids.add(job_exe_end_model.job_exe_id)
        self.assertSetEqual(failed_job_exe_ids, expected_failed_job_exe_ids)

        # Test executing message again, should get same result
        message_json_dict = message.to_json()
        message = RestartScheduler.from_json(message_json_dict)
        result = message.execute()
        self.assertTrue(result)

        # Jobs 1 and 2 should be in messages to be failed, Jobs 3 and 4 should not be included
        expected_failed_jobs = {FailedJob(running_job_exe_1.job_id, running_job_exe_1.exe_num, error.id),
                                FailedJob(running_job_exe_2.job_id, running_job_exe_2.exe_num, error.id)}
        expected_failed_job_exe_ids = {running_job_exe_1.id, running_job_exe_2.id}
        self.assertSetEqual(set(failed_jobs_msg._failed_jobs.values()[0]), expected_failed_jobs)
        failed_job_exe_ids = set()
        for job_exe_end_model in job_exe_end_msg._job_exe_ends:
            failed_job_exe_ids.add(job_exe_end_model.job_exe_id)
        self.assertSetEqual(failed_job_exe_ids, expected_failed_job_exe_ids)
