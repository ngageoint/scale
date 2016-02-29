'''Defines the command that performs the post-job steps'''
from __future__ import unicode_literals

import logging
import subprocess
import sys
from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import DatabaseError

import job.execution.file_system as file_system
import job.settings as settings
from error.models import Error
from job.execution.cleanup import cleanup_job_exe
from job.models import JobExecution
from storage.exceptions import NfsError
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


# Exit codes that map to specific job errors
DB_EXIT_CODE = 1001
IO_EXIT_CODE = 1002
NFS_EXIT_CODE = 1003
EXIT_CODE_DICT = {DB_EXIT_CODE, Error.objects.get_database_error,
                  IO_EXIT_CODE, Error.objects.get_filesystem_error,
                  NFS_EXIT_CODE, Error.objects.get_nfs_error}


class Command(BaseCommand):
    '''Command that performs the post-job steps for a job execution
    '''

    option_list = BaseCommand.option_list + (
        make_option('-i', '--job-exe-id', action='store', type='int',
                    help=('The ID of the job execution')),
    )

    help = 'Performs the post-job steps for a job execution'

    def handle(self, **options):
        '''See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        '''
        exe_id = options.get('job_exe_id')

        logger.info('Command starting: scale_post_steps - Job Execution ID: %i', exe_id)
        try:
            output_dir = file_system.get_job_exe_output_dir(exe_id)

            # TODO: remove when we can
            # This shouldn't be necessary once we have user namespaces in docker
            if output_dir:
                subprocess.call(['sudo', 'chmod', '-R', '777', output_dir])

            # Get the pre-loaded job_exe for efficiency
            job_exe = self._get_job_exe(exe_id)

            self._perform_post_steps(job_exe)

            if not settings.settings.SKIP_CLEANUP_JOB_DIR:
                self._cleanup(exe_id)
        except Exception as ex:
            logger.exception('Job Execution %i: Error performing post-job steps', exe_id)

            if not settings.settings.SKIP_CLEANUP_JOB_DIR:
                self._cleanup(exe_id)

            exit_code = -1
            if isinstance(ex, DatabaseError):
                exit_code = DB_EXIT_CODE
            elif isinstance(ex, NfsError):
                exit_code = NFS_EXIT_CODE
            elif isinstance(ex, IOError):
                exit_code = IO_EXIT_CODE
            sys.exit(exit_code)

        logger.info('Command completed: scale_post_steps')

    def _cleanup(self, exe_id):
        '''Cleans up the work directory for the job. This method is safe and should not throw any exceptions.
        '''

        try:
            cleanup_job_exe(exe_id)
        except Exception:
            logger.exception('Job Execution %i: Error cleaning up', exe_id)

    @retry_database_query
    def _get_job_exe(self, job_exe_id):
        '''Returns the job execution for the ID with its related job and job type models

        :param job_exe_id: The job execution ID
        :type job_exe_id: int
        :returns: The job execution model
        :rtype: :class:`job.models.JobExecution`
        '''

        return JobExecution.objects.get_job_exe_with_job_and_job_type(job_exe_id)

    @retry_database_query
    def _perform_post_steps(self, job_exe):
        '''Populates the full set of command arguments for the job execution

        :param job_exe: The job execution
        :type job_exe: :class:`job.models.JobExecution`
        '''

        job_interface = job_exe.get_job_interface()
        job_data = job_exe.job.get_job_data()
        stdout_and_stderr = (job_exe.stdout or '') + '\n' + (job_exe.stderr or '')

        with transaction.atomic():
            job_results, results_manifest = job_interface.perform_post_steps(job_exe, job_data, stdout_and_stderr)
            JobExecution.objects.post_steps_results(job_exe.id, job_results, results_manifest)
