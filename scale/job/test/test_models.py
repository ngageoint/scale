from __future__ import unicode_literals

import datetime

import django
import django.utils.timezone as timezone
from django.conf import settings
from django.test import TestCase, TransactionTestCase

import error.test.utils as error_test_utils
import job.test.utils as job_test_utils
import node.test.utils as node_test_utils
import storage.test.utils as storage_test_utils
import trigger.test.utils as trigger_test_utils
from error.models import Error
from job.configuration.configuration.job_configuration import DockerParam, JobConfiguration, MODE_RO, MODE_RW
from job.configuration.data.exceptions import InvalidConnection
from job.configuration.data.job_data import JobData
from job.configuration.interface.error_interface import ErrorInterface
from job.configuration.interface.job_interface import JobInterface
from job.execution import container
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH
from job.models import Job, JobExecution, JobType, JobTypeRevision
from job.resources import JobResources
from storage.container import get_workspace_volume_path
from trigger.models import TriggerRule


class TestJobManager(TransactionTestCase):

    def setUp(self):
        django.setup()

    def test_populate_job_data(self):
        """Tests calling JobManager.populate_job_data()"""

        workspace_1 = storage_test_utils.create_workspace()
        workspace_2 = storage_test_utils.create_workspace()
        workspace_3 = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file(workspace=workspace_1)
        file_2 = storage_test_utils.create_file(workspace=workspace_2)
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
        job = job_test_utils.create_job(job_type=job_type, status='PENDING')
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

        # Check that the correct workspaces are configured for the job
        # Make sure both workspaces will be used for the pre-task in read-only mode
        pre_task_workspaces = job.get_job_configuration().get_pre_task_workspaces()
        self.assertEqual(len(pre_task_workspaces), 2)
        name_set = set()
        for workspace in pre_task_workspaces:
            name_set.add(workspace.name)
            self.assertEqual(workspace.mode, MODE_RO)
        self.assertSetEqual(name_set, {workspace_1.name, workspace_2.name})
        # Make sure both workspaces will be used for the job-task in read-only mode
        job_task_workspaces = job.get_job_configuration().get_job_task_workspaces()
        self.assertEqual(len(job_task_workspaces), 2)
        name_set = set()
        for workspace in job_task_workspaces:
            name_set.add(workspace.name)
            self.assertEqual(workspace.mode, MODE_RO)
        self.assertSetEqual(name_set, {workspace_1.name, workspace_2.name})
        # Make sure all input and output workspaces will be used for the post-task and they are in read-write mode
        post_task_workspaces = job.get_job_configuration().get_post_task_workspaces()
        self.assertEqual(len(post_task_workspaces), 3)
        name_set = set()
        for workspace in post_task_workspaces:
            name_set.add(workspace.name)
            self.assertEqual(workspace.mode, MODE_RW)
        self.assertSetEqual(name_set, {workspace_1.name, workspace_2.name, workspace_3.name})

    def test_queue_job_timestamps(self):
        """Tests that job attributes are updated when a job is queued."""
        job = job_test_utils.create_job(num_exes=1, data={}, started=timezone.now(), ended=timezone.now())

        Job.objects.queue_jobs([job], timezone.now())

        self.assertEqual(job.status, 'QUEUED')
        self.assertIsNotNone(job.queued)
        self.assertIsNone(job.started)
        self.assertIsNone(job.ended)

    def test_queue_superseded_jobs(self):
        """Tests that JobManager.queue_jobs() does not queue superseded jobs"""

        job = job_test_utils.create_job(status='FAILED')
        Job.objects.supersede_jobs([job], timezone.now())

        job_exes = Job.objects.queue_jobs([job], timezone.now())
        job = Job.objects.get(pk=job.id)

        self.assertListEqual(job_exes, [])
        self.assertEqual(job.status, 'FAILED')
        self.assertTrue(job.is_superseded)

    def test_supersede_jobs(self):
        """Tests calling JobManager.supersede_jobs()"""

        job_1 = job_test_utils.create_job(status='PENDING')
        job_2 = job_test_utils.create_job(status='BLOCKED')
        job_3 = job_test_utils.create_job(status='RUNNING')
        job_4 = job_test_utils.create_job(status='COMPLETED')
        when = timezone.now()

        Job.objects.supersede_jobs([job_1, job_2, job_3, job_4], when)

        job_1 = Job.objects.get(pk=job_1.id)
        self.assertTrue(job_1.is_superseded)
        self.assertEqual(job_1.superseded, when)
        self.assertEqual(job_1.status, 'CANCELED')  # PENDING job should be CANCELED when superseded
        job_2 = Job.objects.get(pk=job_2.id)
        self.assertTrue(job_2.is_superseded)
        self.assertEqual(job_2.superseded, when)
        self.assertEqual(job_2.status, 'CANCELED')  # BLOCKED job should be CANCELED when superseded
        job_3 = Job.objects.get(pk=job_3.id)
        self.assertTrue(job_3.is_superseded)
        self.assertEqual(job_3.superseded, when)
        self.assertEqual(job_3.status, 'RUNNING')
        job_4 = Job.objects.get(pk=job_4.id)
        self.assertTrue(job_4.is_superseded)
        self.assertEqual(job_4.superseded, when)
        self.assertEqual(job_4.status, 'COMPLETED')

    def test_superseded_job(self):
        """Tests creating a job that supersedes another job"""

        old_job = job_test_utils.create_job()

        event = trigger_test_utils.create_trigger_event()
        new_job = Job.objects.create_job(old_job.job_type, event, old_job, False)
        new_job.save()
        when = timezone.now()
        Job.objects.supersede_jobs([old_job], when)

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

    def test_is_ready_to_queue(self):
        """Tests checking the job status for queue eligibility."""
        self.assertTrue(Job(status='PENDING').is_ready_to_queue)
        self.assertFalse(Job(status='BLOCKED').is_ready_to_queue)
        self.assertFalse(Job(status='QUEUED').is_ready_to_queue)
        self.assertFalse(Job(status='RUNNING').is_ready_to_queue)
        self.assertTrue(Job(status='FAILED').is_ready_to_queue)
        self.assertFalse(Job(status='COMPLETED').is_ready_to_queue)
        self.assertTrue(Job(status='CANCELED').is_ready_to_queue)

    def test_is_ready_to_requeue(self):
        """Tests checking the job status for requeue eligibility."""
        self.assertFalse(Job(status='PENDING').is_ready_to_requeue)
        self.assertFalse(Job(status='BLOCKED').is_ready_to_requeue)
        self.assertFalse(Job(status='QUEUED').is_ready_to_requeue)
        self.assertFalse(Job(status='RUNNING').is_ready_to_requeue)
        self.assertTrue(Job(status='FAILED').is_ready_to_requeue)
        self.assertFalse(Job(status='COMPLETED').is_ready_to_requeue)
        self.assertTrue(Job(status='CANCELED').is_ready_to_requeue)

    def test_increase_max_tries_canceled(self):
        """Tests increasing the maximum number of tries for a job instance that was canceled prematurely."""
        job_type = JobType(max_tries=10)
        job = Job(job_type=job_type, num_exes=3, max_tries=5)
        job.increase_max_tries()

        self.assertEqual(job.max_tries, 13)

    def test_increase_max_tries_failed(self):
        """Tests increasing the maximum number of tries for a job instance that ran out of tries due to failures."""
        job_type = JobType(max_tries=10)
        job = Job(job_type=job_type, num_exes=5, max_tries=5)
        job.increase_max_tries()

        self.assertEqual(job.max_tries, 15)


