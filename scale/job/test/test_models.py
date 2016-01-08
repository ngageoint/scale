#@PydevCodeAnalysisIgnore
import datetime
import time

import django
import django.utils.timezone as timezone
from django.test import TestCase, TransactionTestCase

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import node.test.utils as node_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from error.models import Error
from job.configuration.data.exceptions import InvalidConnection
from job.configuration.interface.error_interface import ErrorInterface
from job.configuration.interface.job_interface import JobInterface
from job.models import Job, JobExecution, JobType, JobTypeRevision
from job.resources import JobResources
from trigger.models import TriggerRule


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

    def test_update_jobs_to_running(self):
        '''Tests that job attributes are updated when a job is running.'''
        job_1 = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())
        job_2 = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        when = timezone.now()
        jobs = Job.objects.update_jobs_to_running([job_1.id, job_2.id], when)

        for job in jobs:
            self.assertEqual(job.status, u'RUNNING')
            self.assertEqual(job.started, when)
            self.assertIsNone(job.ended)
            self.assertEqual(job.last_status_change, when)

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

    def test_schedule_job_executions(self):
        job_exe_1 = job_test_utils.create_job_exe(status='QUEUED')
        job_exe_2 = job_test_utils.create_job_exe(status='QUEUED')
        node_1 = node_test_utils.create_node()
        node_2 = node_test_utils.create_node()
        resources_1 = JobResources(cpus=1, mem=2, disk_in=3, disk_out=4, disk_total=7)
        resources_2 = JobResources(cpus=10, mem=11, disk_in=12, disk_out=13, disk_total=25)

        job_exes = JobExecution.objects.schedule_job_executions([(job_exe_1, node_1, resources_1), (job_exe_2, node_2, resources_2)])

        for job_exe in job_exes:
            if job_exe.id == job_exe_1.id:
                job_exe_1 = job_exe
                self.assertEqual(job_exe_1.status, 'RUNNING')
                self.assertEqual(job_exe_1.job.status, 'RUNNING')
                self.assertEqual(job_exe_1.node_id, node_1.id)
                self.assertIsNotNone(job_exe_1.started)
                self.assertEqual(job_exe_1.cpus_scheduled, 1)
                self.assertEqual(job_exe_1.mem_scheduled, 2)
                self.assertEqual(job_exe_1.disk_in_scheduled, 3)
                self.assertEqual(job_exe_1.disk_out_scheduled, 4)
                self.assertEqual(job_exe_1.disk_total_scheduled, 7)
                self.assertEqual(job_exe_1.requires_cleanup, job_exe_1.job.job_type.requires_cleanup)
            else:
                job_exe_2 = job_exe
                self.assertEqual(job_exe_2.status, 'RUNNING')
                self.assertEqual(job_exe_2.job.status, 'RUNNING')
                self.assertEqual(job_exe_2.node_id, node_2.id)
                self.assertIsNotNone(job_exe_2.started)
                self.assertEqual(job_exe_2.cpus_scheduled, 10)
                self.assertEqual(job_exe_2.mem_scheduled, 11)
                self.assertEqual(job_exe_2.disk_in_scheduled, 12)
                self.assertEqual(job_exe_2.disk_out_scheduled, 13)
                self.assertEqual(job_exe_2.disk_total_scheduled, 25)
                self.assertEqual(job_exe_2.requires_cleanup, job_exe_2.job.job_type.requires_cleanup)


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


