from __future__ import unicode_literals

import os

import django
from django.test import TestCase

from job.configuration.configurators import QueuedExecutionConfigurator, ScheduledExecutionConfigurator
from job.configuration.data.job_data import JobData
from job.configuration.json.execution.exe_config import ExecutionConfiguration
from job.execution.container import SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH
from job.test import utils as job_test_utils
from storage.test import utils as storage_test_utils
from trigger.test import utils as trigger_test_utils


class TestQueuedExecutionConfigurator(TestCase):

    def setUp(self):
        django.setup()

    def test_configure_queued_job_regular(self):
        """Tests successfully calling configure_queued_job() on a regular (non-system) job"""

        workspace = storage_test_utils.create_workspace()
        file_1 = storage_test_utils.create_file()
        file_2 = storage_test_utils.create_file()
        file_3 = storage_test_utils.create_file()
        input_files = {file_1.id: file_1, file_2.id: file_2, file_3.id: file_3}
        interface_dict = {'version': '1.4', 'command': 'foo',
                          'command_arguments': '${-a :input_1} ${-b :input_2} ${input_3} ${job_output_dir}',
                          'input_data': [{'name': 'input_1', 'type': 'property'}, {'name': 'input_2', 'type': 'file'},
                                         {'name': 'input_3', 'type': 'files'}],
                          'output_data': [{'name': 'output_1', 'type': 'file'}]}
        data_dict = {'input_data': [{'name': 'input_1', 'value': 'my_val'}, {'name': 'input_2', 'file_id': file_1.id},
                                    {'name': 'input_3', 'file_ids': [file_2.id, file_3.id]}],
                     'output_data': [{'name': 'output_1', 'workspace_id': workspace.id}]}
        input_2_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_2', file_1.file_name)
        input_3_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_3')
        expected_args = '-a my_val -b %s %s ${job_output_dir}' % (input_2_val, input_3_val)
        expected_env_vars = {'INPUT_1': 'my_val', 'INPUT_2': input_2_val, 'INPUT_3': input_3_val,
                             'job_output_dir': SCALE_JOB_EXE_OUTPUT_PATH, 'OUTPUT_DIR': SCALE_JOB_EXE_OUTPUT_PATH}
        expected_output_workspaces = {'output_1': workspace.name}
        job_type = job_test_utils.create_job_type(interface=interface_dict)
        job = job_test_utils.create_job(job_type=job_type, data=data_dict, status='QUEUED')
        configurator = QueuedExecutionConfigurator(input_files)

        # Test method
        exe_config = configurator.configure_queued_job(job)

        config_dict = exe_config.get_dict()
        # Make sure the dict validates
        ExecutionConfiguration(config_dict)
        self.assertSetEqual(set(config_dict['input_files'].keys()), {'input_2', 'input_3'})
        self.assertEqual(len(config_dict['input_files']['input_2']), 1)
        self.assertEqual(len(config_dict['input_files']['input_3']), 2)
        self.assertDictEqual(config_dict['output_workspaces'], expected_output_workspaces)
        self.assertEqual(len(config_dict['tasks']), 1)
        main_task = config_dict['tasks'][0]
        self.assertEqual(main_task['type'], 'main')
        self.assertEqual(main_task['args'], expected_args)
        self.assertDictEqual(main_task['env_vars'], expected_env_vars)

    def test_configure_queued_job_old_ingest(self):
        """Tests successfully calling configure_queued_job() on an old (before revision 3) ingest job"""

        workspace_1 = storage_test_utils.create_workspace()
        workspace_2 = storage_test_utils.create_workspace()
        from ingest.test import utils as ingest_test_utils
        ingest = ingest_test_utils.create_ingest(workspace=workspace_1, new_workspace=workspace_2)
        data = JobData()
        data.add_property_input('Ingest ID', str(ingest.id))
        ingest.job.data = data.get_dict()
        ingest.job.status = 'QUEUED'
        ingest.job.save()

        expected_args = 'scale_ingest -i %s' % str(ingest.id)
        expected_env_vars = {'INGEST ID': str(ingest.id)}
        expected_workspaces = {workspace_1.name: {'mode': 'rw'}, workspace_2.name: {'mode': 'rw'}}
        expected_config = {'version': '2.0', 'tasks': [{'type': 'main', 'args': expected_args,
                                                        'env_vars': expected_env_vars,
                                                        'workspaces': expected_workspaces}]}
        configurator = QueuedExecutionConfigurator({})

        # Test method
        exe_config = configurator.configure_queued_job(ingest.job)

        config_dict = exe_config.get_dict()
        self.assertDictEqual(config_dict, expected_config)

    def test_configure_queued_job_ingest_with_new_workspace(self):
        """Tests successfully calling configure_queued_job() on an ingest job with a new workspace"""

        workspace_1 = storage_test_utils.create_workspace()
        workspace_2 = storage_test_utils.create_workspace()
        from ingest.models import Ingest
        from ingest.test import utils as ingest_test_utils
        ingest = ingest_test_utils.create_ingest(workspace=workspace_1, new_workspace=workspace_2)
        Ingest.objects.start_ingest_tasks([ingest])

        expected_args = 'scale_ingest -i %s' % str(ingest.id)
        expected_env_vars = {'INGEST_ID': str(ingest.id)}
        expected_workspaces = {workspace_1.name: {'mode': 'rw'}, workspace_2.name: {'mode': 'rw'}}
        expected_config = {'version': '2.0', 'tasks': [{'type': 'main', 'args': expected_args,
                                                        'env_vars': expected_env_vars,
                                                        'workspaces': expected_workspaces}]}
        configurator = QueuedExecutionConfigurator({})

        # Test method
        exe_config = configurator.configure_queued_job(ingest.job)

        config_dict = exe_config.get_dict()
        # Make sure the dict validates
        ExecutionConfiguration(config_dict)
        self.assertDictEqual(config_dict, expected_config)

    def test_configure_queued_job_ingest_without_new_workspace(self):
        """Tests successfully calling configure_queued_job() on an ingest job without a new workspace"""

        workspace_1 = storage_test_utils.create_workspace()
        from ingest.models import Ingest
        from ingest.test import utils as ingest_test_utils
        ingest = ingest_test_utils.create_ingest(workspace=workspace_1)
        Ingest.objects.start_ingest_tasks([ingest])

        expected_args = 'scale_ingest -i %s' % str(ingest.id)
        expected_env_vars = {'INGEST_ID': str(ingest.id)}
        expected_workspaces = {workspace_1.name: {'mode': 'rw'}}
        expected_config = {'version': '2.0', 'tasks': [{'type': 'main', 'args': expected_args,
                                                        'env_vars': expected_env_vars,
                                                        'workspaces': expected_workspaces}]}
        configurator = QueuedExecutionConfigurator({})

        # Test method
        exe_config = configurator.configure_queued_job(ingest.job)

        config_dict = exe_config.get_dict()
        # Make sure the dict validates
        ExecutionConfiguration(config_dict)
        self.assertDictEqual(config_dict, expected_config)

    def test_configure_queued_job_strike(self):
        """Tests successfully calling configure_queued_job() on a Strike job"""

        workspace = storage_test_utils.create_workspace()
        configuration = {'version': '1.0', 'mount': 'host:/my/path', 'transfer_suffix': '_tmp',
                         'files_to_ingest': [{'filename_regex': '.*txt', 'workspace_name': workspace.name,
                                              'workspace_path': 'wksp/path'}]}
        from ingest.test import utils as ingest_test_utils
        strike = ingest_test_utils.create_strike(configuration=configuration)
        data = JobData()
        data.add_property_input('Strike ID', str(strike.id))
        strike.job.data = data.get_dict()
        strike.job.status = 'QUEUED'
        strike.job.save()

        expected_args = 'scale_strike -i %s' % str(strike.id)
        expected_env_vars = {'STRIKE ID': str(strike.id)}
        expected_workspaces = {workspace.name: {'mode': 'rw'}}
        expected_config = {'version': '2.0', 'tasks': [{'type': 'main', 'args': expected_args,
                                                        'env_vars': expected_env_vars,
                                                        'workspaces': expected_workspaces}]}
        configurator = QueuedExecutionConfigurator({})

        # Test method
        exe_config = configurator.configure_queued_job(strike.job)

        config_dict = exe_config.get_dict()
        # Make sure the dict validates
        ExecutionConfiguration(config_dict)
        self.assertDictEqual(config_dict, expected_config)

    def test_configure_queued_job_scan(self):
        """Tests successfully calling configure_queued_job() on a Scan job"""

        workspace = storage_test_utils.create_workspace()
        configuration = {'version': '1.0', 'workspace': workspace.name, 'scanner': {'type': 'dir'}, 'recursive': True,
                         'files_to_ingest': [{'filename_regex': '.*'}]}
        from ingest.models import Scan
        from ingest.test import utils as ingest_test_utils
        scan = ingest_test_utils.create_scan(configuration=configuration)
        Scan.objects.queue_scan(scan.id, False)

        expected_args = 'scale_scan -i %s' % str(scan.id)
        expected_env_vars = {'SCAN ID': str(scan.id), 'DRY RUN': 'False'}
        expected_workspaces = {workspace.name: {'mode': 'rw'}}
        expected_config = {'version': '2.0', 'tasks': [{'type': 'main', 'args': expected_args,
                                                        'env_vars': expected_env_vars,
                                                        'workspaces': expected_workspaces}]}
        configurator = QueuedExecutionConfigurator({})

        # Test method
        exe_config = configurator.configure_queued_job(scan.job)

        config_dict = exe_config.get_dict()
        # Make sure the dict validates
        ExecutionConfiguration(config_dict)
        self.assertDictEqual(config_dict, expected_config)


