from __future__ import unicode_literals


import django
from django.db.utils import DatabaseError, OperationalError
from django.utils.timezone import now
from django.test import TestCase, TransactionTestCase
from mock import patch

from error.exceptions import ScaleDatabaseError, ScaleIOError, ScaleOperationalError
from job.configuration.results.exceptions import InvalidResultsManifest, MissingRequiredOutput
from job.configuration.results.job_results import JobResults
from job.configuration.results.results_manifest.results_manifest import ResultsManifest
from job.management.commands.scale_post_steps import Command as PostCommand
from job.models import JobExecution
from job.test import utils as job_utils
from trigger.models import TriggerEvent


JOB_RESULTS = JobResults()
RESULTS_MANIFEST = ResultsManifest()
RESULTS = (JOB_RESULTS, RESULTS_MANIFEST)


class TestPostJobSteps(TransactionTestCase):

    def setUp(self):
        django.setup()

        cmd = 'command'
        cmd_args = 'args'
        interface = {'version': '1.0', 'command': cmd, 'command_arguments': cmd_args, 'inputs': [],
                     'outputs': [{'name': 'arg1'}, {'name': 'arg2'}]}

        self.job_type = job_utils.create_job_type(name='Test', version='1.0', interface=interface)
        self.event = TriggerEvent.objects.create_trigger_event('TEST', None, {}, now())
        self.job = job_utils.create_job(job_type=self.job_type, event=self.event, status='RUNNING')
        self.running_job_exe = job_utils.create_running_job_exe(job=self.job)
        self.job_exe = JobExecution.objects.get(id=self.running_job_exe.id)

    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    def test_scale_post_steps_successful(self, mock_job_exe_manager):
        """Tests successfully executing scale_post_steps."""

        # Set up mocks
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.get_job_interface.return_value.perform_post_steps.return_value = RESULTS
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.id = self.job_exe.id

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_job_exe_manager.post_steps_results.assert_called_with(self.job_exe.id, JOB_RESULTS, RESULTS_MANIFEST)

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects.select_related')
    def test_scale_post_steps_database_error(self, mock_db, mock_sys_exit):
        """Tests executing scale_post_steps when a database error occurs."""

        # Set up mocks
        mock_db.side_effect = DatabaseError()

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_sys_exit.assert_called_with(ScaleDatabaseError().exit_code)

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects.select_related')
    def test_scale_post_steps_database_operation_error(self, mock_db, mock_sys_exit):
        """Tests executing scale_post_steps when a database operation error occurs."""

        # Set up mocks
        mock_db.side_effect = OperationalError()

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_sys_exit.assert_called_with(ScaleOperationalError().exit_code)

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    def test_scale_post_steps_io_error(self, mock_job_exe_manager, mock_sys_exit):
        """Tests executing scale_post_steps when an IO error occurs."""

        # Set up mocks
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.get_job_interface.return_value.perform_post_steps.side_effect = IOError()

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_sys_exit.assert_called_with(ScaleIOError().exit_code)

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    def test_scale_post_steps_invalid_manifest_error(self, mock_job_exe_manager, mock_sys_exit):
        """Tests executing scale_post_steps when an invalid manifest occurs."""

        # Set up mocks
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.get_job_interface.return_value.perform_post_steps.side_effect = InvalidResultsManifest('')

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_sys_exit.assert_called_with(InvalidResultsManifest('').exit_code)

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    def test_scale_post_steps_missing_manifest_output_error(self, mock_job_exe_manager, mock_sys_exit):
        """Tests executing scale_post_steps when a missing output manifest occurs."""

        # Set up mocks
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.get_job_interface.return_value.perform_post_steps.side_effect = MissingRequiredOutput('')

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_sys_exit.assert_called_with(MissingRequiredOutput('').exit_code)

    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    def test_scale_post_steps_no_stderr(self, mock_job_exe_manager):
        """Tests successfully executing scale_post_steps."""

        # Set up mocks
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.stdout = 'something'
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.stderr = None
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.get_job_interface.return_value.perform_post_steps.return_value = RESULTS
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.id = self.job_exe.id

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps', '-i', str(self.job_exe.id)])

        # Check results
        mock_job_exe_manager.post_steps_results.assert_called_with(self.job_exe.id, JOB_RESULTS, RESULTS_MANIFEST)
