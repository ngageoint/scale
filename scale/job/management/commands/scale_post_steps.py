"""Defines the command that performs the post-job steps"""
from __future__ import unicode_literals

import logging
import os
import sys

from django.core.management.base import BaseCommand
from django.db import transaction

from error.exceptions import ScaleError, get_error_by_exception
from job.models import JobExecution, JobExecutionOutput
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


class Command(BaseCommand):
    """Command that performs the post-job steps for a job execution
    """

    help = 'Performs the post-job steps for a job execution'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        """

        job_id = int(os.environ.get('SCALE_JOB_ID'))
        exe_num = int(os.environ.get('SCALE_EXE_NUM'))

        logger.info('Command starting: scale_post_steps - Job ID: %d, Execution Number: %d', job_id, exe_num)
        try:
            # Get the pre-loaded job_exe for efficiency
            job_exe = self._get_job_exe(job_id, exe_num)

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
                logger.exception('Error performing post-job steps')
            sys.exit(exit_code)

        logger.info('Command completed: scale_post_steps')

    @retry_database_query
    def _get_job_exe(self, job_id, exe_num):
        """Returns the job execution for the ID with its related job and job type models

        :param job_id: The job ID
        :type job_id: int
        :param exe_num: The execution number
        :type exe_num: int
        :returns: The job execution model
        :rtype: :class:`job.models.JobExecution`
        """

        return JobExecution.objects.get_job_exe_with_job_and_job_type(job_id, exe_num)

    @retry_database_query
    def _perform_post_steps(self, job_exe):
        """Populates the full set of command arguments for the job execution

        :param job_exe: The job execution
        :type job_exe: :class:`job.models.JobExecution`
        """

        job_interface = job_exe.job_type.get_job_interface()
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
            job_exe_output = JobExecutionOutput()
            job_exe_output.job_exe_id = job_exe.id
            job_exe_output.job_id = job_exe.job_id
            job_exe_output.job_type_id = job_exe.job_type_id
            job_exe_output.exe_num = job_exe.exe_num
            job_exe_output.output = job_results.get_dict()
            job_exe_output.save()
