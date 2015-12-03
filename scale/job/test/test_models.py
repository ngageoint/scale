#@PydevCodeAnalysisIgnore
import datetime
import time

import django
import django.utils.timezone as timezone
from django.test import TestCase, TransactionTestCase

import job.test.utils as job_test_utils
from error.models import Error
from job.models import Job, JobExecution, JobType


class TestJobManager(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_queue_job_timestamps(self):
        '''Tests that job attributes are updated when a job is queued.'''
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.queue_job(job, None, timezone.now())

        self.assertEqual(job.status, u'QUEUED')
        self.assertIsNotNone(job.queued)
        self.assertIsNone(job.started)
        self.assertIsNone(job.ended)

    def test_update_status_pending(self):
        '''Tests that job attributes are updated when a job is pending.'''
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.update_status(job, u'PENDING', timezone.now())

        self.assertEqual(job.status, u'PENDING')

    def test_update_status_blocked(self):
        '''Tests that job attributes are updated when a job is blocked.'''
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.update_status(job, u'BLOCKED', timezone.now())

        self.assertEqual(job.status, u'BLOCKED')

    def test_update_status_queued(self):
        '''Tests that queued status updates are rejected.'''
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        self.assertRaises(Exception, Job.objects.update_status, job, u'QUEUED', timezone.now())

    def test_update_status_running(self):
        '''Tests that job attributes are updated when a job is running.'''
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.update_status(job, u'RUNNING', timezone.now())

        self.assertEqual(job.status, u'RUNNING')
        self.assertIsNotNone(job.started)
        self.assertIsNone(job.ended)

    def test_update_status_failed(self):
        '''Tests that job attributes are updated when a job is failed.'''
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        self.assertRaises(Exception, Job.objects.update_status, job, u'FAILED', timezone.now())
        self.assertRaises(Exception, Job.objects.update_status, job, u'RUNNING', timezone.now(), Error())

        Job.objects.update_status(job, u'FAILED', timezone.now(), Error())

        self.assertEqual(job.status, u'FAILED')
        self.assertIsNotNone(job.ended)

    def test_update_status_completed(self):
        '''Tests that job attributes are updated when a job is completed.'''
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.update_status(job, u'COMPLETED', timezone.now())

        self.assertEqual(job.status, u'COMPLETED')
        self.assertIsNotNone(job.ended)

    def test_update_status_canceled(self):
        '''Tests that job attributes are updated when a job is canceled.'''
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.update_status(job, u'CANCELED', timezone.now())

        self.assertEqual(job.status, u'CANCELED')
        self.assertIsNotNone(job.ended)


class TestJob(TestCase):

    def setUp(self):
        django.setup()

    def test_is_ready_to_queue(self):
        '''Tests checking the job status for queue eligibility.'''
        self.assertTrue(Job(status='PENDING').is_ready_to_queue)
        self.assertFalse(Job(status='BLOCKED').is_ready_to_queue)
        self.assertFalse(Job(status='QUEUED').is_ready_to_queue)
        self.assertFalse(Job(status='RUNNING').is_ready_to_queue)
        self.assertTrue(Job(status='FAILED').is_ready_to_queue)
        self.assertFalse(Job(status='COMPLETED').is_ready_to_queue)
        self.assertTrue(Job(status='CANCELED').is_ready_to_queue)

    def test_is_ready_to_requeue(self):
        '''Tests checking the job status for requeue eligibility.'''
        self.assertFalse(Job(status='PENDING').is_ready_to_requeue)
        self.assertFalse(Job(status='BLOCKED').is_ready_to_requeue)
        self.assertFalse(Job(status='QUEUED').is_ready_to_requeue)
        self.assertFalse(Job(status='RUNNING').is_ready_to_requeue)
        self.assertTrue(Job(status='FAILED').is_ready_to_requeue)
        self.assertFalse(Job(status='COMPLETED').is_ready_to_requeue)
        self.assertTrue(Job(status='CANCELED').is_ready_to_requeue)

    def test_increase_max_tries_canceled(self):
        '''Tests increasing the maximum number of tries for a job instance that was canceled prematurely.'''
        job_type = JobType(max_tries=10)
        job = Job(job_type=job_type, num_exes=3, max_tries=5)
        job.increase_max_tries()

        self.assertEqual(job.max_tries, 13)

    def test_increase_max_tries_failed(self):
        '''Tests increasing the maximum number of tries for a job instance that ran out of tries due to failures.'''
        job_type = JobType(max_tries=10)
        job = Job(job_type=job_type, num_exes=5, max_tries=5)
        job.increase_max_tries()

        self.assertEqual(job.max_tries, 15)


class TestJobExecutionManager(TransactionTestCase):
    '''Tests for the job execution model manager'''

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type()
        self.job_type_2 = job_test_utils.create_job_type()

        self.job_1a = job_test_utils.create_job(job_type=self.job_type_1)
        job_test_utils.create_job_exe(job=self.job_1a, status=u'FAILED')
        job_test_utils.create_job_exe(job=self.job_1a, status=u'FAILED')
        job_test_utils.create_job_exe(job=self.job_1a, status=u'COMPLETED')
        self.last_run_1a = job_test_utils.create_job_exe(job=self.job_1a, status=u'RUNNING')

        self.job_1b = job_test_utils.create_job(job_type=self.job_type_1, status=u'FAILED')
        self.last_run_1b = job_test_utils.create_job_exe(job=self.job_1b, status=u'FAILED')

        self.job_2a = job_test_utils.create_job(job_type=self.job_type_2)
        job_test_utils.create_job_exe(job=self.job_2a, status=u'FAILED')
        job_test_utils.create_job_exe(job=self.job_2a, status=u'FAILED')
        job_test_utils.create_job_exe(job=self.job_2a, status=u'COMPLETED')
        self.last_run_2a = job_test_utils.create_job_exe(job=self.job_2a, status=u'RUNNING')

        self.job_2b = job_test_utils.create_job(job_type=self.job_type_2)
        self.last_run_2b = job_test_utils.create_job_exe(job=self.job_2b, status=u'COMPLETED')

    def test_get_latest(self):
        job_query = Job.objects.all()
        expected_result = {
            self.job_1a.id: self.last_run_1a,
            self.job_1b.id: self.last_run_1b,
            self.job_2a.id: self.last_run_2a,
            self.job_2b.id: self.last_run_2b,
        }
        latest_job_exes = JobExecution.objects.get_latest(job_query)
        self.assertDictEqual(latest_job_exes, expected_result, 'latest job executions do not match expected results')

    def test_get_latest_job_exes_with_a_filter(self):
        job_query = Job.objects.filter(status=u'FAILED')
        expected_result = {
            self.job_1b.id: self.last_run_1b,
        }
        latest_job_exes = JobExecution.objects.get_latest(job_query)
        self.assertDictEqual(latest_job_exes, expected_result, 'latest job executions do not match expected results')


class TestJobExecution(TransactionTestCase):
    '''Tests for the job execution model'''

    def setUp(self):
        django.setup()

    def test_append_stdout_initial(self):
        '''Tests appending output for the first time.'''
        job_exe = JobExecution()
        job_exe.append_stdout(stdout='initial')
        
        self.assertEqual(job_exe.stdout, 'initial')

    def test_append_stdout_join(self):
        '''Tests appending output to existing output.'''
        job_exe = JobExecution(stdout='initial')
        job_exe.append_stdout('-test1')
        
        self.assertEqual(job_exe.stdout, 'initial-test1')

    def test_append_stdout_none(self):
        '''Tests skipping append when no output is provided.'''
        job_exe = JobExecution(stdout='initial')
        job_exe.append_stdout(None)
        
        self.assertEqual(job_exe.stdout, 'initial')

    def test_append_stderr_initial(self):
        '''Tests appending error for the first time.'''
        job_exe = JobExecution()
        job_exe.append_stderr(stderr='initial')
        
        self.assertEqual(job_exe.stderr, 'initial')

    def test_append_stderr_join(self):
        '''Tests appending error to existing error.'''
        job_exe = JobExecution(stderr='initial')
        job_exe.append_stderr('-test1')
        
        self.assertEqual(job_exe.stderr, 'initial-test1')

    def test_append_stderr_none(self):
        '''Tests skipping append when no error is provided.'''
        job_exe = JobExecution(stderr='initial')
        job_exe.append_stderr(None)
        
        self.assertEqual(job_exe.stderr, 'initial')


class TestJobType(TestCase):

    def setUp(self):
        django.setup()
        self.job_type = job_test_utils.create_job_type()

    def test_update_error_mapping(self):
        '''Tests updating error mapping for job type'''
        error_mapping = {'version': '1.0', 'exit_codes': {'-15': 8, '231': 3}}

        # add a delay for comparing last_modified
        time.sleep(.01)

        JobType.objects.update_error_mapping(error_mapping, self.job_type.id)
        job_type = JobType.objects.get(id=self.job_type.id)

        self.assertEqual(job_type.error_mapping, error_mapping)
        self.assertGreater(job_type.last_modified, self.job_type.last_modified)


class TestJobTypeRunningStatus(TestCase):

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type(name=u'Type 1', version=u'1.0')
        self.job_type_2 = job_test_utils.create_job_type(name=u'Type 2', version=u'2.0')
        self.job_type_3 = job_test_utils.create_job_type(name=u'Type 1', version=u'2.0')

        self.entry_1_longest = datetime.datetime.utcfromtimestamp(500000).replace(tzinfo=timezone.utc)
        self.entry_1_shortest = datetime.datetime.utcfromtimestamp(650000).replace(tzinfo=timezone.utc)
        self.entry_2_longest = datetime.datetime.utcfromtimestamp(600000).replace(tzinfo=timezone.utc)
        self.entry_2_shortest = datetime.datetime.utcfromtimestamp(750000).replace(tzinfo=timezone.utc)
        self.entry_3_longest = datetime.datetime.utcfromtimestamp(700000).replace(tzinfo=timezone.utc)
        self.entry_3_shortest = datetime.datetime.utcfromtimestamp(800000).replace(tzinfo=timezone.utc)

        job_test_utils.create_job(job_type=self.job_type_1, status=u'RUNNING', last_status_change=self.entry_1_longest)
        job_test_utils.create_job(job_type=self.job_type_1, status=u'RUNNING', last_status_change=self.entry_1_shortest)

        job_test_utils.create_job(job_type=self.job_type_2, status=u'RUNNING', last_status_change=self.entry_2_shortest)
        job_test_utils.create_job(job_type=self.job_type_2, status=u'RUNNING', last_status_change=self.entry_2_longest)
        job_test_utils.create_job(job_type=self.job_type_2, status=u'RUNNING', last_status_change=self.entry_2_shortest)

        job_test_utils.create_job(job_type=self.job_type_3, status=u'RUNNING', last_status_change=self.entry_3_shortest)
        job_test_utils.create_job(job_type=self.job_type_3, status=u'RUNNING', last_status_change=self.entry_3_longest)
        job_test_utils.create_job(job_type=self.job_type_3, status=u'RUNNING', last_status_change=self.entry_3_longest)
        job_test_utils.create_job(job_type=self.job_type_3, status=u'RUNNING', last_status_change=self.entry_3_shortest)

    def test_successful(self):
        '''Tests calling the get_running_job_status method on JobExecutionManager.'''

        status = JobType.objects.get_running_status()
        self.assertEqual(len(status), 3)

        # Check entry 1
        self.assertEqual(status[0].job_type.id, self.job_type_1.id)
        self.assertEqual(status[0].job_type.name, u'Type 1')
        self.assertEqual(status[0].job_type.version, u'1.0')
        self.assertEqual(status[0].count, 2)
        self.assertEqual(status[0].longest_running, self.entry_1_longest)

        # Check entry 2
        self.assertEqual(status[1].job_type.id, self.job_type_2.id)
        self.assertEqual(status[1].job_type.name, u'Type 2')
        self.assertEqual(status[1].job_type.version, u'2.0')
        self.assertEqual(status[1].count, 3)
        self.assertEqual(status[1].longest_running, self.entry_2_longest)

        # Check entry 3
        self.assertEqual(status[2].job_type.id, self.job_type_3.id)
        self.assertEqual(status[2].job_type.name, u'Type 1')
        self.assertEqual(status[2].job_type.version, u'2.0')
        self.assertEqual(status[2].count, 4)
        self.assertEqual(status[2].longest_running, self.entry_3_longest)


class TestJobTypeFailedStatus(TestCase):

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type(name=u'Type 1', version=u'1.0')
        self.job_type_2 = job_test_utils.create_job_type(name=u'Type 2', version=u'2.0')
        self.job_type_3 = job_test_utils.create_job_type(name=u'Type 1', version=u'2.0')

        self.error_1 = Error.objects.create(name=u'Error 1', description=u'Test', category=u'SYSTEM')
        self.error_2 = Error.objects.create(name=u'Error 2', description=u'Test', category=u'SYSTEM')
        self.error_3 = Error.objects.create(name=u'Error 3', description=u'Test', category=u'DATA')

        # Date stamps for errors
        self.entry_1_last_time = datetime.datetime.utcfromtimestamp(590000).replace(tzinfo=timezone.utc)
        self.entry_1_first_time = datetime.datetime.utcfromtimestamp(580000).replace(tzinfo=timezone.utc)
        self.entry_2_time = datetime.datetime.utcfromtimestamp(585000).replace(tzinfo=timezone.utc)
        self.entry_3_last_time = datetime.datetime.utcfromtimestamp(490000).replace(tzinfo=timezone.utc)
        self.entry_3_mid_time = datetime.datetime.utcfromtimestamp(480000).replace(tzinfo=timezone.utc)
        self.entry_3_first_time = datetime.datetime.utcfromtimestamp(470000).replace(tzinfo=timezone.utc)
        self.entry_4_time = datetime.datetime.utcfromtimestamp(385000).replace(tzinfo=timezone.utc)

        # Create jobs
        job_test_utils.create_job(job_type=self.job_type_1, status=u'RUNNING', last_status_change=timezone.now())
        job_test_utils.create_job(job_type=self.job_type_1, error=self.error_1, status=u'FAILED',
                                  last_status_change=self.entry_2_time)
        job_test_utils.create_job(job_type=self.job_type_2, error=self.error_1, status=u'FAILED',
                                  last_status_change=self.entry_4_time)
        job_test_utils.create_job(job_type=self.job_type_2, error=self.error_2, status=u'FAILED',
                                  last_status_change=self.entry_1_last_time)
        job_test_utils.create_job(job_type=self.job_type_2, error=self.error_2, status=u'FAILED',
                                  last_status_change=self.entry_1_first_time)
        job_test_utils.create_job(job_type=self.job_type_3, error=self.error_2, status=u'FAILED',
                                  last_status_change=self.entry_3_mid_time)
        job_test_utils.create_job(job_type=self.job_type_3, error=self.error_2, status=u'FAILED',
                                  last_status_change=self.entry_3_last_time)
        job_test_utils.create_job(job_type=self.job_type_3, error=self.error_2, status=u'FAILED',
                                  last_status_change=self.entry_3_first_time)
        job_test_utils.create_job(job_type=self.job_type_3, error=self.error_3, status=u'FAILED',
                                  last_status_change=timezone.now())

    def test_successful(self):
        '''Tests calling the get_failed_jobs_with_system_errors method on JobManager.'''

        status = JobType.objects.get_failed_status()
        self.assertEqual(len(status), 4)

        # Check entry 1
        self.assertEqual(status[0].job_type.id, self.job_type_2.id)
        self.assertEqual(status[0].job_type.name, u'Type 2')
        self.assertEqual(status[0].job_type.version, u'2.0')
        self.assertEqual(status[0].error.name, u'Error 2')
        self.assertEqual(status[0].count, 2)
        self.assertEqual(status[0].first_error, self.entry_1_first_time)
        self.assertEqual(status[0].last_error, self.entry_1_last_time)

        # Check entry 2
        self.assertEqual(status[1].job_type.id, self.job_type_1.id)
        self.assertEqual(status[1].job_type.name, u'Type 1')
        self.assertEqual(status[1].job_type.version, u'1.0')
        self.assertEqual(status[1].error.name, u'Error 1')
        self.assertEqual(status[1].count, 1)
        self.assertEqual(status[1].first_error, self.entry_2_time)
        self.assertEqual(status[1].last_error, self.entry_2_time)

        # Check entry 3
        self.assertEqual(status[2].job_type.id, self.job_type_3.id)
        self.assertEqual(status[2].job_type.name, u'Type 1')
        self.assertEqual(status[2].job_type.version, u'2.0')
        self.assertEqual(status[2].error.name, u'Error 2')
        self.assertEqual(status[2].count, 3)
        self.assertEqual(status[2].first_error, self.entry_3_first_time)
        self.assertEqual(status[2].last_error, self.entry_3_last_time)

        # Check entry 4
        self.assertEqual(status[3].job_type.id, self.job_type_2.id)
        self.assertEqual(status[3].job_type.name, u'Type 2')
        self.assertEqual(status[3].job_type.version, u'2.0')
        self.assertEqual(status[3].error.name, u'Error 1')
        self.assertEqual(status[3].count, 1)
        self.assertEqual(status[3].first_error, self.entry_4_time)
        self.assertEqual(status[3].last_error, self.entry_4_time)