class TestJobExecutionManager(TransactionTestCase):
    """Tests for the job execution model manager"""

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

        self.job_type_1 = job_test_utils.create_job_type()
        self.job_type_2 = job_test_utils.create_job_type()

        self.job_1a = job_test_utils.create_job(job_type=self.job_type_1)
        job_test_utils.create_job_exe(job=self.job_1a, status='FAILED')
        job_test_utils.create_job_exe(job=self.job_1a, status='FAILED')
        job_test_utils.create_job_exe(job=self.job_1a, status='COMPLETED')
        self.last_run_1a = job_test_utils.create_job_exe(job=self.job_1a, status='RUNNING')

        self.job_1b = job_test_utils.create_job(job_type=self.job_type_1, status='FAILED')
        self.last_run_1b = job_test_utils.create_job_exe(job=self.job_1b, status='FAILED')

        self.job_2a = job_test_utils.create_job(job_type=self.job_type_2)
        job_test_utils.create_job_exe(job=self.job_2a, status='FAILED')
        job_test_utils.create_job_exe(job=self.job_2a, status='FAILED')
        job_test_utils.create_job_exe(job=self.job_2a, status='COMPLETED')
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

    def test_schedule_job_executions(self):
        job_exe_1 = job_test_utils.create_job_exe(status='QUEUED')
        job_exe_2 = job_test_utils.create_job_exe(status='QUEUED')

        node_1 = node_test_utils.create_node()
        node_2 = node_test_utils.create_node()
        resources_1 = JobResources(cpus=1, mem=2, disk_in=3, disk_out=4, disk_total=7)
        resources_2 = JobResources(cpus=10, mem=11, disk_in=12, disk_out=13, disk_total=25)

        job_exes = JobExecution.objects.schedule_job_executions('123', [(job_exe_1, node_1, resources_1),
                                                                        (job_exe_2, node_2, resources_2)], {})

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

    def test_schedule_job_executions_non_system_docker_params_host_broker(self):
        """Testing scheduling a job execution and checking Docker params for a non-system job that only uses a host
        broker for input
        """
        workspace = storage_test_utils.create_workspace(json_config={'broker': {'type': 'host', 'host_path': '/scale'}})
        configuration = JobConfiguration()
        configuration.add_pre_task_workspace(workspace.name, MODE_RO)
        configuration.add_job_task_workspace(workspace.name, MODE_RO)
        job_exe = job_test_utils.create_job_exe(status='QUEUED', configuration=configuration.get_dict())
        input_data_volume_ro = '%s:%s:ro' % (container.get_job_exe_input_vol_name('123', job_exe.id),
                                             SCALE_JOB_EXE_INPUT_PATH)
        input_data_volume_rw = '%s:%s:rw' % (container.get_job_exe_input_vol_name('123', job_exe.id),
                                             SCALE_JOB_EXE_INPUT_PATH)
        output_data_volume_rw = '%s:%s:rw' % (container.get_job_exe_output_vol_name('123', job_exe.id),
                                              SCALE_JOB_EXE_OUTPUT_PATH)
        output_data_volume_ro = '%s:%s:ro' % (container.get_job_exe_output_vol_name('123', job_exe.id),
                                              SCALE_JOB_EXE_OUTPUT_PATH)
        workspace_volume = '/scale:%s:ro' % get_workspace_volume_path(workspace.name)

        db = settings.DATABASES['default']
        env_vars = [DockerParam('env', 'SCALE_DB_NAME=' + db['NAME']),
                    DockerParam('env', 'SCALE_DB_USER=' + db['USER']),
                    DockerParam('env', 'SCALE_DB_PASS=' + db['PASSWORD']),
                    DockerParam('env', 'SCALE_DB_HOST=' + db['HOST']),
                    DockerParam('env', 'SCALE_DB_PORT=' + db['PORT'])]
        job_exe_pre_task_params = list(env_vars)
        job_exe_pre_task_params.extend([DockerParam('volume', input_data_volume_rw),
                                        DockerParam('volume', output_data_volume_rw),
                                        DockerParam('volume', workspace_volume)])
        job_exe_job_task_params = [DockerParam('volume', input_data_volume_ro),
                                   DockerParam('volume', output_data_volume_rw),
                                   DockerParam('volume', workspace_volume)]
        job_exe_post_task_params = list(env_vars)
        job_exe_post_task_params.extend([DockerParam('volume', output_data_volume_ro)])
        node = node_test_utils.create_node()
        resources = JobResources(cpus=10, mem=11, disk_in=12, disk_out=13, disk_total=25)
        workspaces = {workspace.name: workspace}

        job_exes = JobExecution.objects.schedule_job_executions('123', [(job_exe, node, resources)], workspaces)

        params = job_exes[0].get_job_configuration().get_pre_task_docker_params()
        self.assertEqual(len(params), len(job_exe_pre_task_params))
        for i in range(len(params)):
            param = params[i]
            expected_param = job_exe_pre_task_params[i]
            self.assertEqual(param.flag, expected_param.flag)
            self.assertEqual(param.value, expected_param.value)
        params = job_exes[0].get_job_configuration().get_job_task_docker_params()
        self.assertEqual(len(params), len(job_exe_job_task_params))
        for i in range(len(params)):
            param = params[i]
            expected_param = job_exe_job_task_params[i]
            self.assertEqual(param.flag, expected_param.flag)
            self.assertEqual(param.value, expected_param.value)
        params = job_exes[0].get_job_configuration().get_post_task_docker_params()
        self.assertEqual(len(params), len(job_exe_post_task_params))
        for i in range(len(params)):
            param = params[i]
            expected_param = job_exe_post_task_params[i]
            self.assertEqual(param.flag, expected_param.flag)
            self.assertEqual(param.value, expected_param.value)

    def test_schedule_job_executions_non_system_docker_params_nfs_broker(self):
        """Testing scheduling a job execution and checking Docker params for a non-system job that uses an NFS broker
        for input and output
        """
        workspace_1 = storage_test_utils.create_workspace(json_config={'broker': {'type': 'nfs',
                                                                                  'nfs_path': 'scale_1:/scale'}})
        workspace_2 = storage_test_utils.create_workspace(json_config={'broker': {'type': 'nfs',
                                                                                  'nfs_path': 'scale_2:/scale'}})
        configuration = JobConfiguration()
        configuration.add_pre_task_workspace(workspace_1.name, MODE_RO)
        configuration.add_job_task_workspace(workspace_1.name, MODE_RO)
        configuration.add_post_task_workspace(workspace_1.name, MODE_RW)
        configuration.add_post_task_workspace(workspace_2.name, MODE_RW)
        job_exe = job_test_utils.create_job_exe(status='QUEUED', configuration=configuration.get_dict())
        input_data_volume_ro = '%s:%s:ro' % (container.get_job_exe_input_vol_name('123', job_exe.id),
                                             SCALE_JOB_EXE_INPUT_PATH)
        input_data_volume_rw = '%s:%s:rw' % (container.get_job_exe_input_vol_name('123', job_exe.id),
                                             SCALE_JOB_EXE_INPUT_PATH)
        output_data_volume_ro = '%s:%s:ro' % (container.get_job_exe_output_vol_name('123', job_exe.id),
                                              SCALE_JOB_EXE_OUTPUT_PATH)
        output_data_volume_rw = '%s:%s:rw' % (container.get_job_exe_output_vol_name('123', job_exe.id),
                                              SCALE_JOB_EXE_OUTPUT_PATH)
        volume_name_1 = container.get_workspace_volume_name('123', job_exe.id, workspace_1.name)
        workspace_volume_1_create = '$(docker volume create --driver=nfs --name=%s scale_1/scale):%s:ro'
        workspace_volume_1_create = workspace_volume_1_create % (volume_name_1,
                                                                 get_workspace_volume_path(workspace_1.name))
        workspace_volume_1_ro = '%s:%s:ro' % (container.get_workspace_volume_name('123', job_exe.id, workspace_1.name),
                                              get_workspace_volume_path(workspace_1.name))
        workspace_volume_1_rw = '%s:%s:rw' % (container.get_workspace_volume_name('123', job_exe.id, workspace_1.name),
                                              get_workspace_volume_path(workspace_1.name))
        volume_name_2 = container.get_workspace_volume_name('123', job_exe.id, workspace_2.name)
        workspace_volume_2_create = '$(docker volume create --driver=nfs --name=%s scale_2/scale):%s:rw'
        workspace_volume_2_create = workspace_volume_2_create % (volume_name_2,
                                                                 get_workspace_volume_path(workspace_2.name))

        db = settings.DATABASES['default']
        env_vars = [DockerParam('env', 'SCALE_DB_NAME=' + db['NAME']),
                    DockerParam('env', 'SCALE_DB_USER=' + db['USER']),
                    DockerParam('env', 'SCALE_DB_PASS=' + db['PASSWORD']),
                    DockerParam('env', 'SCALE_DB_HOST=' + db['HOST']),
                    DockerParam('env', 'SCALE_DB_PORT=' + db['PORT'])]
        job_exe_pre_task_params = list(env_vars)
        job_exe_pre_task_params.extend([DockerParam('volume', input_data_volume_rw),
                                        DockerParam('volume', output_data_volume_rw),
                                        DockerParam('volume', workspace_volume_1_create)])
        job_exe_job_task_params = [DockerParam('volume', input_data_volume_ro),
                                   DockerParam('volume', output_data_volume_rw),
                                   DockerParam('volume', workspace_volume_1_ro)]
        job_exe_post_task_params = list(env_vars)
        job_exe_post_task_params.extend([DockerParam('volume', output_data_volume_ro),
                                         DockerParam('volume', workspace_volume_1_rw),
                                         DockerParam('volume', workspace_volume_2_create)])
        node = node_test_utils.create_node()
        resources = JobResources(cpus=10, mem=11, disk_in=12, disk_out=13, disk_total=25)
        workspaces = {workspace_1.name: workspace_1, workspace_2.name: workspace_2}

        job_exes = JobExecution.objects.schedule_job_executions('123', [(job_exe, node, resources)], workspaces)

        params = job_exes[0].get_job_configuration().get_pre_task_docker_params()
        self.assertEqual(len(params), len(job_exe_pre_task_params))
        for i in range(len(params)):
            param = params[i]
            expected_param = job_exe_pre_task_params[i]
            self.assertEqual(param.flag, expected_param.flag)
            self.assertEqual(param.value, expected_param.value)
        params = job_exes[0].get_job_configuration().get_job_task_docker_params()
        self.assertEqual(len(params), len(job_exe_job_task_params))
        for i in range(len(params)):
            param = params[i]
            expected_param = job_exe_job_task_params[i]
            self.assertEqual(param.flag, expected_param.flag)
            self.assertEqual(param.value, expected_param.value)
        params = job_exes[0].get_job_configuration().get_post_task_docker_params()
        self.assertEqual(len(params), len(job_exe_post_task_params))
        for i in range(len(params)):
            param = params[i]
            expected_param = job_exe_post_task_params[i]
            self.assertEqual(param.flag, expected_param.flag)
            self.assertEqual(param.value, expected_param.value)

    def test_schedule_job_executions_ingest_docker_params(self):
        """Testing scheduling a job execution and checking Docker params for an ingest job"""
        workspace = storage_test_utils.create_workspace(json_config={'broker': {'type': 'nfs',
                                                                                'nfs_path': 'scale:/scale'}})
        job_type = JobType.objects.get_by_natural_key('scale-ingest', '1.0')
        job = job_test_utils.create_job(job_type=job_type, status='QUEUED')

        configuration = JobConfiguration()
        configuration.add_job_task_workspace(workspace.name, MODE_RW)
        job_exe = job_test_utils.create_job_exe(status='QUEUED', job=job, configuration=configuration.get_dict())

        volume_name = container.get_workspace_volume_name('123', job_exe.id, workspace.name)
        workspace_volume_create = '$(docker volume create --driver=nfs --name=%s scale/scale):%s:rw'
        workspace_volume_create = workspace_volume_create % (volume_name, get_workspace_volume_path(workspace.name))

        db = settings.DATABASES['default']
        job_exe_job_task_params = [DockerParam('env', 'SCALE_DB_NAME=' + db['NAME']),
                                   DockerParam('env', 'SCALE_DB_USER=' + db['USER']),
                                   DockerParam('env', 'SCALE_DB_PASS=' + db['PASSWORD']),
                                   DockerParam('env', 'SCALE_DB_HOST=' + db['HOST']),
                                   DockerParam('env', 'SCALE_DB_PORT=' + db['PORT']),
                                   DockerParam('volume', workspace_volume_create)]

        node = node_test_utils.create_node()
        resources = JobResources(cpus=10, mem=11, disk_in=12, disk_out=13, disk_total=25)
        workspaces = {workspace.name: workspace}

        job_exes = JobExecution.objects.schedule_job_executions('123', [(job_exe, node, resources)], workspaces)

        self.assertEqual(len(job_exes[0].get_job_configuration().get_pre_task_docker_params()), 0)
        params = job_exes[0].get_job_configuration().get_job_task_docker_params()
        self.assertEqual(len(params), len(job_exe_job_task_params))
        for i in range(len(params)):
            param = params[i]
            expected_param = job_exe_job_task_params[i]
            self.assertEqual(param.flag, expected_param.flag)
            self.assertEqual(param.value, expected_param.value)
        self.assertEqual(len(job_exes[0].get_job_configuration().get_post_task_docker_params()), 0)


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
        """Tests calling JobTypeManager.create_job_type() successfully with no trigger rule or error mapping"""

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
        """Tests calling JobTypeManager.create_job_type() successfully with a trigger rule and error mapping"""

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
        """Tests calling JobTypeManager.create_job_type() with an invalid trigger rule"""

        name = 'my-job-type'
        version = '1.0'
        trigger_rule = trigger_test_utils.create_trigger_rule(trigger_type=job_test_utils.MOCK_ERROR_TYPE,
                                                              configuration=self.trigger_config.get_dict())

        # Call test
        self.assertRaises(InvalidConnection, JobType.objects.create_job_type, name, version, self.job_interface,
                          trigger_rule, self.error_mapping)

    def test_successful_other_fields(self):
        """Tests calling JobTypeManager.create_job_type() successfully with additional fields"""

        name = 'my-job-type'
        version = '1.0'
        title = 'my title'
        description = 'my-description'
        priority = 13
        docker_params = [["a","1"],["b","2"]]

        # Call test
        job_type = JobType.objects.create_job_type(name, version, self.job_interface, title=title,
                                                   description=description, priority=priority,
                                                   docker_params=docker_params)

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
        self.assertEqual(job_type.docker_params, docker_params)

    def test_successful_paused(self):
        """Tests calling JobTypeManager.create_job_type() and pausing it"""

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
        """Tests calling JobTypeManager.create_job_type() with an uneditable field"""

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
        """Tests calling JobTypeManager.create_job_type() with an invalid error mapping"""

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
        """Tests calling JobTypeManager.edit_job_type() with a change to some general fields"""

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
        """Tests calling JobTypeManager.edit_job_type() with a change to the interface"""

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
        """Tests calling JobTypeManager.edit_job_type() with a change to the trigger rule"""

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
        """Tests calling JobTypeManager.edit_job_type() that removes the trigger rule"""

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
        """Tests calling JobTypeManager.edit_job_type() with a change to both the definition and the trigger rule
        """

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
        """Tests calling JobTypeManager.edit_job_type() with a new invalid trigger rule"""

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
        """Tests calling JobTypeManager.edit_job_type() for a system job type"""

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
        """Tests calling JobTypeManager.edit_job_type() to change an uneditable field"""

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
        """Tests calling JobTypeManager.edit_job_type() with an invalid error mapping"""

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
        """Tests calling JobTypeManager.validate_job_type() successfully"""

        warnings = JobType.objects.validate_job_type('name', '1.0', self.interface, self.error_mapping,
                                                     self.trigger_config)

        # Check results
        self.assertListEqual(warnings, [])

    def test_invalid(self):
        """Tests calling JobTypeManager.validate_job_type() with an invalid trigger rule"""

        self.assertRaises(InvalidConnection, JobType.objects.validate_job_type, 'name', '1.0', self.interface,
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
