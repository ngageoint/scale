from __future__ import unicode_literals

import copy
import json

import django
from django.db.utils import DatabaseError, OperationalError
from django.utils.timezone import now
from django.test import TransactionTestCase
from mock import patch

from error.exceptions import ScaleDatabaseError, ScaleIOError, ScaleOperationalError
from job.configuration.data.exceptions import InvalidConnection
from job.execution.configuration.configurators import QueuedExecutionConfigurator
from job.management.commands.scale_pre_steps import Command as PreCommand
from job.test import utils as job_utils
from storage.models import ScaleFile
from storage.serializers import ScaleFileDetailsSerializerV6 as serialize
from storage.test import utils as storage_utils
from trigger.models import TriggerEvent

FILLED_IN_CMD = 'run test filled in'


def new_fill_in_command_dirs(job_exe):
    return FILLED_IN_CMD


def new_populate_output_args(config, args):
    for arg_name in args:
        arg_value = args[arg_name]
        for output in config['outputs']:
            if output['name'] == arg_name:
                output['value'] = arg_value
    return config


class TestPreJobSteps(TransactionTestCase):

    def setUp(self):
        django.setup()

        cmd = 'command'
        cmd_args = 'run test'
        timeout = 60

        workspace = storage_utils.create_workspace(base_url="http://test.com/")
        self.file_1 = storage_utils.create_file(workspace=workspace, file_path="path/1/file1.txt")
        self.file_2 = storage_utils.create_file(workspace=workspace, file_path="path/2/file2.txt")
        self.file_3 = storage_utils.create_file(workspace=workspace, file_path="path/3/file3.txt")
        input_files = {self.file_1.id: self.file_1, self.file_2.id: self.file_2, self.file_3.id: self.file_3}

        manifest = job_utils.create_seed_manifest(command='command run test')
        imm = copy.deepcopy(manifest)
        imm['job']['jobVersion'] = '1.0.1'
        imm['job']['interface']['inputs']['files'].append({'name': 'INPUT_METADATA_MANIFEST'})

        self.seed_job_type = job_utils.create_seed_job_type(manifest=manifest)
        self.seed_job_type_metadata = job_utils.create_seed_job_type(manifest=imm)
        self.event = TriggerEvent.objects.create_trigger_event('TEST', None, {}, now())
        self.seed_job = job_utils.create_job(job_type=self.seed_job_type, event=self.event, status='RUNNING')

        self.data_dict = {'json': {'input_1': 'my_val'},
                     'files': {'input_2': [self.file_1.id], 'input_3': [self.file_2.id, self.file_3.id]}}
        self.seed_job_meta = job_utils.create_job(job_type=self.seed_job_type_metadata, event=self.event,
                                                      input=self.data_dict, status='RUNNING')
        config = {'output_workspaces': {'default': storage_utils.create_workspace().name}}
        self.seed_exe = job_utils.create_job_exe(job=self.seed_job, status='RUNNING', timeout=timeout, queued=now(),
                                                 configuration=config)

        configurator = QueuedExecutionConfigurator(input_files)
        exe_config = configurator.configure_queued_job(self.seed_job_meta)
        self.seed_exe_meta = job_utils.create_job_exe(job=self.seed_job_meta, status='RUNNING', timeout=timeout, queued=now(),
                                                 configuration=exe_config.get_dict())

    @patch('__builtin__.open')
    @patch('job.management.commands.scale_pre_steps.json.dump')
    def test_generate_input_metadata(self, mock_dump, mock_open):

        cmd = PreCommand()

        cmd._generate_input_metadata(self.seed_exe_meta)
        mock_dump.assert_called_once()
        args, kwargs = mock_dump.call_args
        metadata_dict = {'JOB': {}}
        metadata_dict['JOB']['input_1'] = 'my_val'
        metadata_dict['JOB']['input_2'] = [serialize(ScaleFile.objects.get_details(file_id=self.file_1.id)).data]
        metadata_dict['JOB']['input_3'] = [serialize(ScaleFile.objects.get_details(file_id=self.file_2.id)).data, serialize(ScaleFile.objects.get_details(file_id=self.file_3.id)).data]
        self.maxDiff = None
        self.assertDictEqual(args[0]['JOB']['input_2'][0], metadata_dict['JOB']['input_2'][0])
        self.assertDictEqual(args[0], metadata_dict)

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.os.environ.get')
    def test_seed_pre_steps_no_workspace(self, mock_env_vars, mock_sysexit):

        seed_exe = job_utils.create_job_exe(job=self.seed_job, status='RUNNING', timeout=60, queued=now())
        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.seed_job.id) if name == 'SCALE_JOB_ID' else str(seed_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Make sure we get an exit code of 1
        mock_sysexit.assert_called_with(1)

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.os.environ.get')
    def test_scale_pre_steps_successful(self, mock_env_vars, mock_sysexit):
        """Tests successfully executing scale_pre_steps."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.seed_job.id) if name == 'SCALE_JOB_ID' else str(self.seed_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Make sure sys.exit() was never called
        self.assertItemsEqual(mock_sysexit.call_args_list, [])

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.JobExecution.objects.select_related')
    @patch('job.management.commands.scale_pre_steps.os.environ.get')
    def test_scale_pre_steps_database_error(self, mock_env_vars, mock_db, mock_sys_exit):
        """Tests executing scale_pre_steps when a database error occurs."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.seed_job.id) if name == 'SCALE_JOB_ID' else str(self.seed_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_db.side_effect = DatabaseError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleDatabaseError().exit_code)

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.JobExecution.objects.select_related')
    @patch('job.management.commands.scale_pre_steps.os.environ.get')
    def test_scale_pre_steps_database_operation_error(self, mock_env_vars, mock_db, mock_sys_exit):
        """Tests executing scale_pre_steps when a database operation error occurs."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.seed_job.id) if name == 'SCALE_JOB_ID' else str(self.seed_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_db.side_effect = OperationalError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleOperationalError().exit_code)

    @patch('job.management.commands.scale_pre_steps.JobData')
    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.JobExecution')
    @patch('job.management.commands.scale_pre_steps.os.environ.get')
    def test_scale_pre_steps_io_error(self, mock_env_vars, mock_job_exe, mock_sys_exit, mock_JobData):
        """Tests executing scale_pre_steps when an IO error occurs."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.seed_job.id) if name == 'SCALE_JOB_ID' else str(self.seed_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_job_exe.objects.get_job_exe_with_job_and_job_type.return_value.job_type.get_job_interface.return_value.perform_pre_steps.side_effect = IOError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleIOError().exit_code)
