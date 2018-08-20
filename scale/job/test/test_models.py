from __future__ import unicode_literals
from __future__ import absolute_import

import copy
import datetime
import json
import time

import django
import django.utils.timezone as timezone
from django.test import TestCase, TransactionTestCase

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from error.models import Error
from job.configuration.data.exceptions import InvalidConnection
from job.configuration.data.job_data import JobData
from job.configuration.interface.job_interface import JobInterface
from job.configuration.results.job_results import JobResults
from job.error.mapping import create_legacy_error_mapping
from job.seed.results.job_results import JobResults as SeedJobResults
from job.models import Job, JobExecution, JobExecutionOutput, JobInputFile, JobType, JobTypeRevision, JobTypeTag
from node.resources.json.resources import Resources
from trigger.models import TriggerRule


class TestJobManager(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_get_details(self):
        """Tests calling JobManager.get_details() with extra data inputs that should be ignored"""

        workspace_1 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace_1)
        file_2 = storage_test_utils.create_file(workspace=workspace_1)
        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }]}
        job_type = job_test_utils.create_job_type(interface=interface)
        job = job_test_utils.create_job(job_type=job_type, status='PENDING')
        orig_data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_1.id
            }, {
                'name': 'Input 2',
                'file_id': file_2.id
            }, {
                'name': 'Input 3',
                'value': 'hello'
            }]}
        data = copy.deepcopy(orig_data)
        job_data = JobData(data)
        Job.objects.populate_job_data(job, job_data)
        # populate_job_data() strips out extra inputs, so force them back in
        job.data = orig_data
        job.save()

        # No exception means success
        Job.objects.get_details(job.id)

    def test_populate_job_data(self):
        """Tests calling JobManager.populate_job_data()"""

        workspace_1 = storage_test_utils.create_workspace()
        workspace_2 = storage_test_utils.create_workspace()
        workspace_3 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace_1, file_size=10485760.0)
        file_2 = storage_test_utils.create_file(workspace=workspace_2, file_size=104857600.0)
        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }, {
                'name': 'Input 2',
                'type': 'file',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        job_type = job_test_utils.create_job_type(interface=interface)
        job = job_test_utils.create_job(job_type=job_type, status='PENDING', input_file_size=None)
        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_1.id
            }, {
                'name': 'Input 2',
                'file_id': file_2.id
            }],
            'output_data': [{
                'name': 'Output 1',
                'workspace_id': workspace_3.id
            }]}
        job_data = JobData(data)

        Job.objects.populate_job_data(job, job_data)

        job = Job.objects.get(id=job.id)

        # Make sure input file size is calculated and set
        self.assertEqual(job.input_file_size, 110)  # Convert from file bytes to MiB to get 110 value
        # Make sure job input file models are created
        job_input_files = JobInputFile.objects.filter(job_id=job.id)
        self.assertEqual(len(job_input_files), 2)
        for job_input_file in job_input_files:
            if job_input_file.job_input == 'Input 1':
                self.assertEqual(job_input_file.input_file_id, file_1.id)
            elif job_input_file.job_input == 'Input 2':
                self.assertEqual(job_input_file.input_file_id, file_2.id)
            else:
                self.fail('Invalid input name: %s' % job_input_file.job_input)

    def test_populate_job_data_extra_inputs(self):
        """Tests calling JobManager.populate_job_data() with extra inputs"""

        workspace_1 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace_1)
        file_2 = storage_test_utils.create_file(workspace=workspace_1)
        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }]}
        job_type = job_test_utils.create_job_type(interface=interface)
        job = job_test_utils.create_job(job_type=job_type, status='PENDING')
        data = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_1.id
            }, {
                'name': 'Input 2',
                'file_id': file_2.id
            }, {
                'name': 'Input 3',
                'value': 'hello'
            }]}
        job_data = JobData(data)

        Job.objects.populate_job_data(job, job_data)

        # Check that only Input 1 remains in the job_data
        job = Job.objects.get(id=job.id)
        data_dict = job.get_job_data().get_dict()
        self.assertEqual(len(data_dict['input_data']), 1)
        self.assertEqual(data_dict['input_data'][0]['name'], 'Input 1')

    def test_process_job_input(self):
        """Tests calling JobManager.process_job_input()"""

        date_1 = timezone.now()
        min_src_started_job_1 = date_1 - datetime.timedelta(days=200)
        max_src_ended_job_1 = date_1 + datetime.timedelta(days=200)
        date_2 = date_1 + datetime.timedelta(minutes=30)
        date_3 = date_1 + datetime.timedelta(minutes=40)
        date_4 = date_1 + datetime.timedelta(minutes=50)
        min_src_started_job_2 = date_1 - datetime.timedelta(days=500)
        max_src_ended_job_2 = date_1 + datetime.timedelta(days=500)
        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=10485760.0)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0, source_started=date_2,
                                                source_ended=date_3)
        file_3 = storage_test_utils.create_file(workspace=workspace, file_size=987654321.0,
                                                source_started=min_src_started_job_1, source_ended=date_4)
        file_4 = storage_test_utils.create_file(workspace=workspace, file_size=46546.0,
                                                source_ended=max_src_ended_job_1)
        file_5 = storage_test_utils.create_file(workspace=workspace, file_size=83457.0, source_started=date_2)
        file_6 = storage_test_utils.create_file(workspace=workspace, file_size=42126588636633.0, source_ended=date_4)
        file_7 = storage_test_utils.create_file(workspace=workspace, file_size=76645464662354.0)
        file_8 = storage_test_utils.create_file(workspace=workspace, file_size=4654.0,
                                                source_started=min_src_started_job_2)
        file_9 = storage_test_utils.create_file(workspace=workspace, file_size=545.0, source_started=date_3,
                                                source_ended=max_src_ended_job_2)
        file_10 = storage_test_utils.create_file(workspace=workspace, file_size=0.154, source_ended=date_4)
        interface = {
            'version': '1.0',
            'command': 'my_command',
            'command_arguments': 'args',
            'input_data': [{
                'name': 'Input 1',
                'type': 'file',
                'media_types': ['text/plain'],
            }, {
                'name': 'Input 2',
                'type': 'files',
                'media_types': ['text/plain'],
            }],
            'output_data': [{
                'name': 'Output 1',
                'type': 'files',
                'media_type': 'image/png',
            }]}
        job_type = job_test_utils.create_job_type(interface=interface)

        data_1 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_1.id
            }, {
                'name': 'Input 2',
                'file_ids': [file_2.id, file_3.id, file_4.id, file_5.id]
            }],
            'output_data': [{
                'name': 'Output 1',
                'workspace_id': workspace.id
            }]}
        data_2 = {
            'version': '1.0',
            'input_data': [{
                'name': 'Input 1',
                'file_id': file_6.id
            }, {
                'name': 'Input 2',
                'file_ids': [file_7.id, file_8.id, file_9.id, file_10.id]
            }],
            'output_data': [{
                'name': 'Output 1',
                'workspace_id': workspace.id
            }]}

        job_1 = job_test_utils.create_job(job_type=job_type, num_exes=0, status='PENDING', input_file_size=None,
                                          input=data_1)
        job_2 = job_test_utils.create_job(job_type=job_type, num_exes=0, status='PENDING', input_file_size=None,
                                          input=data_2)

        # Execute method
        Job.objects.process_job_input(job_1)
        Job.objects.process_job_input(job_2)

        # Retrieve updated job models
        jobs = Job.objects.filter(id__in=[job_1.id, job_2.id]).order_by('id')
        job_1 = jobs[0]
        job_2 = jobs[1]

        # Check jobs for expected fields
        self.assertEqual(job_1.input_file_size, 1053.0)
        self.assertEqual(job_1.source_started, min_src_started_job_1)
        self.assertEqual(job_1.source_ended, max_src_ended_job_1)
        self.assertEqual(job_2.input_file_size, 113269857.0)
        self.assertEqual(job_2.source_started, min_src_started_job_2)
        self.assertEqual(job_2.source_ended, max_src_ended_job_2)

        # Make sure job input file models are created
        job_input_files = JobInputFile.objects.filter(job_id=job_1.id)
        self.assertEqual(len(job_input_files), 5)
        input_files_dict = {'Input 1': set(), 'Input 2': set()}
        for job_input_file in job_input_files:
            input_files_dict[job_input_file.job_input].add(job_input_file.input_file_id)
        self.assertDictEqual(input_files_dict, {'Input 1': {file_1.id}, 'Input 2': {file_2.id, file_3.id, file_4.id,
                                                                                    file_5.id}})
        job_input_files = JobInputFile.objects.filter(job_id=job_2.id)
        self.assertEqual(len(job_input_files), 5)
        input_files_dict = {'Input 1': set(), 'Input 2': set()}
        for job_input_file in job_input_files:
            input_files_dict[job_input_file.job_input].add(job_input_file.input_file_id)
        self.assertDictEqual(input_files_dict, {'Input 1': {file_6.id}, 'Input 2': {file_7.id, file_8.id, file_9.id,
                                                                                    file_10.id}})

    def test_process_job_output(self):
        """Tests calling JobManager.process_job_output()"""

        output_1 = JobResults()
        output_1.add_file_parameter('foo', 1)
        output_2 = JobResults()
        output_2.add_file_parameter('foo', 2)

        # These jobs have completed and have their execution results
        job_exe_1 = job_test_utils.create_job_exe(status='COMPLETED', output=output_1)
        job_exe_2 = job_test_utils.create_job_exe(status='COMPLETED', output=output_2)

        # These jobs have their execution results, but have not completed
        job_exe_3 = job_test_utils.create_job_exe(status='RUNNING')
        job_exe_4 = job_test_utils.create_job_exe(status='RUNNING')
        for job_exe in [job_exe_3, job_exe_4]:
            job_exe_output = JobExecutionOutput()
            job_exe_output.job_exe_id = job_exe.id
            job_exe_output.job_id = job_exe.job_id
            job_exe_output.job_type_id = job_exe.job.job_type_id
            job_exe_output.exe_num = job_exe.exe_num
            job_exe_output.output = JobResults().get_dict()
            job_exe_output.save()

        # These jobs have completed, but do not have their execution results
        job_exe_5 = job_test_utils.create_job_exe(status='RUNNING')
        job_exe_6 = job_test_utils.create_job_exe(status='RUNNING')
        for job in [job_exe_5.job, job_exe_6.job]:
            job.status = 'COMPLETED'
            job.save()

        # Test method
        job_ids = [job_exe.job_id for job_exe in [job_exe_1, job_exe_2, job_exe_3, job_exe_4, job_exe_5, job_exe_6]]
        result_ids = Job.objects.process_job_output(job_ids, timezone.now())

        self.assertEqual(set(result_ids), {job_exe_1.job_id, job_exe_2.job_id})
        # Jobs 1 and 2 should have output populated, jobs 3 through 6 should not
        jobs = list(Job.objects.filter(id__in=job_ids).order_by('id'))
        self.assertEqual(len(jobs), 6)
        self.assertTrue(jobs[0].has_output())
        self.assertDictEqual(jobs[0].output, output_1.get_dict())
        self.assertTrue(jobs[1].has_output())
        self.assertDictEqual(jobs[1].output, output_2.get_dict())
        self.assertFalse(jobs[2].has_output())
        self.assertFalse(jobs[3].has_output())
        self.assertFalse(jobs[4].has_output())
        self.assertFalse(jobs[5].has_output())

    def test_queue_job_timestamps(self):
        """Tests that job attributes are updated when a job is queued."""
        job = job_test_utils.create_job(num_exes=1, status='CANCELED', input={}, started=timezone.now(),
                                        ended=timezone.now())

        Job.objects.update_jobs_to_queued([job], timezone.now(), requeue=True)
        job = Job.objects.get(pk=job.id)

        self.assertEqual(job.status, 'QUEUED')
        self.assertIsNotNone(job.queued)
        self.assertIsNone(job.started)
        self.assertIsNone(job.ended)

    def test_queue_superseded_jobs(self):
        """Tests that JobManager.update_jobs_to_queued() does not queue superseded jobs"""

        job = job_test_utils.create_job(status='FAILED')
        Job.objects.supersede_jobs_old([job], timezone.now())

        job_ids = Job.objects.update_jobs_to_queued([job], timezone.now())
        job = Job.objects.get(pk=job.id)

        self.assertListEqual(job_ids, [])
        self.assertEqual(job.status, 'FAILED')
        self.assertTrue(job.is_superseded)

    def test_superseded_job(self):
        """Tests creating a job that supersedes another job"""

        old_job = job_test_utils.create_job()

        event = trigger_test_utils.create_trigger_event()
        new_job = Job.objects.create_job_old(old_job.job_type, event.id, superseded_job=old_job,
                                             delete_superseded=False)
        new_job.save()
        when = timezone.now()
        Job.objects.supersede_jobs_old([old_job], when)

        new_job = Job.objects.get(pk=new_job.id)
        self.assertEqual(new_job.status, 'PENDING')
        self.assertFalse(new_job.is_superseded)
        self.assertEqual(new_job.root_superseded_job_id, old_job.id)
        self.assertEqual(new_job.superseded_job_id, old_job.id)
        self.assertFalse(new_job.delete_superseded)
        self.assertIsNone(new_job.superseded)
        old_job = Job.objects.get(pk=old_job.id)
        self.assertTrue(old_job.is_superseded)
        self.assertEqual(old_job.superseded, when)

    def test_update_status_running(self):
        """Tests that job attributes are updated when a job is running."""
        job_1 = job_test_utils.create_job(num_exes=1, started=None, ended=timezone.now())
        job_2 = job_test_utils.create_job(num_exes=1, started=None, ended=timezone.now())

        when = timezone.now()
        Job.objects.update_status([job_1, job_2], 'RUNNING', when)

        jobs = Job.objects.filter(id__in=[job_1.id, job_2.id])
        for job in jobs:
            self.assertEqual(job.status, 'RUNNING')
            self.assertEqual(job.started, when)
            self.assertIsNone(job.ended)
            self.assertEqual(job.last_status_change, when)

    def test_update_status_pending(self):
        """Tests that job attributes are updated when a job is pending."""
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.update_status([job], 'PENDING', timezone.now())

        self.assertEqual(job.status, 'PENDING')
        self.assertIsNone(job.ended)

    def test_update_status_blocked(self):
        """Tests that job attributes are updated when a job is blocked."""
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.update_status([job], 'BLOCKED', timezone.now())

        self.assertEqual(job.status, 'BLOCKED')
        self.assertIsNone(job.ended)

    def test_update_status_queued(self):
        """Tests that queued status updates are rejected."""
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        self.assertRaises(Exception, Job.objects.update_status, [job], 'QUEUED', timezone.now())

    def test_update_status_failed(self):
        """Tests that job attributes are updated when a job is failed."""
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())
        error = error_test_utils.create_error()

        self.assertRaises(Exception, Job.objects.update_status, [job], 'FAILED', timezone.now())
        self.assertRaises(Exception, Job.objects.update_status, [job], 'RUNNING', timezone.now(), error)

        Job.objects.update_status([job], 'FAILED', timezone.now(), error)

        self.assertEqual(job.status, 'FAILED')
        self.assertIsNotNone(job.ended)

    def test_update_status_completed(self):
        """Tests that job attributes are updated when a job is completed."""
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.update_status([job], 'COMPLETED', timezone.now())

        self.assertEqual(job.status, 'COMPLETED')
        self.assertIsNotNone(job.ended)

    def test_update_status_canceled(self):
        """Tests that job attributes are updated when a job is canceled."""
        job = job_test_utils.create_job(num_exes=1, started=timezone.now(), ended=timezone.now())

        Job.objects.update_status([job], 'CANCELED', timezone.now())

        self.assertEqual(job.status, 'CANCELED')
        self.assertIsNotNone(job.ended)


