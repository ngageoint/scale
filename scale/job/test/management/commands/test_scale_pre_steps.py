from __future__ import unicode_literals

import django
from django.db.utils import DatabaseError, OperationalError
from django.utils.timezone import now
from django.test import TransactionTestCase
from mock import patch

from error.exceptions import ScaleDatabaseError, ScaleIOError, ScaleOperationalError
from job.management.commands.scale_pre_steps import Command as PreCommand
from job.test import utils as job_utils
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
        interface = {'version': '1.0', 'command': cmd, 'command_arguments': cmd_args}

        self.job_type = job_utils.create_job_type(name='Test', version='1.0', interface=interface)
        self.event = TriggerEvent.objects.create_trigger_event('TEST', None, {}, now())
        self.job = job_utils.create_job(job_type=self.job_type, event=self.event, status='RUNNING')
        self.job_exe = job_utils.create_job_exe(job=self.job, status='RUNNING', timeout=timeout, queued=now())

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('os.environ.get')
    def test_scale_pre_steps_successful(self, mock_env_vars, mock_sysexit):
        """Tests successfully executing scale_pre_steps."""

        # Set up mocks
        mock_env_vars.return_value = 1

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Make sure sys.exit() was never called
        self.assertItemsEqual(mock_sysexit.call_args_list, [])

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.JobExecution.objects.select_related')
    @patch('os.environ.get')
    def test_scale_pre_steps_database_error(self, mock_env_vars, mock_db, mock_sys_exit):
        """Tests executing scale_pre_steps when a database error occurs."""

        # Set up mocks
        mock_env_vars.return_value = 1
        mock_db.side_effect = DatabaseError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleDatabaseError().exit_code)

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.JobExecution.objects.select_related')
    @patch('os.environ.get')
    def test_scale_pre_steps_database_operation_error(self, mock_env_vars, mock_db, mock_sys_exit):
        """Tests executing scale_pre_steps when a database operation error occurs."""

        # Set up mocks
        mock_env_vars.return_value = 1
        mock_db.side_effect = OperationalError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleOperationalError().exit_code)

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.JobExecution')
    @patch('os.environ.get')
    def test_scale_pre_steps_io_error(self, mock_env_vars, mock_job_exe, mock_sys_exit):
        """Tests executing scale_pre_steps when an IO error occurs."""

        # Set up mocks
        mock_env_vars.return_value = '1'
        mock_job_exe.objects.get_job_exe_with_job_and_job_type.return_value.get_job_interface.return_value.perform_pre_steps.side_effect = IOError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleIOError().exit_code)
