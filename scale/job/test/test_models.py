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
from data.data.data import Data
from data.data.json.data_v6 import convert_data_to_v6_json
from error.models import Error
from job.configuration.data.exceptions import InvalidConnection
from job.configuration.data.job_data import JobData
from job.configuration.interface.job_interface import JobInterface
from job.configuration.results.job_results import JobResults
from job.error.mapping import create_legacy_error_mapping
from job.seed.results.job_results import JobResults as SeedJobResults
from job.models import Job, JobExecution, JobExecutionOutput, JobInputFile, JobType, JobTypeRevision, JobTypeTag
from node.resources.json.resources import Resources


# TODO: Remove before release, just for reference (v5, v6)
# {
#     'command': '${INPUT_IMAGE} ${OUTPUT_DIR}',
#     'inputs': {
#         'files': [{'name': 'INPUT_IMAGE', 'mediaTypes': ['image/png'], 'required': True}]
#     },
#     'outputs': {
#         'files': [{'name': 'OUTPUT_IMAGE', 'pattern': '*_watermark.png', 'mediaType': 'image/png'}]
#     },
#     'mounts': [
#       {
#         'name': 'MOUNT_PATH',
#         'path': '/the/container/path',
#         'mode': 'ro'
#       }
#     ],
#     'settings': [
#       {
#         'name': 'VERSION',
#         'secret': False
#       },
#       {
#         'name': 'DB_HOST',
#         'secret': False
#       },
#       {
#         'name': 'DB_PASS',
#       'secret': True
#       }
#     ]
# }

