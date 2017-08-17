"""Defines the command that performs the pre-job steps"""
from __future__ import unicode_literals

import logging
import os
import sys

from django.core.management.base import BaseCommand

from error.exceptions import ScaleError, get_error_by_exception
from job.models import JobExecution
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


GENERAL_FAIL_EXIT_CODE = 1


class Command(BaseCommand):
    """Command that performs the pre-job steps for a job execution
    """

    help = 'Performs the pre-job steps for a job execution'

    def handle(self, *args, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        """

        job_id = int(os.environ.get('SCALE_JOB_ID'))
        exe_num = int(os.environ.get('SCALE_EXE_NUM'))

        logger.info('Command starting: scale_pre_steps - Job ID: %d, Execution Number: %d', job_id, exe_num)
        try:
            job_exe = self._get_job_exe(job_id, exe_num)

            job_interface = job_exe.get_job_interface()
            exe_config = job_exe.get_execution_configuration()
            logger.info('Validating mounts...')
            job_interface.validate_populated_mounts(exe_config)
            logger.info('Validating settings...')
            job_interface.validate_populated_settings(exe_config)
            job_data = job_exe.job.get_job_data()
            logger.info('Setting up input files...')
            job_interface.perform_pre_steps(job_data, None)

            logger.info('Ready to execute job: %s', exe_config.get_args('main'))
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
                logger.exception('Error performing pre-job steps')
                print str(ex)
                ex.
            sys.exit(exit_code)

        logger.info('Command completed: scale_pre_steps')

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
