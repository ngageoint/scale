"""Defines the command that performs the post-job steps"""
from __future__ import unicode_literals

import logging
import sys
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import transaction

from error.exceptions import ScaleError, get_error_by_exception
from job.models import JobExecution
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


class Command(BaseCommand):
    """Command that performs the post-job steps for a job execution
    """

    help = 'Performs the post-job steps for a job execution'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--job-exe-id', action='store', type='int',
                            help='The ID of the job execution')

    def handle(self, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        """
        exe_id = options.get('job_exe_id')

        logger.info('Command starting: scale_post_steps - Job Execution ID: %i', exe_id)
        try:
            # Get the pre-loaded job_exe for efficiency
            job_exe = self._get_job_exe(exe_id)

            self._perform_post_steps(job_exe)
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
                logger.exception('Job Execution %i: Error performing post-job steps', exe_id)
            sys.exit(exit_code)

        logger.info('Command completed: scale_post_steps')

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
    def _perform_post_steps(self, job_exe):
        """Populates the full set of command arguments for the job execution

        :param job_exe: The job execution
        :type job_exe: :class:`job.models.JobExecution`
        """

        job_interface = job_exe.get_job_interface()
        job_data = job_exe.job.get_job_data()
        stdout_and_stderr = None
        try:
            stdout_and_stderr, _last_modified = job_exe.get_log_text()
        except:
            logger.exception('Failed to retrieve job execution logs')
        if stdout_and_stderr is None:
            stdout_and_stderr = ''

        with transaction.atomic():
            job_results, results_manifest = job_interface.perform_post_steps(job_exe, job_data, stdout_and_stderr)
            JobExecution.objects.post_steps_results(job_exe.id, job_results, results_manifest)
