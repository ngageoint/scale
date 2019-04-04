from __future__ import unicode_literals


import django
from django.db.utils import DatabaseError, OperationalError
from django.utils.timezone import now
from django.test import TransactionTestCase
from mock import patch

from error.exceptions import ScaleDatabaseError, ScaleIOError, ScaleOperationalError
from job.configuration.results.exceptions import InvalidResultsManifest, MissingRequiredOutput
from job.seed.results.job_results import JobResults
from job.configuration.results.results_manifest.results_manifest import ResultsManifest
from job.management.commands.scale_post_steps import Command as PostCommand
from job.models import JobExecutionOutput
from job.test import utils as job_utils
from recipe.test import utils as recipe_utils
from trigger.models import TriggerEvent


JOB_RESULTS = JobResults()
RESULTS_MANIFEST = ResultsManifest()
RESULTS = (JOB_RESULTS, RESULTS_MANIFEST)


class TestPostJobSteps(TransactionTestCase):

    def setUp(self):
        django.setup()

        self.recipe_type = recipe_utils.create_recipe_type_v6()
        self.recipe = recipe_utils.create_recipe(recipe_type=self.recipe_type)
        cmd = 'command'
        cmd_args = 'args'

        outputs = [{'name': 'arg1', 'pattern': '*_.txt'}, {'name': 'arg2', 'pattern': '*_.txt'}]
        manifest = job_utils.create_seed_manifest(command='command args', outputs_files=outputs)

        self.job_type = job_utils.create_seed_job_type(job_version='1.0', manifest=manifest)
        self.recipe_type = recipe_utils.create_recipe_type_v6()
        self.recipe = recipe_utils.create_recipe(recipe_type=self.recipe_type)
        self.event = TriggerEvent.objects.create_trigger_event('TEST', None, {}, now())
        self.job = job_utils.create_job(job_type=self.job_type, event=self.event, status='RUNNING', recipe=self.recipe)
        self.job_exe = job_utils.create_job_exe(job=self.job, status='RUNNING')

    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    @patch('job.management.commands.scale_post_steps.os.environ.get')
    def test_scale_post_steps_successful(self, mock_env_vars, mock_job_exe_manager):
        """Tests successfully executing scale_post_steps."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.job.id) if name == 'SCALE_JOB_ID' else str(self.job_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.job_type.get_job_interface.return_value.perform_post_steps.return_value = RESULTS
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.id = self.job_exe.id
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.job_id = self.job_exe.job_id
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.job_type_id = self.job_exe.job_type_id
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.exe_num = self.job_exe.exe_num

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps'])

        # Check results
        job_exe_output = JobExecutionOutput.objects.get(job_exe_id=self.job_exe.id)
        self.assertDictEqual(job_exe_output.get_output().get_dict(), JOB_RESULTS.get_dict())

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects.select_related')
    @patch('job.management.commands.scale_post_steps.os.environ.get')
    def test_scale_post_steps_database_error(self, mock_env_vars, mock_db, mock_sys_exit):
        """Tests executing scale_post_steps when a database error occurs."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.job.id) if name == 'SCALE_JOB_ID' else str(self.job_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_db.side_effect = DatabaseError()

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleDatabaseError().exit_code)

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects.select_related')
    @patch('job.management.commands.scale_post_steps.os.environ.get')
    def test_scale_post_steps_database_operation_error(self, mock_env_vars, mock_db, mock_sys_exit):
        """Tests executing scale_post_steps when a database operation error occurs."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.job.id) if name == 'SCALE_JOB_ID' else str(self.job_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_db.side_effect = OperationalError()

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleOperationalError().exit_code)

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    @patch('job.management.commands.scale_post_steps.os.environ.get')
    def test_scale_post_steps_io_error(self, mock_env_vars, mock_job_exe_manager, mock_sys_exit):
        """Tests executing scale_post_steps when an IO error occurs."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.job.id) if name == 'SCALE_JOB_ID' else str(self.job_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.job_type.get_job_interface.return_value.perform_post_steps.side_effect = IOError()

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps'])

        # Check results
        mock_sys_exit.assert_called_with(ScaleIOError().exit_code)

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    @patch('job.management.commands.scale_post_steps.os.environ.get')
    def test_scale_post_steps_invalid_manifest_error(self, mock_env_vars, mock_job_exe_manager, mock_sys_exit):
        """Tests executing scale_post_steps when an invalid manifest occurs."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.job.id) if name == 'SCALE_JOB_ID' else str(self.job_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.job_type.get_job_interface.return_value.perform_post_steps.side_effect = InvalidResultsManifest('')

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps'])

        # Check results
        mock_sys_exit.assert_called_with(InvalidResultsManifest('').exit_code)

    @patch('job.management.commands.scale_post_steps.sys.exit')
    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    @patch('job.management.commands.scale_post_steps.os.environ.get')
    def test_scale_post_steps_missing_manifest_output_error(self, mock_env_vars, mock_job_exe_manager, mock_sys_exit):
        """Tests executing scale_post_steps when a missing output manifest occurs."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.job.id) if name == 'SCALE_JOB_ID' else str(self.job_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.job_type.get_job_interface.return_value.perform_post_steps.side_effect = MissingRequiredOutput('')

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps'])

        # Check results
        mock_sys_exit.assert_called_with(MissingRequiredOutput('').exit_code)

    @patch('job.management.commands.scale_post_steps.JobExecution.objects')
    @patch('job.management.commands.scale_post_steps.os.environ.get')
    def test_scale_post_steps_no_stderr(self, mock_env_vars, mock_job_exe_manager):
        """Tests successfully executing scale_post_steps."""

        # Set up mocks
        def get_env_vars(name, *args, **kwargs):
            return str(self.job.id) if name == 'SCALE_JOB_ID' else str(self.job_exe.exe_num)
        mock_env_vars.side_effect = get_env_vars
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.stdout = 'something'
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.stderr = None
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.job_type.get_job_interface.return_value.perform_post_steps.return_value = RESULTS
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.id = self.job_exe.id
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.job_id = self.job_exe.job_id
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.job_type_id = self.job_exe.job_type_id
        mock_job_exe_manager.get_job_exe_with_job_and_job_type.return_value.exe_num = self.job_exe.exe_num

        # Call method to test
        cmd = PostCommand()
        cmd.run_from_argv(['manage.py', 'scale_post_steps'])

        # Check results
        job_exe_output = JobExecutionOutput.objects.get(job_exe_id= self.job_exe.id)
        self.assertDictEqual(job_exe_output.get_output().get_dict(), JOB_RESULTS.get_dict())