class TestJobTypeManagerCreateJobType(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.error = error_test_utils.create_error()

        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.job_interface = JobInterface(interface)

        self.configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain'
            },
            'data': {
                'input_data_name': 'Test Input 1',
                'workspace_name': self.workspace.name
            }
        }
        self.trigger_config = job_test_utils.MockTriggerRuleConfiguration(job_test_utils.MOCK_TYPE, self.configuration)

        self.error_mapping = ErrorInterface({
            'version': '1.0',
            'exit_codes': {
                '-15': self.error.name,
            }
        })

    def test_successful_no_trigger_rule(self):
        '''Tests calling JobTypeManager.create_job_type() successfully with no trigger rule or error mapping'''

        name = 'my-job-type'
        version = '1.0'

        # Call test
        job_type = JobType.objects.create_job_type(name, version, self.job_interface)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertIsNone(job_type.trigger_rule_id)
        self.assertDictEqual(job_type.get_error_interface().get_dict(), ErrorInterface(None).get_dict())

    def test_successful_with_trigger_rule(self):
        '''Tests calling JobTypeManager.create_job_type() successfully with a trigger rule and error mapping'''

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())

        # Call test
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, trigger_rule, self.error_mapping)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertEqual(job_type.trigger_rule_id, trigger_rule.id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule.id)
        self.assertTrue(trigger_rule.is_active)
        self.assertDictEqual(job_type.get_error_interface().get_dict(), self.error_mapping.get_dict())

    def test_invalid_trigger_rule(self):
        '''Tests calling JobTypeManager.create_job_type() with an invalid trigger rule'''

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_ERROR_TYPE,
                                                              configuration=self.trigger_config.get_dict())

        # Call test
        self.assertRaises(InvalidConnection, JobType.objects.create_job_type, name, version, self.job_interface,
                          trigger_rule, self.error_mapping)

    def test_successful_other_fields(self):
        '''Tests calling JobTypeManager.create_job_type() successfully with additional fields'''

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13

        # Call test
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, title=title,
                                                   description=description, priority=priority)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertIsNone(job_type.trigger_rule_id)
        self.assertDictEqual(job_type.get_error_interface().get_dict(), ErrorInterface(None).get_dict())
        self.assertEqual(job_type.description, description)
        self.assertEqual(job_type.priority, priority)
        self.assertIsNone(job_type.archived)
        self.assertIsNone(job_type.paused)

    def test_successful_paused(self):
        '''Tests calling JobTypeManager.create_job_type() and pausing it'''

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        is_paused = True

        # Call test
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, title=title,
                                                   description=description, priority=priority, is_paused=is_paused)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertIsNone(job_type.trigger_rule_id)
        self.assertDictEqual(job_type.get_error_interface().get_dict(), ErrorInterface(None).get_dict())
        self.assertEqual(job_type.description, description)
        self.assertEqual(job_type.priority, priority)
        self.assertEqual(job_type.is_paused, is_paused)
        self.assertIsNotNone(job_type.paused)

    def test_uneditable_field(self):
        '''Tests calling JobTypeManager.create_job_type() with an uneditable field'''

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        is_system = True

        # Call test
        self.assertRaises(Exception, JobType.objects.create_job_type, name, version, self.job_interface, title=title,
                          description=description, priority=priority, is_system=is_system)

    def test_invalid_error_mapping(self):
        '''Tests calling JobTypeManager.create_job_type() with an invalid error mapping'''

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        is_system = True
        error_mapping = ErrorInterface({
            'version': '1.0',
            'exit_codes': {
                '1': 'test-invalid-error',
            }
        })

        # Call test
        self.assertRaises(Exception, JobType.objects.create_job_type, name, version, self.job_interface,
                          error_mapping=error_mapping, title=title, description=description, priority=priority,
                          is_system=is_system)


