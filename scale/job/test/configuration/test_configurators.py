from __future__ import unicode_literals

import os

import django
from django.test import TestCase
from django.utils.timezone import now
from mock import patch, MagicMock

from job.configuration.configurators import QueuedExecutionConfigurator, ScheduledExecutionConfigurator
from job.configuration.data.job_data import JobData
from job.configuration.json.execution.exe_config import ExecutionConfiguration
from job.execution.container import get_job_exe_input_vol_name, get_job_exe_output_vol_name, get_mount_volume_name, \
    get_workspace_volume_name, SCALE_JOB_EXE_INPUT_PATH, SCALE_JOB_EXE_OUTPUT_PATH
from job.execution.tasks.post_task import POST_TASK_COMMAND_ARGS
from job.execution.tasks.pre_task import PRE_TASK_COMMAND_ARGS
from job.models import JobTypeRevision
from job.tasks.pull_task import create_pull_command
from job.test import utils as job_test_utils
from node.resources.node_resources import NodeResources
from node.resources.resource import Disk
from node.test import utils as node_test_utils
from storage.container import get_workspace_volume_path
from storage.test import utils as storage_test_utils
from trigger.test import utils as trigger_test_utils


class TestQueuedExecutionConfigurator(TestCase):

    fixtures = ['ingest_job_types.json']

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
                          'command_arguments': '${-a :input_1} ${-b :input_2} ${input_3} ${input_4} ${job_output_dir}',
                          'input_data': [{'name': 'input_1', 'type': 'property'}, {'name': 'input_2', 'type': 'file'},
                                         {'name': 'input_3', 'type': 'files'}, {'name': 'input_4', 'type': 'files',
                                         'required': False}],
                          'output_data': [{'name': 'output_1', 'type': 'file'}]}
        data_dict = {'input_data': [{'name': 'input_1', 'value': 'my_val'}, {'name': 'input_2', 'file_id': file_1.id},
                                    {'name': 'input_3', 'file_ids': [file_2.id, file_3.id]}],
                     'output_data': [{'name': 'output_1', 'workspace_id': workspace.id}]}
        input_2_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_2', file_1.file_name)
        input_3_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_3')
        expected_args = '-a my_val -b %s %s ${job_output_dir}' % (input_2_val, input_3_val)
        expected_env_vars = {'INPUT_1': 'my_val', 'INPUT_2': input_2_val, 'INPUT_3': input_3_val}
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
        from ingest.models import Ingest
        ingest = ingest_test_utils.create_ingest(workspace=workspace_1, new_workspace=workspace_2)
        ingest_job_type = Ingest.objects.get_ingest_job_type()
        ingest_rev_2 = JobTypeRevision.objects.get(job_type=ingest_job_type, revision_num=2)
        data = JobData()
        data.add_property_input('Ingest ID', str(ingest.id))
        ingest.job.job_type_rev = ingest_rev_2  # Job has old revision (2nd) of ingest job type
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
        # Make sure the dict validates
        ExecutionConfiguration(config_dict)
        self.assertDictEqual(config_dict, expected_config)

    def test_configure_queued_job_ingest_with_new_workspace(self):
        """Tests successfully calling configure_queued_job() on an ingest job with a new workspace"""

        workspace_1 = storage_test_utils.create_workspace()
        workspace_2 = storage_test_utils.create_workspace()
        from ingest.models import Ingest
        from ingest.test import utils as ingest_test_utils
        scan = ingest_test_utils.create_scan()
        ingest = ingest_test_utils.create_ingest(scan=scan, workspace=workspace_1, new_workspace=workspace_2)
        Ingest.objects.start_ingest_tasks([ingest], scan_id=scan.id)

        expected_args = 'scale_ingest -i %s' % str(ingest.id)
        expected_env_vars = {'INGEST_ID': str(ingest.id), 'WORKSPACE': workspace_1.name,
                             'NEW_WORKSPACE': workspace_2.name}
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
        scan = ingest_test_utils.create_scan()
        ingest = ingest_test_utils.create_ingest(scan=scan, workspace=workspace_1)
        Ingest.objects.start_ingest_tasks([ingest], scan_id=scan.id)

        expected_args = 'scale_ingest -i %s' % str(ingest.id)
        expected_env_vars = {'INGEST_ID': str(ingest.id), 'WORKSPACE': workspace_1.name}
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

        wksp_config_1 = {'version': '1.0', 'broker': {'type': 'host', 'host_path': '/my/path'}}
        workspace_1 = storage_test_utils.create_workspace(json_config=wksp_config_1)
        wksp_config_2 = {'version': '1.0', 'broker': {'type': 'host', 'host_path': '/other/my/path'}}
        workspace_2 = storage_test_utils.create_workspace(json_config=wksp_config_2)
        configuration = {'version': '2.0', 'workspace': workspace_1.name,
                         'monitor': {'type': 'dir-watcher', 'transfer_suffix': '_tmp'},
                         'files_to_ingest': [{'filename_regex': '.*txt', 'new_workspace': workspace_2.name}]}
        from ingest.test import utils as ingest_test_utils
        strike = ingest_test_utils.create_strike(configuration=configuration)
        data = JobData()
        data.add_property_input('Strike ID', str(strike.id))
        strike.job.data = data.get_dict()
        strike.job.status = 'QUEUED'
        strike.job.save()

        expected_args = 'scale_strike -i %s' % str(strike.id)
        expected_env_vars = {'STRIKE ID': str(strike.id)}
        expected_workspaces = {workspace_1.name: {'mode': 'rw'}}
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
        scan = Scan.objects.queue_scan(scan.id, False)

        expected_args = 'scale_scan -i %s -d False' % str(scan.id)
        expected_env_vars = {'SCAN ID': str(scan.id), 'DRY RUN': str(False)}
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

    fixtures = ['ingest_job_types.json']

    def setUp(self):
        django.setup()

    def test_configure_scheduled_job_ingest(self):
        """Tests successfully calling configure_scheduled_job() on an ingest job"""

        framework_id = '1234'
        node = node_test_utils.create_node()
        broker_dict = {'version': '1.0', 'broker': {'type': 'host', 'host_path': '/w_1/host/path'}}
        workspace = storage_test_utils.create_workspace(json_config=broker_dict)
        broker_dict = {'version': '1.0', 'broker': {'type': 's3', 'bucket_name': 'bucket1',
                                                    'host_path': '/w_2/host/path', 'region_name': 'us-east-1'}}
        new_workspace = storage_test_utils.create_workspace(json_config=broker_dict)
        workspaces = {workspace.name: workspace, new_workspace.name: new_workspace}
        from ingest.models import Ingest
        from ingest.test import utils as ingest_test_utils
        scan = ingest_test_utils.create_scan()
        ingest_job_type = Ingest.objects.get_ingest_job_type()
        ingest = ingest_test_utils.create_ingest(scan=scan, workspace=workspace, new_workspace=new_workspace)
        Ingest.objects.start_ingest_tasks([ingest], scan_id=scan.id)

        job = ingest.job
        resources = job.get_resources()
        # Get job info off of the queue
        from queue.job_exe import QueuedJobExecution
        from queue.models import Queue
        queue = Queue.objects.get(job_id=job.id)
        queued_job_exe = QueuedJobExecution(queue)
        queued_job_exe.scheduled('agent_1', node.id, resources)
        job_exe_model = queued_job_exe.create_job_exe_model(framework_id, now())

        # Test method
        with patch('job.configuration.configurators.settings') as mock_settings:
            mock_settings.LOGGING_ADDRESS = None  # Ignore logging settings
            mock_settings.DATABASES = {'default': {'NAME': 'TEST_NAME', 'USER': 'TEST_USER',
                                                   'PASSWORD': 'TEST_PASSWORD', 'HOST': 'TEST_HOST',
                                                   'PORT': 'TEST_PORT'}}
            configurator = ScheduledExecutionConfigurator(workspaces)
            exe_config_with_secrets = configurator.configure_scheduled_job(job_exe_model, ingest_job_type,
                                                                           queue.get_job_interface(), 'INFO')

        # Expected results
        wksp_vol_name = get_workspace_volume_name(job_exe_model, workspace.name)
        wksp_vol_path = get_workspace_volume_path(workspace.name)
        new_wksp_vol_name = get_workspace_volume_name(job_exe_model, new_workspace.name)
        new_wksp_vol_path = get_workspace_volume_path(new_workspace.name)

        expected_main_task = {'task_id': '%s_main' % job_exe_model.get_cluster_id(), 'type': 'main',
                              'resources': {'cpus': resources.cpus, 'mem': resources.mem, 'disk': resources.disk},
                              'args': 'scale_ingest -i %s' % unicode(ingest.id),
                              'env_vars': {'ALLOCATED_CPUS': unicode(resources.cpus),
                                           'ALLOCATED_MEM': unicode(resources.mem),
                                           'ALLOCATED_DISK': unicode(resources.disk), 'SCALE_DB_NAME': 'TEST_NAME',
                                           'SCALE_DB_USER': 'TEST_USER', 'SCALE_DB_PASS': 'TEST_PASSWORD',
                                           'SCALE_DB_HOST': 'TEST_HOST', 'SCALE_DB_PORT': 'TEST_PORT',
                                           'INGEST_ID': unicode(ingest.id), 'WORKSPACE': workspace.name,
                                           'NEW_WORKSPACE': new_workspace.name, 'SYSTEM_LOGGING_LEVEL': 'INFO'},
                              'workspaces': {workspace.name: {'mode': 'rw', 'volume_name': wksp_vol_name},
                                             new_workspace.name: {'mode': 'rw', 'volume_name': new_wksp_vol_name}},
                              'settings': {'SCALE_DB_NAME': 'TEST_NAME', 'SCALE_DB_USER': 'TEST_USER',
                                           'SCALE_DB_PASS': 'TEST_PASSWORD', 'SCALE_DB_HOST': 'TEST_HOST',
                                           'SCALE_DB_PORT': 'TEST_PORT'},
                              'volumes': {wksp_vol_name: {'container_path': wksp_vol_path, 'mode': 'rw', 'type': 'host',
                                                          'host_path': '/w_1/host/path'},
                                          new_wksp_vol_name: {'container_path': new_wksp_vol_path, 'mode': 'rw',
                                                              'type': 'host', 'host_path': '/w_2/host/path'}},
                              'docker_params': [{'flag': 'env', 'value': 'SCALE_DB_USER=TEST_USER'},
                                                {'flag': 'env', 'value': 'SCALE_DB_NAME=TEST_NAME'},
                                                {'flag': 'env', 'value': 'ALLOCATED_MEM=%.1f' % resources.mem},
                                                {'flag': 'env', 'value': 'ALLOCATED_CPUS=%.1f' % resources.cpus},
                                                {'flag': 'env', 'value': 'SCALE_DB_HOST=TEST_HOST'},
                                                {'flag': 'env', 'value': 'ALLOCATED_DISK=%.1f' % resources.disk},
                                                {'flag': 'env', 'value': 'SCALE_DB_PASS=TEST_PASSWORD'},
                                                {'flag': 'env', 'value': 'SCALE_DB_PORT=TEST_PORT'},
                                                {'flag': 'env', 'value': 'INGEST_ID=%s' % unicode(ingest.id)},
                                                {'flag': 'env', 'value': 'WORKSPACE=%s' % workspace.name},
                                                {'flag': 'env', 'value': 'NEW_WORKSPACE=%s' % new_workspace.name},
                                                {'flag': 'env', 'value': 'SYSTEM_LOGGING_LEVEL=INFO'},
                                                {'flag': 'volume',
                                                 'value': '/w_1/host/path:%s:rw' % wksp_vol_path},
                                                {'flag': 'volume',
                                                 'value': '/w_2/host/path:%s:rw' % new_wksp_vol_path},
                                               ]}
        expected_config = {'version': '2.0', 'tasks': [expected_main_task]}

        # Ensure configuration is valid
        ExecutionConfiguration(exe_config_with_secrets.get_dict())
        # Compare results including secrets, but convert Docker param lists to sets so order is ignored
        config_with_secrets_dict = exe_config_with_secrets.get_dict()
        for task_dict in config_with_secrets_dict['tasks']:
            docker_params_set = set()
            for docker_param in task_dict['docker_params']:
                docker_params_set.add('%s=%s' % (docker_param['flag'], docker_param['value']))
            task_dict['docker_params'] = docker_params_set
        for task_dict in expected_config['tasks']:
            docker_params_set = set()
            for docker_param in task_dict['docker_params']:
                docker_params_set.add('%s=%s' % (docker_param['flag'], docker_param['value']))
            task_dict['docker_params'] = docker_params_set
        self.assertDictEqual(config_with_secrets_dict, expected_config)

    def test_configure_scheduled_job_logging(self):
        """Tests successfully calling configure_scheduled_job() and checks Docker logging parameters"""

        framework_id = '1234'
        node = node_test_utils.create_node()
        interface_dict = {'version': '1.4', 'command': 'foo', 'command_arguments': '', 'env_vars': [], 'settings': [],
                          'input_data': [], 'output_data': []}
        data_dict = {'input_data': [], 'output_data': []}
        job_type = job_test_utils.create_job_type(interface=interface_dict)
        from queue.job_exe import QueuedJobExecution
        from queue.models import Queue
        job = Queue.objects.queue_new_job(job_type, JobData(data_dict), trigger_test_utils.create_trigger_event())
        resources = job.get_resources()
        # Get job info off of the queue
        queue = Queue.objects.get(job_id=job.id)
        queued_job_exe = QueuedJobExecution(queue)
        queued_job_exe.scheduled('agent_1', node.id, resources)
        job_exe_model = queued_job_exe.create_job_exe_model(framework_id, now())

        # Test method
        with patch('job.configuration.configurators.settings') as mock_settings:
            with patch('job.configuration.configurators.secrets_mgr') as mock_secrets_mgr:
                mock_settings.LOGGING_ADDRESS = 'test-logging-address'
                mock_settings.DATABASES = {'default': {'NAME': 'TEST_NAME', 'USER': 'TEST_USER',
                                                       'PASSWORD': 'TEST_PASSWORD', 'HOST': 'TEST_HOST',
                                                       'PORT': 'TEST_PORT'}}
                mock_secrets_mgr.retrieve_job_type_secrets = MagicMock()
                mock_secrets_mgr.retrieve_job_type_secrets.return_value = {}
                configurator = ScheduledExecutionConfigurator({})
                exe_config_with_secrets = configurator.configure_scheduled_job(job_exe_model, job_type,
                                                                               queue.get_job_interface(), 'INFO')

        # Ensure configuration is valid
        ExecutionConfiguration(exe_config_with_secrets.get_dict())

        # Check config for logging parameters
        for task_type in exe_config_with_secrets.get_task_types():
            if task_type == 'pull':
                continue  # Ignore pull tasks which are not Docker tasks
            found_log_driver = False
            found_syslog_format = False
            found_syslog_address = False
            found_tag = False
            for docker_param in exe_config_with_secrets.get_docker_params(task_type):
                if docker_param.flag == 'log-driver':
                    self.assertEqual(docker_param.value, 'syslog')
                    found_log_driver = True
                elif docker_param.flag == 'log-opt':
                    array = docker_param.value.split('=')
                    opt_name = array[0]
                    opt_value = array[1]
                    if opt_name == 'syslog-format':
                        self.assertEqual(opt_value, 'rfc3164')
                        found_syslog_format = True
                    elif opt_name == 'syslog-address':
                        self.assertEqual(opt_value, 'test-logging-address')
                        found_syslog_address = True
                    elif opt_name == 'tag':
                        tag_value = '%s|%s' % (exe_config_with_secrets.get_task_id(task_type), job_type.name)
                        self.assertEqual(opt_value, tag_value)
                        found_tag = True
            self.assertTrue(found_log_driver)
            self.assertTrue(found_syslog_format)
            self.assertTrue(found_syslog_address)
            self.assertTrue(found_tag)

    def test_configure_scheduled_job_regular(self):
        """Tests successfully calling configure_scheduled_job() on a regular (non-system) job"""

        framework_id = '1234'
        node = node_test_utils.create_node()
        broker_dict = {'version': '1.0', 'broker': {'type': 'host', 'host_path': '/w_1/host/path'}}
        input_workspace = storage_test_utils.create_workspace(json_config=broker_dict)
        broker_dict = {'version': '1.0', 'broker': {'type': 's3', 'bucket_name': 'bucket1',
                                                    'host_path': '/w_2/host/path', 'region_name': 'us-east-1'}}
        output_workspace = storage_test_utils.create_workspace(json_config=broker_dict)
        workspaces = {input_workspace.name: input_workspace, output_workspace.name: output_workspace}
        file_1 = storage_test_utils.create_file(workspace=input_workspace)
        file_2 = storage_test_utils.create_file(workspace=input_workspace)
        file_3 = storage_test_utils.create_file(workspace=input_workspace)
        interface_dict = {'version': '1.4', 'command': 'foo',
                          'command_arguments': '${-a :input_1} ${-b :input_2} ${input_3} ${s_1} ${job_output_dir}',
                          'env_vars': [{'name': 'my_special_env', 'value': '${s_2}'}],
                          'mounts': [{'name': 'm_1', 'path': '/the/cont/path', 'mode': 'ro'},
                                     {'name': 'm_2', 'path': '/the/missing/cont/path', 'mode': 'rw'},
                                     {'name': 'm_3', 'path': '/the/optional/cont/path', 'mode': 'rw',
                                      'required': False}],
                          'settings': [{'name': 's_1'}, {'name': 's_2', 'secret': True}, {'name': 's_3'},
                                       {'name': 's_4', 'required': False}],
                          'input_data': [{'name': 'input_1', 'type': 'property'}, {'name': 'input_2', 'type': 'file'},
                                         {'name': 'input_3', 'type': 'files'}],
                          'output_data': [{'name': 'output_1', 'type': 'file'}]}
        data_dict = {'input_data': [{'name': 'input_1', 'value': 'my_val'}, {'name': 'input_2', 'file_id': file_1.id},
                                    {'name': 'input_3', 'file_ids': [file_2.id, file_3.id]}],
                     'output_data': [{'name': 'output_1', 'workspace_id': output_workspace.id}]}
        job_type_config_dict = {'version': '2.0', 'settings': {'s_1': 's_1_value'},
                                'mounts': {'m_1': {'type': 'host', 'host_path': '/m_1/host_path'}}}
        job_type = job_test_utils.create_job_type(interface=interface_dict, configuration=job_type_config_dict)
        from queue.job_exe import QueuedJobExecution
        from queue.models import Queue
        job = Queue.objects.queue_new_job(job_type, JobData(data_dict), trigger_test_utils.create_trigger_event())
        resources = job.get_resources()
        main_resources = resources.copy()
        main_resources.subtract(NodeResources([Disk(job.disk_in_required)]))
        post_resources = resources.copy()
        post_resources.remove_resource('disk')
        # Get job info off of the queue
        queue = Queue.objects.get(job_id=job.id)
        queued_job_exe = QueuedJobExecution(queue)
        queued_job_exe.scheduled('agent_1', node.id, resources)
        job_exe_model = queued_job_exe.create_job_exe_model(framework_id, now())

        # Test method
        with patch('job.configuration.configurators.settings') as mock_settings:
            with patch('job.configuration.configurators.secrets_mgr') as mock_secrets_mgr:
                mock_settings.LOGGING_ADDRESS = None  # Ignore logging settings, there's enough in this unit test
                mock_settings.DATABASES = {'default': {'NAME': 'TEST_NAME', 'USER': 'TEST_USER',
                                                       'PASSWORD': 'TEST_PASSWORD', 'HOST': 'TEST_HOST',
                                                       'PORT': 'TEST_PORT'}}
                mock_secrets_mgr.retrieve_job_type_secrets = MagicMock()
                mock_secrets_mgr.retrieve_job_type_secrets.return_value = {'s_2': 's_2_secret'}
                configurator = ScheduledExecutionConfigurator(workspaces)
                exe_config_with_secrets = configurator.configure_scheduled_job(job_exe_model, job_type,
                                                                            queue.get_job_interface(), 'INFO')

        # Expected results
        input_wksp_vol_name = get_workspace_volume_name(job_exe_model, input_workspace.name)
        input_wksp_vol_path = get_workspace_volume_path(input_workspace.name)
        output_wksp_vol_name = get_workspace_volume_name(job_exe_model, output_workspace.name)
        output_wksp_vol_path = get_workspace_volume_path(output_workspace.name)
        m_1_vol_name = get_mount_volume_name(job_exe_model, 'm_1')
        input_mnt_name = 'scale_input_mount'
        output_mnt_name = 'scale_output_mount'
        input_vol_name = get_job_exe_input_vol_name(job_exe_model)
        output_vol_name = get_job_exe_output_vol_name(job_exe_model)
        input_2_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_2', file_1.file_name)
        input_3_val = os.path.join(SCALE_JOB_EXE_INPUT_PATH, 'input_3')
        expected_input_files = queue.get_execution_configuration().get_dict()['input_files']
        expected_output_workspaces = {'output_1': output_workspace.name}
        expected_pull_task = {'task_id': '%s_pull' % job_exe_model.get_cluster_id(), 'type': 'pull',
                              'resources': {'cpus': resources.cpus, 'mem': resources.mem, 'disk': resources.disk},
                              'args': create_pull_command(job_type.docker_image),
                              'env_vars': {'ALLOCATED_CPUS': unicode(resources.cpus),
                                           'ALLOCATED_MEM': unicode(resources.mem),
                                           'ALLOCATED_DISK': unicode(resources.disk)},
                              'docker_params': [{'flag': 'env', 'value': 'ALLOCATED_MEM=%.1f' % resources.mem},
                                                {'flag': 'env', 'value': 'ALLOCATED_CPUS=%.1f' % resources.cpus},
                                                {'flag': 'env', 'value': 'ALLOCATED_DISK=%.1f' % resources.disk}]}
        expected_pre_task = {'task_id': '%s_pre' % job_exe_model.get_cluster_id(), 'type': 'pre',
                             'resources': {'cpus': resources.cpus, 'mem': resources.mem, 'disk': resources.disk},
                             'args': PRE_TASK_COMMAND_ARGS,
                             'env_vars': {'SCALE_JOB_ID': unicode(job.id), 'SCALE_EXE_NUM': unicode(job.num_exes),
                                          'ALLOCATED_CPUS': unicode(resources.cpus),
                                          'ALLOCATED_MEM': unicode(resources.mem),
                                          'ALLOCATED_DISK': unicode(resources.disk), 'SCALE_DB_NAME': 'TEST_NAME',
                                          'SCALE_DB_USER': 'TEST_USER', 'SCALE_DB_PASS': 'TEST_PASSWORD',
                                          'SCALE_DB_HOST': 'TEST_HOST', 'SCALE_DB_PORT': 'TEST_PORT'},
                             'workspaces': {input_workspace.name: {'mode': 'ro', 'volume_name': input_wksp_vol_name}},
                             'mounts': {input_mnt_name: input_vol_name, output_mnt_name: output_vol_name},
                             'settings': {'SCALE_DB_NAME': 'TEST_NAME', 'SCALE_DB_USER': 'TEST_USER',
                                          'SCALE_DB_PASS': 'TEST_PASSWORD', 'SCALE_DB_HOST': 'TEST_HOST',
                                          'SCALE_DB_PORT': 'TEST_PORT'},
                             'volumes': {input_wksp_vol_name: {'container_path': input_wksp_vol_path, 'mode': 'ro',
                                                               'type': 'host', 'host_path': '/w_1/host/path'},
                                         input_vol_name: {'container_path': SCALE_JOB_EXE_INPUT_PATH, 'mode': 'rw',
                                                          'type': 'volume'},
                                         output_vol_name: {'container_path': SCALE_JOB_EXE_OUTPUT_PATH, 'mode': 'rw',
                                                           'type': 'volume'}},
                             'docker_params': [{'flag': 'env', 'value': 'SCALE_DB_USER=TEST_USER'},
                                               {'flag': 'env', 'value': 'SCALE_DB_NAME=TEST_NAME'},
                                               {'flag': 'env', 'value': 'SCALE_JOB_ID=%d' % job.id},
                                               {'flag': 'env', 'value': 'SCALE_EXE_NUM=%d' % job.num_exes},
                                               {'flag': 'env', 'value': 'ALLOCATED_MEM=%.1f' % resources.mem},
                                               {'flag': 'env', 'value': 'ALLOCATED_CPUS=%.1f' % resources.cpus},
                                               {'flag': 'env', 'value': 'SCALE_DB_HOST=TEST_HOST'},
                                               {'flag': 'env', 'value': 'ALLOCATED_DISK=%.1f' % resources.disk},
                                               {'flag': 'env', 'value': 'SCALE_DB_PASS=TEST_PASSWORD'},
                                               {'flag': 'env', 'value': 'SCALE_DB_PORT=TEST_PORT'},
                                               {'flag': 'volume', 'value': '%s:%s:rw' %
                                                                           (output_vol_name, SCALE_JOB_EXE_OUTPUT_PATH)},
                                               {'flag': 'volume',
                                                'value': '/w_1/host/path:%s:ro' % input_wksp_vol_path},
                                               {'flag': 'volume', 'value': '%s:%s:rw' %
                                                                           (input_vol_name, SCALE_JOB_EXE_INPUT_PATH)}

                                               ]}
        expected_pst_task = {'task_id': '%s_post' % job_exe_model.get_cluster_id(), 'type': 'post',
                             'resources': {'cpus': post_resources.cpus, 'mem': post_resources.mem,
                                           'disk': post_resources.disk},
                             'args': POST_TASK_COMMAND_ARGS,
                             'env_vars': {'SCALE_JOB_ID': unicode(job.id), 'SCALE_EXE_NUM': unicode(job.num_exes),
                                          'ALLOCATED_CPUS': unicode(post_resources.cpus),
                                          'ALLOCATED_MEM': unicode(post_resources.mem),
                                          'ALLOCATED_DISK': unicode(post_resources.disk), 'SCALE_DB_NAME': 'TEST_NAME',
                                          'SCALE_DB_USER': 'TEST_USER', 'SCALE_DB_PASS': 'TEST_PASSWORD',
                                          'SCALE_DB_HOST': 'TEST_HOST', 'SCALE_DB_PORT': 'TEST_PORT'},
                             'workspaces': {input_workspace.name: {'mode': 'rw', 'volume_name': input_wksp_vol_name},
                                            output_workspace.name: {'mode': 'rw', 'volume_name': output_wksp_vol_name}},
                             'mounts': {output_mnt_name: output_vol_name},
                             'settings': {'SCALE_DB_NAME': 'TEST_NAME', 'SCALE_DB_USER': 'TEST_USER',
                                          'SCALE_DB_PASS': 'TEST_PASSWORD', 'SCALE_DB_HOST': 'TEST_HOST',
                                          'SCALE_DB_PORT': 'TEST_PORT'},
                             'volumes': {input_wksp_vol_name: {'container_path': input_wksp_vol_path, 'mode': 'rw',
                                                               'type': 'host', 'host_path': '/w_1/host/path'},
                                         output_wksp_vol_name: {'container_path': output_wksp_vol_path, 'mode': 'rw',
                                                                'type': 'host', 'host_path': '/w_2/host/path'},
                                         output_vol_name: {'container_path': SCALE_JOB_EXE_OUTPUT_PATH, 'mode': 'ro',
                                                           'type': 'volume'}},
                             'docker_params': [{'flag': 'env', 'value': 'SCALE_DB_USER=TEST_USER'},
                                               {'flag': 'env', 'value': 'SCALE_DB_NAME=TEST_NAME'},
                                               {'flag': 'env', 'value': 'SCALE_JOB_ID=%d' % job.id},
                                               {'flag': 'env', 'value': 'SCALE_EXE_NUM=%d' % job.num_exes},
                                               {'flag': 'env', 'value': 'ALLOCATED_MEM=%.1f' % post_resources.mem},
                                               {'flag': 'env', 'value': 'ALLOCATED_CPUS=%.1f' % post_resources.cpus},
                                               {'flag': 'env', 'value': 'SCALE_DB_HOST=TEST_HOST'},
                                               {'flag': 'env', 'value': 'ALLOCATED_DISK=%.1f' % post_resources.disk},
                                               {'flag': 'env', 'value': 'SCALE_DB_PASS=TEST_PASSWORD'},
                                               {'flag': 'env', 'value': 'SCALE_DB_PORT=TEST_PORT'},
                                               {'flag': 'volume', 'value': '%s:%s:ro' %
                                                                           (output_vol_name, SCALE_JOB_EXE_OUTPUT_PATH)},
                                               {'flag': 'volume',
                                                'value': '/w_1/host/path:%s:rw' % input_wksp_vol_path},
                                               {'flag': 'volume',
                                                'value': '/w_2/host/path:%s:rw' % output_wksp_vol_path}
                                               ]}
        expected_main_task = {'task_id': '%s_main' % job_exe_model.get_cluster_id(), 'type': 'main',
                              'resources': {'cpus': main_resources.cpus, 'mem': main_resources.mem,
                                            'disk': main_resources.disk},
                              'args': '-a my_val -b %s %s s_1_value %s' %
                                      (input_2_val, input_3_val, SCALE_JOB_EXE_OUTPUT_PATH),
                              'env_vars': {'INPUT_1': 'my_val', 'INPUT_2': input_2_val, 'INPUT_3': input_3_val,
                                           'job_output_dir': SCALE_JOB_EXE_OUTPUT_PATH,
                                           'OUTPUT_DIR': SCALE_JOB_EXE_OUTPUT_PATH, 'S_1': 's_1_value',
                                           'S_2': 's_2_secret', 'my_special_env': 's_2_secret',
                                           'ALLOCATED_CPUS': unicode(main_resources.cpus),
                                           'ALLOCATED_MEM': unicode(main_resources.mem),
                                           'ALLOCATED_DISK': unicode(main_resources.disk)},
                              'workspaces': {input_workspace.name: {'mode': 'ro', 'volume_name': input_wksp_vol_name}},
                              'mounts': {'m_1': m_1_vol_name, 'm_2': None, 'm_3': None, input_mnt_name: input_vol_name,
                                         output_mnt_name: output_vol_name},  # m_2 and s_3 are required, but missing
                              'settings': {'s_1': 's_1_value', 's_2': 's_2_secret', 's_3': None},
                              'volumes': {input_wksp_vol_name: {'container_path': input_wksp_vol_path, 'mode': 'ro',
                                                                'type': 'host', 'host_path': '/w_1/host/path'},
                                          input_vol_name: {'container_path': SCALE_JOB_EXE_INPUT_PATH, 'mode': 'ro',
                                                           'type': 'volume'},
                                          output_vol_name: {'container_path': SCALE_JOB_EXE_OUTPUT_PATH, 'mode': 'rw',
                                                            'type': 'volume'},
                                          m_1_vol_name: {'container_path': '/the/cont/path', 'mode': 'ro',
                                                         'type': 'host', 'host_path': '/m_1/host_path'}},
                              'docker_params': [{'flag': 'env', 'value': 'S_1=s_1_value'},
                                                {'flag': 'env', 'value': 'S_2=s_2_secret'},
                                                {'flag': 'env', 'value': 'ALLOCATED_MEM=%.1f' % main_resources.mem},
                                                {'flag': 'env', 'value': 'ALLOCATED_CPUS=%.1f' % main_resources.cpus},
                                                {'flag': 'env', 'value': 'my_special_env=s_2_secret'},
                                                {'flag': 'env', 'value': 'ALLOCATED_DISK=%.1f' % main_resources.disk},
                                                {'flag': 'env', 'value': 'INPUT_2=%s' % input_2_val},
                                                {'flag': 'env', 'value': 'INPUT_3=%s' % input_3_val},
                                                {'flag': 'env', 'value': 'INPUT_1=my_val'},
                                                {'flag': 'env', 'value': 'job_output_dir=%s' % SCALE_JOB_EXE_OUTPUT_PATH},
                                                {'flag': 'env', 'value': 'OUTPUT_DIR=%s' % SCALE_JOB_EXE_OUTPUT_PATH},
                                                {'flag': 'volume', 'value': '%s:%s:rw' %
                                                                            (output_vol_name, SCALE_JOB_EXE_OUTPUT_PATH)},
                                                {'flag': 'volume',
                                                 'value': '/m_1/host_path:/the/cont/path:ro'},
                                                {'flag': 'volume',
                                                 'value': '/w_1/host/path:%s:ro' % input_wksp_vol_path},
                                                {'flag': 'volume', 'value': '%s:%s:ro' %
                                                                            (input_vol_name, SCALE_JOB_EXE_INPUT_PATH)}
                                               ]}
        expected_config = {'version': '2.0',
                           'input_files': expected_input_files,
                           'output_workspaces': expected_output_workspaces,
                           'tasks': [expected_pull_task, expected_pre_task, expected_main_task, expected_pst_task]}

        # Ensure configuration is valid
        ExecutionConfiguration(exe_config_with_secrets.get_dict())
        # Compare results including secrets, but convert Docker param lists to sets so order is ignored
        config_with_secrets_dict = exe_config_with_secrets.get_dict()
        for task_dict in config_with_secrets_dict['tasks']:
            docker_params_set = set()
            for docker_param in task_dict['docker_params']:
                docker_params_set.add('%s=%s' % (docker_param['flag'], docker_param['value']))
            task_dict['docker_params'] = docker_params_set
        for task_dict in expected_config['tasks']:
            docker_params_set = set()
            for docker_param in task_dict['docker_params']:
                docker_params_set.add('%s=%s' % (docker_param['flag'], docker_param['value']))
            task_dict['docker_params'] = docker_params_set
        self.assertDictEqual(config_with_secrets_dict, expected_config)

    def test_configure_scheduled_job_secrets(self):
        """Tests successfully calling configure_scheduled_job() and checks to make sure secrets are appropriately
        handled
        """

        framework_id = '1234'
        node = node_test_utils.create_node()
        interface_dict = {'version': '1.4', 'command': 'foo',
                          'command_arguments': '',
                          'env_vars': [{'name': 'my_special_env', 'value': '${s_2}'}],
                          'settings': [{'name': 's_1', 'secret': True}, {'name': 's_2', 'secret': True},
                                       {'name': 's_3'}],
                          'input_data': [], 'output_data': []}
        data_dict = {'input_data': [], 'output_data': []}
        job_type_config_dict = {'version': '2.0', 'settings': {'s_3': 's_3_value'}}
        job_type = job_test_utils.create_job_type(interface=interface_dict, configuration=job_type_config_dict)
        from queue.job_exe import QueuedJobExecution
        from queue.models import Queue
        job = Queue.objects.queue_new_job(job_type, JobData(data_dict), trigger_test_utils.create_trigger_event())
        resources = job.get_resources()
        # Get job info off of the queue
        queue = Queue.objects.get(job_id=job.id)
        queued_job_exe = QueuedJobExecution(queue)
        queued_job_exe.scheduled('agent_1', node.id, resources)
        job_exe_model = queued_job_exe.create_job_exe_model(framework_id, now())

        # Test method
        with patch('job.configuration.configurators.settings') as mock_settings:
            with patch('job.configuration.configurators.secrets_mgr') as mock_secrets_mgr:
                mock_settings.LOGGING_ADDRESS = None  # Ignore logging settings
                mock_settings.DATABASES = {'default': {'NAME': 'TEST_NAME', 'USER': 'TEST_USER',
                                                       'PASSWORD': 'TEST_PASSWORD', 'HOST': 'TEST_HOST',
                                                       'PORT': 'TEST_PORT'}}
                mock_secrets_mgr.retrieve_job_type_secrets = MagicMock()
                mock_secrets_mgr.retrieve_job_type_secrets.return_value = {'s_1': 's_1_secret', 's_2': 's_2_secret'}
                configurator = ScheduledExecutionConfigurator({})
                exe_config_with_secrets = configurator.configure_scheduled_job(job_exe_model, job_type,
                                                                               queue.get_job_interface(),'INFO')

        expected_pre_secret_settings = {'SCALE_DB_NAME': 'TEST_NAME', 'SCALE_DB_USER': 'TEST_USER',
                                        'SCALE_DB_PASS': 'TEST_PASSWORD', 'SCALE_DB_HOST': 'TEST_HOST',
                                        'SCALE_DB_PORT': 'TEST_PORT'}
        expected_pre_censored_settings = {'SCALE_DB_NAME': '*****', 'SCALE_DB_USER': '*****', 'SCALE_DB_PASS': '*****',
                                          'SCALE_DB_HOST': '*****', 'SCALE_DB_PORT': '*****'}
        expected_pre_secret_env_vars = {'SCALE_DB_NAME': 'TEST_NAME', 'SCALE_DB_USER': 'TEST_USER',
                                        'SCALE_DB_PASS': 'TEST_PASSWORD', 'SCALE_DB_HOST': 'TEST_HOST',
                                        'SCALE_DB_PORT': 'TEST_PORT'}
        expected_pre_censored_env_vars = {'SCALE_DB_NAME': '*****', 'SCALE_DB_USER': '*****', 'SCALE_DB_PASS': '*****',
                                          'SCALE_DB_HOST': '*****', 'SCALE_DB_PORT': '*****'}
        expected_main_secret_settings = {'s_1': 's_1_secret', 's_2': 's_2_secret', 's_3': 's_3_value'}
        expected_main_censored_settings = {'s_1': '*****', 's_2': '*****', 's_3': 's_3_value'}
        expected_main_secret_env_vars = {'S_1': 's_1_secret', 'S_2': 's_2_secret', 'S_3': 's_3_value',
                                         'my_special_env': 's_2_secret'}
        expected_main_censored_env_vars = {'S_1': '*****', 'S_2': '*****', 'S_3': 's_3_value',
                                           'my_special_env': '*****'}

        # Ensure secrets configuration is valid
        ExecutionConfiguration(exe_config_with_secrets.get_dict())

        # Check config with secrets
        did_pre_task = False
        did_main_task = False
        for task_dict in exe_config_with_secrets.get_dict()['tasks']:
            if task_dict['type'] == 'pre':
                for setting_name, setting_value in task_dict['settings'].items():
                    if setting_name in expected_pre_secret_settings:
                        expected_value = expected_pre_secret_settings[setting_name]
                        self.assertEqual(setting_value, expected_value)
                        del expected_pre_secret_settings[setting_name]
                for env_name, env_value in task_dict['env_vars'].items():
                    if env_name in expected_pre_secret_env_vars:
                        expected_value = expected_pre_secret_env_vars[env_name]
                        self.assertEqual(env_value, expected_value)
                        del expected_pre_secret_env_vars[env_name]
                self.assertDictEqual(expected_pre_secret_settings, {}, 'Config did not contain some expected settings')
                self.assertDictEqual(expected_pre_secret_env_vars, {}, 'Config did not contain some expected env vars')
                did_pre_task = True
            elif task_dict['type'] == 'main':
                for setting_name, setting_value in task_dict['settings'].items():
                    if setting_name in expected_main_secret_settings:
                        expected_value = expected_main_secret_settings[setting_name]
                        self.assertEqual(setting_value, expected_value)
                        del expected_main_secret_settings[setting_name]
                for env_name, env_value in task_dict['env_vars'].items():
                    if env_name in expected_main_secret_env_vars:
                        expected_value = expected_main_secret_env_vars[env_name]
                        self.assertEqual(env_value, expected_value)
                        del expected_main_secret_env_vars[env_name]
                self.assertDictEqual(expected_main_secret_settings, {}, 'Config did not contain some expected settings')
                self.assertDictEqual(expected_main_secret_env_vars, {}, 'Config did not contain some expected env vars')
                did_main_task = True
        self.assertTrue(did_pre_task)
        self.assertTrue(did_main_task)

        # Check censored config
        did_pre_task = False
        did_main_task = False
        exe_config_censored = job_exe_model.get_execution_configuration()
        for task_dict in exe_config_censored.get_dict()['tasks']:
            if task_dict['type'] == 'pre':
                for setting_name, setting_value in task_dict['settings'].items():
                    if setting_name in expected_pre_censored_settings:
                        expected_value = expected_pre_censored_settings[setting_name]
                        self.assertEqual(setting_value, expected_value)
                        del expected_pre_censored_settings[setting_name]
                for env_name, env_value in task_dict['env_vars'].items():
                    if env_name in expected_pre_censored_env_vars:
                        expected_value = expected_pre_censored_env_vars[env_name]
                        self.assertEqual(env_value, expected_value)
                        del expected_pre_censored_env_vars[env_name]
                self.assertDictEqual(expected_pre_censored_settings, {},
                                     'Config did not contain some expected settings')
                self.assertDictEqual(expected_pre_censored_env_vars, {},
                                     'Config did not contain some expected env vars')
                did_pre_task = True
            elif task_dict['type'] == 'main':
                for setting_name, setting_value in task_dict['settings'].items():
                    if setting_name in expected_main_censored_settings:
                        expected_value = expected_main_censored_settings[setting_name]
                        self.assertEqual(setting_value, expected_value)
                        del expected_main_censored_settings[setting_name]
                for env_name, env_value in task_dict['env_vars'].items():
                    if env_name in expected_main_censored_env_vars:
                        expected_value = expected_main_censored_env_vars[env_name]
                        self.assertEqual(env_value, expected_value)
                        del expected_main_censored_env_vars[env_name]
                self.assertDictEqual(expected_main_censored_settings, {},
                                     'Config did not contain some expected settings')
                self.assertDictEqual(expected_main_censored_env_vars, {},
                                     'Config did not contain some expected env vars')
                did_main_task = True
        self.assertTrue(did_pre_task)
        self.assertTrue(did_main_task)

    def test_configure_scheduled_job_shared_mem(self):
        """Tests successfully calling configure_scheduled_job() with a job using shared memory"""

        framework_id = '1234'
        node = node_test_utils.create_node()
        job_type = job_test_utils.create_job_type()
        job_type.shared_mem_required = 1024.0
        job_type.save()
        from queue.job_exe import QueuedJobExecution
        from queue.models import Queue
        job = Queue.objects.queue_new_job(job_type, JobData({}), trigger_test_utils.create_trigger_event())
        # Get job info off of the queue
        queue = Queue.objects.get(job_id=job.id)
        queued_job_exe = QueuedJobExecution(queue)
        queued_job_exe.scheduled('agent_1', node.id, job.get_resources())
        job_exe_model = queued_job_exe.create_job_exe_model(framework_id, now())

        # Test method
        with patch('django.conf.settings') as mock_settings:
            with patch('scheduler.vault.manager.secrets_mgr') as mock_secrets_mgr:
                mock_settings.LOGGING_ADDRESS = None  # Ignore logging settings, there's enough in this unit test
                mock_settings.DATABASES = {'default': {'SCALE_DB_NAME': 'TEST_NAME', 'SCALE_DB_USER': 'TEST_USER',
                                                       'SCALE_DB_PASS': 'TEST_PASSWORD', 'SCALE_DB_HOST': 'TEST_HOST',
                                                       'SCALE_DB_PORT': 'TEST_PORT'}}
                mock_secrets_mgr.retrieve_job_type_secrets = MagicMock()
                mock_secrets_mgr.retrieve_job_type_secrets.return_value = {}
            configurator = ScheduledExecutionConfigurator({})
            exe_config_with_secrets = configurator.configure_scheduled_job(job_exe_model, job_type,
                                                                           queue.get_job_interface(), 'INFO')

        # Ensure configuration is valid
        ExecutionConfiguration(exe_config_with_secrets.get_dict())
        # Compare results
        found_shm_size = False
        for param in exe_config_with_secrets.get_docker_params('main'):
            if param.flag == 'shm-size':
                found_shm_size = True
                self.assertEqual(param.value, '1024m')
                break
        self.assertTrue(found_shm_size)
        env_vars = exe_config_with_secrets.get_env_vars('main')
        self.assertTrue('ALLOCATED_SHARED_MEM' in env_vars)
        self.assertEqual(env_vars['ALLOCATED_SHARED_MEM'], '1024.0')