class TestJobManager(TransactionTestCase):

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
        s_class = 'A'
        s_sensor = '1'
        collection = '12345'
        task = 'abcd'
        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace, file_size=10485760.0,
                                                source_sensor_class=s_class, source_sensor=s_sensor,
                                                source_collection=collection, source_task=task)
        file_2 = storage_test_utils.create_file(workspace=workspace, file_size=104857600.0,
                                                source_started=date_2, source_ended=date_3,
                                                source_sensor_class = s_class, source_sensor = s_sensor,
                                                source_collection = collection, source_task=task)
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
        file_10 = storage_test_utils.create_file(workspace=workspace, file_size=0.154, source_ended=date_4,
                                                 source_sensor_class=s_class, source_sensor=s_sensor,
                                                 source_collection=collection, source_task=task)
        interface = {
            'command': 'my_command',
            'inputs': {
                'files': [{
                    'name': 'Input 1',
                    'mediaTypes': ['text/plain'],
                }, {
                    'name': 'Input 2',
                    'mediaTypes': ['text/plain'],
                }]
            },
            'outputs': {
                'files': [{
                    'name': 'Output 1',
                    'mediaType': 'image/png',
            }]}}
        job_type = job_test_utils.create_seed_job_type(interface=interface)

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
        self.assertEqual(job_1.source_sensor_class, s_class)
        self.assertEqual(job_1.source_sensor, s_sensor)
        self.assertEqual(job_1.source_collection, collection)
        self.assertEqual(job_1.source_task, task)
        self.assertEqual(job_2.input_file_size, 113269857.0)
        self.assertEqual(job_2.source_started, min_src_started_job_2)
        self.assertEqual(job_2.source_ended, max_src_ended_job_2)
        self.assertEqual(job_2.source_sensor_class, s_class)
        self.assertEqual(job_2.source_sensor, s_sensor)
        self.assertEqual(job_2.source_collection, collection)
        self.assertEqual(job_2.source_task, task)

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

        data_dict = convert_data_to_v6_json(Data()).get_dict()
        job = job_test_utils.create_job(num_exes=1, status='CANCELED', input=data_dict, started=timezone.now(),
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
        Job.objects.supersede_jobs([job.id], timezone.now())

        job_ids = Job.objects.update_jobs_to_queued([job], timezone.now())
        job = Job.objects.get(pk=job.id)

        self.assertListEqual(job_ids, [])
        self.assertEqual(job.status, 'FAILED')
        self.assertTrue(job.is_superseded)

    def test_superseded_job(self):
        """Tests creating a job that supersedes another job"""

        old_job = job_test_utils.create_job()

        event = trigger_test_utils.create_trigger_event()
        new_job = Job.objects.create_job_v6(old_job.job_type_rev, event.id, superseded_job=old_job)
        new_job.save()
        when = timezone.now()
        Job.objects.supersede_jobs([old_job.id], when)

        new_job = Job.objects.get(pk=new_job.id)
        self.assertEqual(new_job.status, 'PENDING')
        self.assertFalse(new_job.is_superseded)
        self.assertEqual(new_job.root_superseded_job_id, old_job.id)
        self.assertEqual(new_job.superseded_job_id, old_job.id)
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

        self.seed_job_type = job_test_utils.create_seed_job_type(manifest=json.loads(seed_interface_str))



    def test_get_seed_cpu_resource_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_resources().get_json().get_dict()
        self.assertEqual(1.5, value['resources']['cpus'])

    def test_get_seed_mem_resource_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_resources().get_json().get_dict()

        self.assertEqual(244.0, value['resources']['mem'])

    def test_get_seed_sharedmem_resource_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_resources().get_json().get_dict()

        self.assertEqual(1.0, value['resources']['sharedmem'])

    def test_get_seed_disk_resource_from_seed_interface(self):
        job_type = self.seed_job_type
        value = job_type.get_resources().get_json().get_dict()

        self.assertEqual(11.0, value['resources']['disk'])

    def test_get_job_version_array(self):
        job_type = self.seed_job_type
        version = '1.0.0'
        value = job_type.get_job_version_array(version)
        self.assertEqual([1,0,0,None], value)

        version = '1.0.0-0'
        value = job_type.get_job_version_array(version)
        self.assertEqual([1,0,0,0], value)

        version = '1.0.0-alpha'
        value = job_type.get_job_version_array(version)
        self.assertEqual([1,0,0,97], value)

        version = '1.0'
        value = job_type.get_job_version_array(version)
        self.assertEqual([0,0,0,0], value)


class TestJobTypeRevision(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.seed_job_type = job_test_utils.create_seed_job_type()
        self.seed_job_type_rev = JobTypeRevision.objects.get_revision(self.seed_job_type.name,
                                                                      self.seed_job_type.version,
                                                                      self.seed_job_type.revision_num)

    def test_revision_get_input_interface(self):
        self.assertEqual(self.seed_job_type_rev.get_input_interface().parameters['INPUT_IMAGE'].PARAM_TYPE, 'file')

    def test_revision_get_output_interface(self):
        self.assertEqual(self.seed_job_type_rev.get_output_interface().parameters['OUTPUT_IMAGE'].PARAM_TYPE, 'file')


class TestJobTypeRunningStatus(TestCase):

    def setUp(self):
        django.setup()

        manifest1 = job_test_utils.create_seed_manifest(name='type-1', jobVersion='1.0.0')
        self.job_type_1 = job_test_utils.create_seed_job_type(manifest=manifest1)
        manifest2 = job_test_utils.create_seed_manifest(name='type-2', jobVersion='2.0.0')
        self.job_type_2 = job_test_utils.create_seed_job_type(manifest=manifest2)
        manifest3 = job_test_utils.create_seed_manifest(name='type-1', jobVersion='2.0.0')
        self.job_type_3 = job_test_utils.create_seed_job_type(manifest=manifest3)

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
        self.assertEqual(status[0].job_type.name, 'type-1')
        self.assertEqual(status[0].job_type.version, '1.0.0')
        self.assertEqual(status[0].count, 2)
        self.assertEqual(status[0].longest_running, self.entry_1_longest)

        # Check entry 2
        self.assertEqual(status[1].job_type.id, self.job_type_2.id)
        self.assertEqual(status[1].job_type.name, 'type-2')
        self.assertEqual(status[1].job_type.version, '2.0.0')
        self.assertEqual(status[1].count, 3)
        self.assertEqual(status[1].longest_running, self.entry_2_longest)

        # Check entry 3
        self.assertEqual(status[2].job_type.id, self.job_type_3.id)
        self.assertEqual(status[2].job_type.name, 'type-1')
        self.assertEqual(status[2].job_type.version, '2.0.0')
        self.assertEqual(status[2].count, 4)
        self.assertEqual(status[2].longest_running, self.entry_3_longest)


class TestJobTypeFailedStatus(TestCase):

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_seed_job_type(job_version='1.0')
        self.job_type_2 = job_test_utils.create_seed_job_type(job_version='2.0')
        self.job_type_3 = job_test_utils.create_seed_job_type(job_version='2.0')

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
        self.assertEqual(status[0].job_type.version, '2.0')
        self.assertEqual(status[0].error.name, 'Error 2')
        self.assertEqual(status[0].count, 2)
        self.assertEqual(status[0].first_error, self.entry_1_first_time)
        self.assertEqual(status[0].last_error, self.entry_1_last_time)

        # Check entry 2
        self.assertEqual(status[1].job_type.id, self.job_type_1.id)
        self.assertEqual(status[1].job_type.version, '1.0')
        self.assertEqual(status[1].error.name, 'Error 1')
        self.assertEqual(status[1].count, 1)
        self.assertEqual(status[1].first_error, self.entry_2_time)
        self.assertEqual(status[1].last_error, self.entry_2_time)

        # Check entry 3
        self.assertEqual(status[2].job_type.id, self.job_type_3.id)
        self.assertEqual(status[2].job_type.version, '2.0')
        self.assertEqual(status[2].error.name, 'Error 2')
        self.assertEqual(status[2].count, 3)
        self.assertEqual(status[2].first_error, self.entry_3_first_time)
        self.assertEqual(status[2].last_error, self.entry_3_last_time)

        # Check entry 4
        self.assertEqual(status[3].job_type.id, self.job_type_2.id)
        self.assertEqual(status[3].job_type.version, '2.0')
        self.assertEqual(status[3].error.name, 'Error 1')
        self.assertEqual(status[3].count, 1)
        self.assertEqual(status[3].first_error, self.entry_4_time)
        self.assertEqual(status[3].last_error, self.entry_4_time)

class TestJobTypeTagManager(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.job_type1 = job_test_utils.create_seed_job_type()
        self.tag_set1 = ["tag1", "tag2", "oneandfour"]
        self.job_type2 = job_test_utils.create_seed_job_type()
        self.tag_set2 = ["tag3", "tag4"]
        self.job_type3 = job_test_utils.create_seed_job_type()
        self.tag_set3 = ["tag5", "tag6"]
        self.job_type4 = job_test_utils.create_seed_job_type()
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

        tags = [jt_tag.tag for jt_tag in JobTypeTag.objects.filter(job_type_id=self.job_type3.id)]

        self.assertListEqual(tags, self.tag_set3)

        JobTypeTag.objects.clear_job_type_tags(self.job_type3.id)

        tags = [jt_tag.tag for jt_tag in JobTypeTag.objects.filter(job_type_id=self.job_type3.id)]

        self.assertEqual(len(tags), 0)