class TestJobTypeManagerEditJobType(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.error = error_test_utils.create_error()

        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.job_interface = JobInterface(interface)

        new_interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 2',
                'type': 'files',
                'media_types': ['image/png', 'image/tiff'],
            }],
            'output_data': [{
                'name': 'Test Output 2',
                'type': 'file',
            }]}
        self.new_job_interface = JobInterface(new_interface)

        self.configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain'
            },
            'data': {
                'input_data_name': 'Test Input 1',
                'workspace_name': self.workspace.name
            }
        }
        self.trigger_config = job_test_utils.MockTriggerRuleConfiguration(job_test_utils.MOCK_TYPE, self.configuration)

        self.new_configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'application/json'
            },
            'data': {
                'input_data_name': 'Test Input 1',
                'workspace_name': self.workspace.name
            }
        }
        self.new_trigger_config = job_test_utils.MockTriggerRuleConfiguration(job_test_utils.MOCK_TYPE,
                                                                              self.new_configuration)

    def test_change_general_fields(self):
        '''Tests calling JobTypeManager.edit_job_type() with a change to some general fields'''

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        priority = 12
        error_mapping = ErrorInterface({
            'version': '1.0',
            'exit_codes': {
                '-15': self.error.name,
            }
        })
        new_title = 'my new title'
        new_priority = 13
        new_error_mapping = ErrorInterface({
            'version': '1.0',
            'exit_codes': {
                '-16': self.error.name,
            }
        })
        new_is_paused = True
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, trigger_rule, title=title,
                                                   priority=priority, error_mapping=error_mapping)

        # Call test
        JobType.objects.edit_job_type(job_type.id, title=new_title, priority=new_priority,
                                      error_mapping=new_error_mapping, is_paused=new_is_paused)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertEqual(job_type.trigger_rule_id, trigger_rule.id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule.id)
        self.assertTrue(trigger_rule.is_active)
        self.assertEqual(job_type.title, new_title)
        self.assertEqual(job_type.priority, new_priority)
        self.assertDictEqual(job_type.get_error_interface().get_dict(), new_error_mapping.get_dict())
        self.assertEqual(job_type.is_paused, new_is_paused)
        self.assertIsNotNone(job_type.paused)

    def test_change_to_interface(self):
        '''Tests calling JobTypeManager.edit_job_type() with a change to the interface'''

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, trigger_rule)

        # Call test
        JobType.objects.edit_job_type(job_type.id, self.new_job_interface, None, False)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.new_job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 2)
        self.assertEqual(job_type.trigger_rule_id, trigger_rule.id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule.id)
        self.assertTrue(trigger_rule.is_active)
        # New revision due to interface change
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 2)

    def test_change_to_trigger_rule(self):
        '''Tests calling JobTypeManager.edit_job_type() with a change to the trigger rule'''

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        new_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                                  configuration=self.new_trigger_config.get_dict())
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, trigger_rule)

        # Call test
        JobType.objects.edit_job_type(job_type.id, None, new_trigger_rule, False)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertEqual(job_type.trigger_rule_id, new_trigger_rule.id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule.id)
        self.assertFalse(trigger_rule.is_active)
        new_trigger_rule = TriggerRule.objects.get(pk=new_trigger_rule.id)
        self.assertTrue(new_trigger_rule.is_active)
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 1)

    def test_remove_trigger_rule(self):
        '''Tests calling JobTypeManager.edit_job_type() that removes the trigger rule'''

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, trigger_rule)

        # Call test
        JobType.objects.edit_job_type(job_type.id, None, None, True)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertIsNone(job_type.trigger_rule)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule.id)
        self.assertFalse(trigger_rule.is_active)
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 1)

    def test_change_to_both(self):
        '''Tests calling JobTypeManager.edit_job_type() with a change to both the definition and the trigger rule
        '''

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        new_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                                  configuration=self.new_trigger_config.get_dict())
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, trigger_rule)

        # Call test
        JobType.objects.edit_job_type(job_type.id, self.new_job_interface, new_trigger_rule, False)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.new_job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 2)
        self.assertEqual(job_type.trigger_rule_id, new_trigger_rule.id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule.id)
        self.assertFalse(trigger_rule.is_active)
        new_trigger_rule = TriggerRule.objects.get(pk=new_trigger_rule.id)
        self.assertTrue(new_trigger_rule.is_active)
        # New revision due to definition change
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 2)

    def test_invalid_trigger_rule(self):
        '''Tests calling JobTypeManager.edit_job_type() with a new invalid trigger rule'''

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        new_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_ERROR_TYPE,
                                                                  configuration=self.new_trigger_config.get_dict())
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, trigger_rule)
        
        # Call test
        self.assertRaises(InvalidConnection, JobType.objects.edit_job_type, job_type.id, self.new_job_interface,
                          new_trigger_rule, False)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertEqual(job_type.trigger_rule_id, trigger_rule.id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule.id)
        self.assertTrue(trigger_rule.is_active)
        num_of_revs = JobTypeRevision.objects.filter(job_type_id=job_type.id).count()
        self.assertEqual(num_of_revs, 1)

    def test_system_job_type(self):
        '''Tests calling JobTypeManager.edit_job_type() for a system job type'''

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        new_title = 'my new title'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, trigger_rule, title=title)
        job_type.is_system = True
        job_type.save()
        
        # Call test
        self.assertRaises(Exception, JobType.objects.edit_job_type, job_type.id, title=new_title)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        # No change
        self.assertEqual(job_type.title, title)

    def test_uneditable_field(self):
        '''Tests calling JobTypeManager.edit_job_type() to change an uneditable field'''

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        new_title = 'my new title'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, trigger_rule, title=title)

        # Call test
        self.assertRaises(Exception, JobType.objects.edit_job_type, job_type.id, title=new_title, is_system=True)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        # No change
        self.assertEqual(job_type.title, title)

    def test_invalid_error_mapping(self):
        '''Tests calling JobTypeManager.edit_job_type() with an invalid error mapping'''

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        is_system = True
        error_mapping = ErrorInterface({
            'version': '1.0',
            'exit_codes': {
                '1': 'test-invalid-error',
            }
        })

        # Call test
        self.assertRaises(Exception, JobType.objects.edit_job_type, name, version, self.job_interface,
                          error_mapping=error_mapping, title=title, description=description, priority=priority,
                          is_system=is_system)


class TestJobTypeManagerValidateJobType(TestCase):

    def setUp(self):
        django.setup()

        self.workspace = storage_test_utils.create_workspace()
        self.error = error_test_utils.create_error()

        self.interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Test Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Test Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        self.job_interface = JobInterface(self.interface)

        self.error_mapping = ErrorInterface({
            'version': '1.0',
            'exit_codes': {
                '1': self.error.name,
            }
        })

        self.configuration = {
            'version': '1.0',
            'condition': {
                'media_type': 'text/plain'
            },
            'data': {
                'input_data_name': 'Test Input 1',
                'workspace_name': self.workspace.name
            }
        }
        self.trigger_config = job_test_utils.MockTriggerRuleConfiguration(job_test_utils.MOCK_TYPE, self.configuration)
        self.trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                                   configuration=self.trigger_config.get_dict())
        self.invalid_trigger_config = job_test_utils.MockErrorTriggerRuleConfiguration(job_test_utils.MOCK_ERROR_TYPE, self.configuration)
        self.invalid_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_ERROR_TYPE,
                                                                   configuration=self.trigger_config.get_dict())

    def test_successful(self):
        '''Tests calling JobTypeManager.validate_job_type() successfully'''

        warnings = JobType.objects.validate_job_type('name', '1.0', self.interface, self.error_mapping,
                                                     self.trigger_config)

        # Check results
        self.assertListEqual(warnings, [])

    def test_invalid(self):
        '''Tests calling JobTypeManager.validate_job_type() with an invalid trigger rule'''

        self.assertRaises(InvalidConnection, JobType.objects.validate_job_type, 'name', '1.0', self.interface,
                          self.error_mapping, self.invalid_trigger_config)


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