class TestJob(TestCase):

    def setUp(self):
        django.setup()

    def test_is_ready_to_requeue(self):
        """Tests checking the job status for requeue eligibility."""
        self.assertFalse(Job(status='PENDING').is_ready_to_requeue)
        self.assertFalse(Job(status='BLOCKED').is_ready_to_requeue)
        self.assertFalse(Job(status='QUEUED').is_ready_to_requeue)
        self.assertFalse(Job(status='RUNNING').is_ready_to_requeue)
        self.assertTrue(Job(status='FAILED').is_ready_to_requeue)
        self.assertFalse(Job(status='COMPLETED').is_ready_to_requeue)
        self.assertTrue(Job(status='CANCELED').is_ready_to_requeue)

    def test_get_seed_job_results(self):
        """Test retrieving job results from a Seed job type"""
        job_type = job_test_utils.create_seed_job_type()

        input = {
            "version": "1.0",
            "input_data": {},
            "output_data": {}
        }

        job = job_test_utils.create_job(job_type, input=input)

        self.assertIsInstance(job.get_job_results(), SeedJobResults)


class TestJobExecutionManager(TransactionTestCase):
    """Tests for the job execution model manager"""

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type()
        self.job_type_2 = job_test_utils.create_job_type()

        self.job_1a = job_test_utils.create_job(job_type=self.job_type_1)
        job_test_utils.create_job_exe(job=self.job_1a, status='FAILED')
        time.sleep(.01)
        job_test_utils.create_job_exe(job=self.job_1a, status='FAILED')
        time.sleep(.01)
        job_test_utils.create_job_exe(job=self.job_1a, status='COMPLETED')
        time.sleep(.01)
        self.last_run_1a = job_test_utils.create_job_exe(job=self.job_1a, status='RUNNING')

        self.job_1b = job_test_utils.create_job(job_type=self.job_type_1, status='FAILED')
        self.last_run_1b = job_test_utils.create_job_exe(job=self.job_1b, status='FAILED')

        self.job_2a = job_test_utils.create_job(job_type=self.job_type_2)
        job_test_utils.create_job_exe(job=self.job_2a, status='FAILED')
        time.sleep(.01)
        job_test_utils.create_job_exe(job=self.job_2a, status='FAILED')
        time.sleep(.01)
        job_test_utils.create_job_exe(job=self.job_2a, status='COMPLETED')
        time.sleep(.01)
        self.last_run_2a = job_test_utils.create_job_exe(job=self.job_2a, status='RUNNING')

        self.job_2b = job_test_utils.create_job(job_type=self.job_type_2)
        self.last_run_2b = job_test_utils.create_job_exe(job=self.job_2b, status='COMPLETED')

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
        job_query = Job.objects.filter(status='FAILED')
        expected_result = {
            self.job_1b.id: self.last_run_1b,
        }
        latest_job_exes = JobExecution.objects.get_latest(job_query)
        self.assertDictEqual(latest_job_exes, expected_result, 'latest job executions do not match expected results')


