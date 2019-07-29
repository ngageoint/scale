from __future__ import unicode_literals

import django
from django.db.utils import DatabaseError, OperationalError
from django.utils.timezone import now
from django.test import TransactionTestCase
from mock import patch

from error.exceptions import ScaleDatabaseError, ScaleIOError, ScaleOperationalError
from job.configuration.data.exceptions import InvalidConnection
from job.management.commands.scale_pre_steps import Command as PreCommand
from job.test import utils as job_utils
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

        manifest = job_utils.create_seed_manifest(command='command run test')
        self.seed_job_type = job_utils.create_seed_job_type(manifest=manifest)
        self.event = TriggerEvent.objects.create_trigger_event('TEST', None, {}, now())
        self.seed_job = job_utils.create_job(job_type=self.seed_job_type, event=self.event, status='RUNNING')
        config = {'output_workspaces': {'default': storage_utils.create_workspace().name}}
        self.seed_exe = job_utils.create_job_exe(job=self.seed_job, status='RUNNING', timeout=timeout, queued=now(), configuration=config)

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
        mock_job_exe.objects.get_job_exe_with_job_and_job_type.return_value.job_type.get_job_interface.return_value.needs_input_metadata.return_value = None
        mock_job_exe.objects.get_job_exe_with_job_and_job_type.return_value.job_type.get_job_interface.return_value.perform_pre_steps.side_effect = IOError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleIOError().exit_code)
