#@PydevCodeAnalysisIgnore
from __future__ import unicode_literals

import os

import django
from django.db.utils import DatabaseError
from django.utils.timezone import now
from django.test import TestCase
from mock import patch

from job.models import Job, JobExecution, JobType
from job.management.commands.scale_pre_steps import Command as PreCommand, DB_EXIT_CODE as PRE_DB_EXIT_CODE, \
    NFS_EXIT_CODE as PRE_NFS_EXIT_CODE, IO_EXIT_CODE as PRE_IO_EXIT_CODE
from job.test import utils as job_utils
from storage.exceptions import NfsError
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


class TestPreJobSteps(TestCase):

    def setUp(self):
        django.setup()

        cmd = 'command'
        cmd_args = 'run test'
        priority = 100
        timeout = 60
        max_tries = 1
        cpus = 1.0
        mem = 1.0
        disk = 1.0
        interface = {'version': '1.0', 'command': cmd, 'command_arguments': cmd_args}

        self.job_type = job_utils.create_job_type(name='Test', version='1.0', interface=interface)
        self.event = TriggerEvent.objects.create_trigger_event('TEST', None, {}, now())
        self.job = job_utils.create_job(job_type=self.job_type, event=self.event, status='RUNNING')
        self.job_exe = job_utils.create_job_exe(job=self.job, status='RUNNING', command_arguments=cmd_args, timeout=timeout, queued=now())

    @patch('job.management.commands.scale_post_steps.subprocess.check_call')
    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.Command._chmod_job_dir')
    @patch('job.management.commands.scale_pre_steps.JobExecution')
    @patch('job.management.commands.scale_pre_steps.file_system')
    def test_scale_pre_steps_successful(self, mock_file_system, mock_job_exe, mock_chmod, mock_sysexit, mock_subprocess):
        '''Tests successfully executing scale_pre_steps.'''

        # Set up mocks
        mock_job_exe.objects.get_job_exe_with_job_and_job_type.return_value.get_job_interface.return_value.fully_populate_command_argument.return_value = FILLED_IN_CMD
        mock_job_exe.objects.get_job_exe_with_job_and_job_type.return_value.get_docker_image.return_value = None

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_job_exe.objects.pre_steps_command_arguments.assert_called_with(self.job_exe.id, FILLED_IN_CMD)

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.JobExecution.objects.select_related')
    @patch('job.management.commands.scale_pre_steps.os.makedirs')
    def test_scale_pre_steps_database_error(self, mock_makedirs, mock_db, mock_sys_exit):
        '''Tests executing scale_pre_steps when a database error occurs.'''

        # Set up mocks
        mock_db.side_effect = DatabaseError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_sys_exit.assert_called_with(PRE_DB_EXIT_CODE)

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.JobExecution')
    @patch('job.management.commands.scale_pre_steps.file_system')
    def test_scale_pre_steps_nfs_error(self, mock_file_system, mock_job_exe, mock_sys_exit):
        '''Tests executing scale_pre_steps when an NFS error occurs.'''

        # Set up mocks
        mock_job_exe.objects.get_job_exe_with_job_and_job_type.return_value.get_job_interface.return_value.perform_pre_steps.side_effect = NfsError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_sys_exit.assert_called_with(PRE_NFS_EXIT_CODE)

    @patch('job.management.commands.scale_pre_steps.sys.exit')
    @patch('job.management.commands.scale_pre_steps.JobExecution')
    @patch('job.management.commands.scale_pre_steps.file_system')
    def test_scale_pre_steps_io_error(self, mock_file_system, mock_job_exe, mock_sys_exit):
        '''Tests executing scale_pre_steps when an IO error occurs.'''

        # Set up mocks
        mock_job_exe.objects.get_job_exe_with_job_and_job_type.return_value.get_job_interface.return_value.perform_pre_steps.side_effect = IOError()

        # Call method to test
        cmd = PreCommand()
        cmd.run_from_argv(['manage.py', 'scale_pre_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_sys_exit.assert_called_with(PRE_IO_EXIT_CODE)