class TestJobType(TransactionTestCase):

    def setUp(self):
        django.setup()

        seed_interface_str = \
            """
            {
              "seedVersion": "1.0.0",
              "job": {
                "name": "test",
                "jobVersion": "1.0.0",
                "packageVersion": "1.0.0",
                "title": "Test job to exercise Seed functionality",
                "description": "Reads input file and ",
                "tags": [
                  "testing",
                  "seed"
                ],
                "maintainer": {
                  "name": "John Doe",
                  "organization": "E-corp",
                  "email": "jdoe@example.com",
                  "url": "http://www.example.com",
                  "phone": "666-555-4321"
                },
                "timeout": 3600,
                "interface": {
                  "command": "${INPUT_TEXT} ${INPUT_FILES} ${READ_LENGTH}",
                  "inputs": {
                    "files": [
                      {
                        "name": "INPUT_TEXT",
                        "mediaTypes": [
                          "text/plain"
                        ],
                        "partial": true
                      },
                      {
                        "name": "INPUT_FILES",
                        "multiple": true
                      }
                    ],
                    "json": [
                      {
                        "name": "READ_LENGTH",
                        "type": "integer"
                      },
                      {
                        "name": "OUTPUT_COUNT",
                        "type": "integer"
                      }
                    ]
                  },
                  "outputs": {
                    "files": [
                      {
                        "name": "OUTPUT_FILES",
                        "mediaType": "text/plain",
                        "multiple": true,
                        "pattern": "output_files*.txt"
                      },
                      {
                        "name": "OUTPUT_TEXT",
                        "mediaType": "text/plain",
                        "pattern": "output_text.txt"
                      }
                    ],
                    "json": [
                      {
                        "name": "cell_count",
                        "key": "cellCount",
                        "type": "integer"
                      }
                    ]
                  },
                  "mounts": [
                    {
                      "name": "MOUNT_PATH",
                      "path": "/the/container/path",
                      "mode": "ro"
                    }
                  ],
                  "settings": [
                    {
                      "name": "DB_HOST",
                      "secret": false
                    },
                    {
                      "name": "DB_PASS",
                      "secret": true
                    }
                  ]
                },
                "resources": {
                  "scalar": [
                    { "name": "cpus", "value": 1.5 },
                    { "name": "mem", "value": 244.0 },
                    { "name": "sharedMem", "value": 1.0 },
                    { "name": "disk", "value": 11.0, "inputMultiplier": 4.0 }
                  ]
                },
                "errors": [
                  {
                    "code": 1,
                    "name": "data-issue",
                    "title": "Data Issue discovered",
                    "description": "There was a problem with input data",
                    "category": "data"
                  },
                  {
                    "code": 2,
                    "name": "missing-mount",
                    "title": "Missing mount",
                    "description": "Expected mount point not available at run time",
                    "category": "job"
                  },
                  {
                    "code": 3,
                    "name": "missing-setting",
                    "title": "Missing setting",
                    "description": "Expected setting not defined in environment variable",
                    "category": "job"
                  },
                  {
                    "code": 4,
                    "name": "missing-env",
                    "title": "Missing environment",
                    "description": "Expected environment not provided",
                    "category": "job"
                  }
                ]
              }
            }
        """

        self.seed_job_type = job_test_utils.create_job_type(interface=json.loads(seed_interface_str))
        self.legacy_job_type = job_test_utils.create_job_type()
        self.legacy_job_type.cpus_required = 5.0
        self.legacy_job_type.mem_const_required = 6.0
        self.legacy_job_type.mem_mult_required = 7.0
        self.legacy_job_type.shared_mem_required = 8.0
        self.legacy_job_type.disk_out_const_required = 9.0
        self.legacy_job_type.disk_out_mult_required = 10.0

    def test_get_legacy_cpu_resource_from_legacy_interface(self):
        job_type = self.legacy_job_type
        value = job_type.get_cpus_required()

        self.assertEqual(job_type.cpus_required, value)

    def test_get_legacy_mem_resource_from_legacy_interface(self):
        job_type = self.legacy_job_type
        value = job_type.get_mem_const_required()

        self.assertEqual(job_type.mem_const_required, value)

    def test_get_legacy_mem_resource_multiplier_from_legacy_interface(self):
        job_type = self.legacy_job_type
        value = job_type.get_mem_mult_required()

        self.assertEqual(job_type.mem_mult_required, value)

    def test_get_legacy_sharedmem_resource_from_legacy_interface(self):
        job_type = self.legacy_job_type
        value = job_type.get_shared_mem_required()

        self.assertEqual(job_type.shared_mem_required, value)

    def test_get_legacy_disk_resource_from_legacy_interface(self):
        job_type = self.legacy_job_type
        value = job_type.get_disk_out_const_required()

        self.assertEqual(job_type.disk_out_const_required, value)

    def test_get_legacy_disk_resource_multiplier_from_legacy_interface(self):
        job_type = self.legacy_job_type
        value = job_type.get_disk_out_mult_required()

        self.assertEqual(job_type.disk_out_mult_required, value)

    def test_get_legacy_cpu_resource_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_cpus_required()
        self.assertEqual(1.5, value)

    def test_get_legacy_cpu_resource_multiplier_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type._get_legacy_resource('cpus', job_type.cpus_required, False)

        self.assertEqual(0.0, value)

    def test_get_legacy_mem_resource_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_mem_const_required()

        self.assertEqual(244.0, value)

    def test_get_legacy_mem_resource_multiplier_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_mem_mult_required()

        self.assertEqual(0.0, value)

    def test_get_legacy_sharedmem_resource_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_shared_mem_required()

        self.assertEqual(1.0, value)

    def test_get_legacy_sharedmem_resource_multiplier_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type._get_legacy_resource('sharedmem', job_type.shared_mem_required, False)

        self.assertEqual(0.0, value)

    def test_get_legacy_disk_resource_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_disk_out_const_required()

        self.assertEqual(11.0, value)

    def test_get_legacy_disk_resource_multiplier_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_disk_out_mult_required()

        self.assertEqual(4.0, value)

    def test_get_tagged_docker_image_from_tagged_image(self):
        job_type = self.seed_job_type
        job_type.docker_image = 'image:tag'

        # Should pull from packageVersion of Seed Manifest
        self.assertEqual('image:1.0.0', job_type.get_tagged_docker_image())

    def test_get_tagged_docker_image_from_untagged_image(self):
        job_type = self.seed_job_type
        job_type.docker_image = 'image'

        # Should pull from packageVersion of Seed Manifest
        self.assertEqual('image:1.0.0', job_type.get_tagged_docker_image())

    def test_get_tagged_docker_image_from_docker_image_legacy_job_type(self):
        job_type = self.legacy_job_type
        job_type.docker_image = 'image:tag'

        # Should ONLY use docker_image field with legacy job type
        self.assertEqual('image:tag', job_type.get_tagged_docker_image())

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

        self.error_mapping = create_legacy_error_mapping({
            'version': '1.0',
            'exit_codes': {
                '-15': self.error.name,
            }
        })

    def test_successful_no_trigger_rule(self):
        """Tests calling JobTypeManager.create_job_type_v5() successfully with no trigger rule or error mapping"""

        name = 'my-job-type'
        version = '1.0'

        # Call test
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertIsNone(job_type.trigger_rule_id)
        self.assertSetEqual(set(job_type.get_error_mapping()._mapping.keys()), set())

    def test_successful_with_trigger_rule(self):
        """Tests calling JobTypeManager.create_job_type_v5() successfully with a trigger rule and error mapping"""

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())

        # Call test
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule, self.error_mapping)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertEqual(job_type.trigger_rule_id, trigger_rule.id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule.id)
        self.assertTrue(trigger_rule.is_active)
        self.assertSetEqual(set(job_type.get_error_mapping()._mapping.keys()), {-15})

    def test_invalid_trigger_rule(self):
        """Tests calling JobTypeManager.create_job_type_v5() with an invalid trigger rule"""

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_ERROR_TYPE,
                                                              configuration=self.trigger_config.get_dict())

        # Call test
        self.assertRaises(InvalidConnection, JobType.objects.create_job_type_v5, name, version, self.job_interface,
                          trigger_rule, self.error_mapping)

    def test_successful_other_fields(self):
        """Tests calling JobTypeManager.create_job_type_v5() successfully with additional fields"""

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        custom_resources = Resources({'resources': {'foo': 10.0}})
        docker_params = [["a","1"],["b","2"]]

        # Call test
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, title=title,
                                                      description=description, priority=priority,
                                                      docker_params=docker_params, custom_resources=custom_resources)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertIsNone(job_type.trigger_rule_id)
        self.assertSetEqual(set(job_type.get_error_mapping()._mapping.keys()), set())
        self.assertDictEqual(job_type.get_custom_resources().get_dict(), custom_resources.get_dict())
        self.assertEqual(job_type.description, description)
        self.assertEqual(job_type.priority, priority)
        self.assertIsNone(job_type.deprecated)
        self.assertIsNone(job_type.paused)
        self.assertEqual(job_type.docker_params, docker_params)

    def test_successful_paused(self):
        """Tests calling JobTypeManager.create_job_type_v5() and pausing it"""

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        is_paused = True

        # Call test
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, title=title,
                                                          description=description, priority=priority, is_paused=is_paused)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertDictEqual(job_type.get_job_interface().get_dict(), self.job_interface.get_dict())
        self.assertEqual(job_type.revision_num, 1)
        self.assertIsNone(job_type.trigger_rule_id)
        self.assertSetEqual(set(job_type.get_error_mapping()._mapping.keys()), set())
        self.assertEqual(job_type.description, description)
        self.assertEqual(job_type.priority, priority)
        self.assertEqual(job_type.is_paused, is_paused)
        self.assertIsNotNone(job_type.paused)

    def test_uneditable_field(self):
        """Tests calling JobTypeManager.create_job_type_v5() with an uneditable field"""

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        is_system = True

        # Call test
        self.assertRaises(Exception, JobType.objects.create_job_type_v5, name, version, self.job_interface, title=title,
                          description=description, priority=priority, is_system=is_system)

    def test_invalid_error_mapping(self):
        """Tests calling JobTypeManager.create_job_type_v5() with an invalid error mapping"""

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        is_system = True
        error_mapping = create_legacy_error_mapping({
            'version': '1.0',
            'exit_codes': {
                '1': 'test-invalid-error',
            }
        })

        # Call test
        self.assertRaises(Exception, JobType.objects.create_job_type_v5, name, version, self.job_interface,
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
        """Tests calling JobTypeManager.edit_job_type_v5() with a change to some general fields"""

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        priority = 12
        error_mapping = create_legacy_error_mapping({
            'version': '1.0',
            'exit_codes': {
                '-15': self.error.name,
            }
        })
        custom_resources = Resources({'resources': {'foo': 10.0}})
        new_title = 'my new title'
        new_priority = 13
        new_error_mapping = create_legacy_error_mapping({
            'version': '1.0',
            'exit_codes': {
                '-16': self.error.name,
            }
        })
        new_custom_resources = Resources({'resources': {'foo': 100.0}})
        new_is_paused = True
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule, title=title,
                                                          priority=priority, error_mapping=error_mapping,
                                                          custom_resources=custom_resources)

        # Call test
        JobType.objects.edit_job_type_v5(job_type.id, title=new_title, priority=new_priority,
                                             error_mapping=new_error_mapping, custom_resources=new_custom_resources,
                                             is_paused=new_is_paused)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertEqual(job_type.revision_num, 1)
        self.assertEqual(job_type.trigger_rule_id, trigger_rule.id)
        trigger_rule = TriggerRule.objects.get(pk=trigger_rule.id)
        self.assertTrue(trigger_rule.is_active)
        self.assertEqual(job_type.title, new_title)
        self.assertEqual(job_type.priority, new_priority)
        self.assertSetEqual(set(job_type.get_error_mapping()._mapping.keys()), {-16})
        self.assertDictEqual(job_type.get_custom_resources().get_dict(), new_custom_resources.get_dict())
        self.assertEqual(job_type.is_paused, new_is_paused)
        self.assertIsNotNone(job_type.paused)

    def test_change_to_interface(self):
        """Tests calling JobTypeManager.edit_job_type_v5() with a change to the interface"""

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule)

        # Call test
        JobType.objects.edit_job_type_v5(job_type.id, self.new_job_interface, None, False)

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
        """Tests calling JobTypeManager.edit_job_type_v5() with a change to the trigger rule"""

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        new_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                                  configuration=self.new_trigger_config.get_dict())
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule)

        # Call test
        JobType.objects.edit_job_type_v5(job_type.id, None, new_trigger_rule, False)

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
        """Tests calling JobTypeManager.edit_job_type_v5() that removes the trigger rule"""

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule)

        # Call test
        JobType.objects.edit_job_type_v5(job_type.id, None, None, True)

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
        """Tests calling JobTypeManager.edit_job_type_v5() with a change to both the definition and the trigger rule
        """

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        new_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                                  configuration=self.new_trigger_config.get_dict())
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule)

        # Call test
        JobType.objects.edit_job_type_v5(job_type.id, self.new_job_interface, new_trigger_rule, False)

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
        """Tests calling JobTypeManager.edit_job_type_v5() with a new invalid trigger rule"""

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        new_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_ERROR_TYPE,
                                                                  configuration=self.new_trigger_config.get_dict())
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule)

        # Call test
        self.assertRaises(InvalidConnection, JobType.objects.edit_job_type_v5, job_type.id, self.new_job_interface,
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
        """Tests calling JobTypeManager.edit_job_type_v5() for a system job type"""

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        new_title = 'my new title'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule, title=title)
        job_type.is_system = True
        job_type.save()

        # Call test
        self.assertRaises(Exception, JobType.objects.edit_job_type_v5, job_type.id, title=new_title)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        # No Change
        self.assertEqual(job_type.title, title)

    def test_pause_system_job_type(self):
        """Tests calling JobTypeManager.edit_job_type_v5() and pausing a system job type"""

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule, is_paused=False)
        job_type.is_system = True
        job_type.save()

        # Call test
        JobType.objects.edit_job_type_v5(job_type.id, is_paused=True)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        self.assertEqual(job_type.is_paused, True)

    def test_uneditable_field(self):
        """Tests calling JobTypeManager.edit_job_type_v5() to change an uneditable field"""

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        new_title = 'my new title'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_TYPE,
                                                              configuration=self.trigger_config.get_dict())
        job_type = JobType.objects.create_job_type_v5(name, version, self.job_interface, trigger_rule, title=title)

        # Call test
        self.assertRaises(Exception, JobType.objects.edit_job_type_v5, job_type.id, title=new_title, is_system=True)

        # Check results
        job_type = JobType.objects.select_related('trigger_rule').get(pk=job_type.id)
        # No change
        self.assertEqual(job_type.title, title)

    def test_invalid_error_mapping(self):
        """Tests calling JobTypeManager.edit_job_type_v5() with an invalid error mapping"""

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        is_system = True
        error_mapping = create_legacy_error_mapping({
            'version': '1.0',
            'exit_codes': {
                '1': 'test-invalid-error',
            }
        })

        # Call test
        self.assertRaises(Exception, JobType.objects.edit_job_type_v5, name, version, self.job_interface,
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

        self.error_mapping = create_legacy_error_mapping({
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
        self.invalid_trigger_config = job_test_utils.MockErrorTriggerRuleConfiguration(job_test_utils.MOCK_ERROR_TYPE,
                                                                                       self.configuration)
        self.invalid_trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_ERROR_TYPE,
                                                                   configuration=self.trigger_config.get_dict())

    def test_successful(self):
        """Tests calling JobTypeManager.validate_job_type_v5() successfully"""

        warnings = JobType.objects.validate_job_type_v5('name', '1.0', self.interface, self.error_mapping,
                                                     self.trigger_config)

        # Check results
        self.assertListEqual(warnings, [])

    def test_invalid(self):
        """Tests calling JobTypeManager.validate_job_type_v5() with an invalid trigger rule"""

        self.assertRaises(InvalidConnection, JobType.objects.validate_job_type_v5, 'name', '1.0', self.interface,
                          self.error_mapping, self.invalid_trigger_config)


class TestJobTypeRunningStatus(TestCase):

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type(name='Type 1', version='1.0')
        self.job_type_2 = job_test_utils.create_job_type(name='Type 2', version='2.0')
        self.job_type_3 = job_test_utils.create_job_type(name='Type 1', version='2.0')

        self.entry_1_longest = datetime.datetime.utcfromtimestamp(500000).replace(tzinfo=timezone.utc)
        self.entry_1_shortest = datetime.datetime.utcfromtimestamp(650000).replace(tzinfo=timezone.utc)
        self.entry_2_longest = datetime.datetime.utcfromtimestamp(600000).replace(tzinfo=timezone.utc)
        self.entry_2_shortest = datetime.datetime.utcfromtimestamp(750000).replace(tzinfo=timezone.utc)
        self.entry_3_longest = datetime.datetime.utcfromtimestamp(700000).replace(tzinfo=timezone.utc)
        self.entry_3_shortest = datetime.datetime.utcfromtimestamp(800000).replace(tzinfo=timezone.utc)

        job_test_utils.create_job(job_type=self.job_type_1, status='RUNNING', last_status_change=self.entry_1_longest)
        job_test_utils.create_job(job_type=self.job_type_1, status='RUNNING', last_status_change=self.entry_1_shortest)

        job_test_utils.create_job(job_type=self.job_type_2, status='RUNNING', last_status_change=self.entry_2_shortest)
        job_test_utils.create_job(job_type=self.job_type_2, status='RUNNING', last_status_change=self.entry_2_longest)
        job_test_utils.create_job(job_type=self.job_type_2, status='RUNNING', last_status_change=self.entry_2_shortest)

        job_test_utils.create_job(job_type=self.job_type_3, status='RUNNING', last_status_change=self.entry_3_shortest)
        job_test_utils.create_job(job_type=self.job_type_3, status='RUNNING', last_status_change=self.entry_3_longest)
        job_test_utils.create_job(job_type=self.job_type_3, status='RUNNING', last_status_change=self.entry_3_longest)
        job_test_utils.create_job(job_type=self.job_type_3, status='RUNNING', last_status_change=self.entry_3_shortest)

    def test_successful(self):
        """Tests calling the get_running_job_status method on JobExecutionManager."""

        status = JobType.objects.get_running_status()
        self.assertEqual(len(status), 3)

        # Check entry 1
        self.assertEqual(status[0].job_type.id, self.job_type_1.id)
        self.assertEqual(status[0].job_type.name, 'Type 1')
        self.assertEqual(status[0].job_type.version, '1.0')
        self.assertEqual(status[0].count, 2)
        self.assertEqual(status[0].longest_running, self.entry_1_longest)

        # Check entry 2
        self.assertEqual(status[1].job_type.id, self.job_type_2.id)
        self.assertEqual(status[1].job_type.name, 'Type 2')
        self.assertEqual(status[1].job_type.version, '2.0')
        self.assertEqual(status[1].count, 3)
        self.assertEqual(status[1].longest_running, self.entry_2_longest)

        # Check entry 3
        self.assertEqual(status[2].job_type.id, self.job_type_3.id)
        self.assertEqual(status[2].job_type.name, 'Type 1')
        self.assertEqual(status[2].job_type.version, '2.0')
        self.assertEqual(status[2].count, 4)
        self.assertEqual(status[2].longest_running, self.entry_3_longest)


class TestJobTypeFailedStatus(TestCase):

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type(name='Type 1', version='1.0')
        self.job_type_2 = job_test_utils.create_job_type(name='Type 2', version='2.0')
        self.job_type_3 = job_test_utils.create_job_type(name='Type 1', version='2.0')

        self.error_1 = Error.objects.create(name='Error 1', description='Test', category='SYSTEM')
        self.error_2 = Error.objects.create(name='Error 2', description='Test', category='SYSTEM')
        self.error_3 = Error.objects.create(name='Error 3', description='Test', category='DATA')

        # Date stamps for errors
        self.entry_1_last_time = datetime.datetime.utcfromtimestamp(590000).replace(tzinfo=timezone.utc)
        self.entry_1_first_time = datetime.datetime.utcfromtimestamp(580000).replace(tzinfo=timezone.utc)
        self.entry_2_time = datetime.datetime.utcfromtimestamp(585000).replace(tzinfo=timezone.utc)
        self.entry_3_last_time = datetime.datetime.utcfromtimestamp(490000).replace(tzinfo=timezone.utc)
        self.entry_3_mid_time = datetime.datetime.utcfromtimestamp(480000).replace(tzinfo=timezone.utc)
        self.entry_3_first_time = datetime.datetime.utcfromtimestamp(470000).replace(tzinfo=timezone.utc)
        self.entry_4_time = datetime.datetime.utcfromtimestamp(385000).replace(tzinfo=timezone.utc)

        # Create jobs
        job_test_utils.create_job(job_type=self.job_type_1, status='RUNNING', last_status_change=timezone.now())
        job_test_utils.create_job(job_type=self.job_type_1, error=self.error_1, status='FAILED',
                                  last_status_change=self.entry_2_time)
        job_test_utils.create_job(job_type=self.job_type_2, error=self.error_1, status='FAILED',
                                  last_status_change=self.entry_4_time)
        job_test_utils.create_job(job_type=self.job_type_2, error=self.error_2, status='FAILED',
                                  last_status_change=self.entry_1_last_time)
        job_test_utils.create_job(job_type=self.job_type_2, error=self.error_2, status='FAILED',
                                  last_status_change=self.entry_1_first_time)
        job_test_utils.create_job(job_type=self.job_type_3, error=self.error_2, status='FAILED',
                                  last_status_change=self.entry_3_mid_time)
        job_test_utils.create_job(job_type=self.job_type_3, error=self.error_2, status='FAILED',
                                  last_status_change=self.entry_3_last_time)
        job_test_utils.create_job(job_type=self.job_type_3, error=self.error_2, status='FAILED',
                                  last_status_change=self.entry_3_first_time)
        job_test_utils.create_job(job_type=self.job_type_3, error=self.error_3, status='FAILED',
                                  last_status_change=timezone.now())

    def test_successful(self):
        """Tests calling the get_failed_jobs_with_system_errors method on JobManager."""

        status = JobType.objects.get_failed_status()
        self.assertEqual(len(status), 4)

        # Check entry 1
        self.assertEqual(status[0].job_type.id, self.job_type_2.id)
        self.assertEqual(status[0].job_type.name, 'Type 2')
        self.assertEqual(status[0].job_type.version, '2.0')
        self.assertEqual(status[0].error.name, 'Error 2')
        self.assertEqual(status[0].count, 2)
        self.assertEqual(status[0].first_error, self.entry_1_first_time)
        self.assertEqual(status[0].last_error, self.entry_1_last_time)

        # Check entry 2
        self.assertEqual(status[1].job_type.id, self.job_type_1.id)
        self.assertEqual(status[1].job_type.name, 'Type 1')
        self.assertEqual(status[1].job_type.version, '1.0')
        self.assertEqual(status[1].error.name, 'Error 1')
        self.assertEqual(status[1].count, 1)
        self.assertEqual(status[1].first_error, self.entry_2_time)
        self.assertEqual(status[1].last_error, self.entry_2_time)

        # Check entry 3
        self.assertEqual(status[2].job_type.id, self.job_type_3.id)
        self.assertEqual(status[2].job_type.name, 'Type 1')
        self.assertEqual(status[2].job_type.version, '2.0')
        self.assertEqual(status[2].error.name, 'Error 2')
        self.assertEqual(status[2].count, 3)
        self.assertEqual(status[2].first_error, self.entry_3_first_time)
        self.assertEqual(status[2].last_error, self.entry_3_last_time)

        # Check entry 4
        self.assertEqual(status[3].job_type.id, self.job_type_2.id)
        self.assertEqual(status[3].job_type.name, 'Type 2')
        self.assertEqual(status[3].job_type.version, '2.0')
        self.assertEqual(status[3].error.name, 'Error 1')
        self.assertEqual(status[3].count, 1)
        self.assertEqual(status[3].first_error, self.entry_4_time)
        self.assertEqual(status[3].last_error, self.entry_4_time)

class TestJobTypeTagManager(TransactionTestCase):
    
    def setUp(self):
        django.setup()

        self.job_type1 = "test-type1"
        self.tag_set1 = ["tag1", "tag2", "oneandfour"]
        self.job_type2 = "test-type2"
        self.tag_set2 = ["tag3", "tag4"]
        self.job_type3 = "test-type3"
        self.tag_set3 = ["tag5", "tag6"]
        self.job_type4 = "test-type4"
        self.tag_set4 = ["tag7", "tag8", "oneandfour"]
        JobTypeTag.objects.create_job_type_tags(self.job_type1, self.tag_set1)
        JobTypeTag.objects.create_job_type_tags(self.job_type3, self.tag_set3)
        JobTypeTag.objects.create_job_type_tags(self.job_type4, self.tag_set4)
        
    def test_create_job_type_tags(self):
        """Tests calling JobTypeManager.create_job_type_tags()"""
        
        result = JobTypeTag.objects.create_job_type_tags(self.job_type2, self.tag_set2)
        
        self.assertEqual(len(result), 2)
        
    def test_clear_job_type_tags(self):
        """Tests calling JobTypeManager.clear_job_type_tags()"""
        
        tags = JobTypeTag.objects.get_tags(self.job_type3)
        
        self.assertEqual(tags, self.tag_set3)
        
        JobTypeTag.objects.clear_job_type_tags(self.job_type3)
        
        tags = JobTypeTag.objects.get_tags(self.job_type3)
        
        self.assertEqual(len(tags), 0)
        
    def test_get_job_type_tags(self):
        """Tests calling JobTypeManager.clear_job_type_tags()"""
        
        tags = JobTypeTag.objects.get_tags(self.job_type1)
        
        self.assertEqual(tags, self.tag_set1)
        
    def test_get_tagged_job_types(self):
        """Tests calling JobTypeManager.get_tagged_job_types()"""
        
        job_types = JobTypeTag.objects.get_tagged_job_types(["tag1", "tag2"])
        
        self.assertEqual(len(job_types), 1)
        self.assertEqual(job_types[0], self.job_type1)

    def test_get_matching_job_types(self):
        """Tests calling JobTypeManager.get_matching_job_types()"""
      
        job_types = JobTypeTag.objects.get_matching_job_types("no-match")
        self.assertEqual(len(job_types), 0)
        
        job_types = JobTypeTag.objects.get_matching_job_types("one")
        self.assertEqual(len(job_types), 2)
        self.assertEqual(job_types[0], self.job_type1)
        
        job_types = JobTypeTag.objects.get_matching_job_types("tag1")
        self.assertEqual(len(job_types), 1)
        self.assertEqual(job_types[0], self.job_type1)