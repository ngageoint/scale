"""Defines the command that performs the pre-job steps"""
from __future__ import unicode_literals

import logging
import sys

from django.core.management.base import BaseCommand
from optparse import make_option

from error.exceptions import ScaleError, get_error_by_exception
from job.models import JobExecution
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


class Command(BaseCommand):
    """Command that performs the pre-job steps for a job execution
    """

    option_list = BaseCommand.option_list + (
        make_option('-i', '--job-exe-id', action='store', type='int',
                    help=('The ID of the job execution')),
    )

    help = 'Performs the pre-job steps for a job execution'

    def handle(self, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        """
        job_exe_id = options.get('job_exe_id')

        logger.info('Command starting: scale_pre_steps - Job Execution ID: %i', job_exe_id)
        try:
            job_exe = self._get_job_exe(job_exe_id)

            job_interface = job_exe.get_job_interface()
            job_configuration = job_exe.get_execution_configuration()
            job_interface.validate_populated_settings(job_configuration)
            job_data = job_exe.job.get_job_data()
            job_environment = job_exe.get_job_environment()
            job_interface.perform_pre_steps(job_data, job_environment)
            command_args = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)

            command_args = job_interface.populate_command_argument_settings(command_args, job_configuration)

            logger.info('Executing job: %i -> %s', job_exe_id, ' '.join(command_args))
            self._populate_command_arguments(job_exe_id, command_args)
        except ScaleError as err:
            err.log()
            sys.exit(err.exit_code)
        except Exception as ex:
            exit_code = GENERAL_FAIL_EXIT_CODE
            err = get_error_by_exception(ex.__class__.__name__)
            if err:
                err.log()
                exit_code = err.exit_code
            else:
                logger.exception('Job Execution %i: Error performing pre-job steps', job_exe_id)
            sys.exit(exit_code)

        logger.info('Command completed: scale_pre_steps')

    @retry_database_query
    def _get_job_exe(self, job_exe_id):
        """Returns the job execution for the ID with its related job and job type models

        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        :returns: The job execution model
        :rtype: :class:`job.models.JobExecution`
        """

        return JobExecution.objects.get_job_exe_with_job_and_job_type(job_exe_id)

    @retry_database_query
    def _populate_command_arguments(self, job_exe_id, command_args):
        """Populates the full set of command arguments for the job execution

        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        :param command_args: The new job execution command argument string with pre-job step information filled in
        :type command_args: str
        """

        JobExecution.objects.pre_steps_command_arguments(job_exe_id, command_args)