class TestScheduledExecutionConfigurator(TestCase):

    def setUp(self):
        django.setup()

    def test_configure_scheduled_job_regular(self):
        """Tests successfully calling configure_scheduled_job() on a regular (non-system) job"""

        workspace = storage_test_utils.create_workspace()
        workspaces = {workspace.name: workspace}
        file_1 = storage_test_utils.create_file()
        file_2 = storage_test_utils.create_file()
        file_3 = storage_test_utils.create_file()
        interface_dict = {'version': '1.4', 'command': 'foo',
                          'command_arguments': '${-a :input_1} ${-b :input_2} ${input_3} ${s_1} ${job_output_dir}',
                          'env_vars': [{'name': 'my_special_env', 'value': '${s_2}'}],
                          'mounts': [{'name': 'm_1', 'path': '/the/cont/path', 'mode': 'ro'},
                                     {'name': 'm_2', 'path': '/the/missing/cont/path', 'mode': 'rw'},
                                     {'name': 'm_3', 'path': '/the/optional/cont/path', 'mode': 'rw'}],
                          'settings': [{'name': 's_1'}, {'name': 's_2', 'secret': True}, {'name': 's_3'},
                                       {'name': 's_4', 'required': False}],
                          'input_data': [{'name': 'input_1', 'type': 'property'}, {'name': 'input_2', 'type': 'file'},
                                         {'name': 'input_3', 'type': 'files'}],
                          'output_data': [{'name': 'output_1', 'type': 'file'}]}
        data_dict = {'input_data': [{'name': 'input_1', 'value': 'my_val'}, {'name': 'input_2', 'file_id': file_1.id},
                                    {'name': 'input_3', 'file_ids': [file_2.id, file_3.id]}],
                     'output_data': [{'name': 'output_1', 'workspace_id': workspace.id}]}
        job_type = job_test_utils.create_job_type(interface=interface_dict)
        from queue.job_exe import QueuedJobExecution
        from queue.models import Queue
        job = Queue.objects.queue_new_job(job_type, JobData(data_dict), trigger_test_utils.create_trigger_event())
        # Get job info off of the queue
        queue = Queue.objects.get(job_id=job.id)
        queued_job_exe = QueuedJobExecution(queue)
        configurator = ScheduledExecutionConfigurator(workspaces)

        # Test method
        exe_config = configurator.configure_scheduled_job()

        # Expected results
        input_2_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_2', file_1.file_name)
        input_3_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_3')
        expected_args = '-a my_val -b %s %s ${job_output_dir}' % (input_2_val, input_3_val)
        expected_env_vars = {'INPUT_1': 'my_val', 'INPUT_2': input_2_val, 'INPUT_3': input_3_val,
                             'job_output_dir': SCALE_JOB_EXE_OUTPUT_PATH, 'OUTPUT_DIR': SCALE_JOB_EXE_OUTPUT_PATH}
        expected_output_workspaces = {'output_1': workspace.name}
