'''Defines the command that performs the pre-job steps'''
from __future__ import unicode_literals

import logging
import os
import subprocess
import sys

from django.core.management.base import BaseCommand
from django.db.utils import DatabaseError
from optparse import make_option

import job.execution.file_system as file_system
from error.models import Error
from job.models import JobExecution
from storage.exceptions import NfsError

logger = logging.getLogger(__name__)

# Exit codes that map to specific job errors
DB_EXIT_CODE = 1001
IO_EXIT_CODE = 1002
NFS_EXIT_CODE = 1003
EXIT_CODE_DICT = {DB_EXIT_CODE, Error.objects.get_database_error,
                  IO_EXIT_CODE, Error.objects.get_filesystem_error,
                  NFS_EXIT_CODE, Error.objects.get_nfs_error}


class Command(BaseCommand):
    '''Command that performs the pre-job steps for a job execution
    '''

    option_list = BaseCommand.option_list + (
        make_option('-i', '--job-exe-id', action='store', type='int',
                    help=('The ID of the job execution')),
    )

    help = 'Performs the pre-job steps for a job execution'

    def handle(self, **options):
        '''See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the command.
        '''
        job_exe_id = options.get('job_exe_id')

        logger.info('Command starting: scale_pre_steps - Job Execution ID: %i', job_exe_id)
        try:
            job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(job_exe_id)

            file_system.create_job_exe_dir(job_exe_id)
            file_system.create_normal_job_exe_dir_tree(job_exe_id)

            job_interface = job_exe.get_job_interface()
            job_data = job_exe.job.get_job_data()
            job_environment = job_exe.get_job_environment()
            job_interface.perform_pre_steps(job_data, job_environment, job_exe_id)
            command_args = job_interface.fully_populate_command_argument(job_data, job_environment, job_exe_id)

            # This shouldn't be necessary once we have user namespaces in docker
            self._chmod_job_dir(file_system.get_job_exe_output_data_dir(job_exe_id))

            # Perform a force pull for docker jobs to get the latest version of the image before running
            # TODO: Remove this hack in favor of the feature in Mesos 0.22.x, see MESOS-1886 for details
            docker_image = job_exe.job.job_type.docker_image
            if docker_image:
                logger.info('Pulling latest docker image: %s', docker_image)
                try:
                    subprocess.check_call(['sudo', 'docker', 'pull', docker_image])
                except subprocess.CalledProcessError:
                    logger.exception('Docker pull returned unexpected exit code.')
                except OSError:
                    logger.exception('OS unable to run docker pull command.')

            logger.info('Executing job: %i -> %s', job_exe_id, ' '.join(command_args))
            JobExecution.objects.pre_steps_command_arguments(job_exe_id, command_args)
        except Exception as ex:
            logger.exception('Job Execution %i: Error performing pre-job steps', job_exe_id)

            exit_code = -1
            if isinstance(ex, DatabaseError):
                exit_code = DB_EXIT_CODE
            elif isinstance(ex, NfsError):
                exit_code = NFS_EXIT_CODE
            elif isinstance(ex, IOError):
                exit_code = IO_EXIT_CODE
            sys.exit(exit_code)
        logger.info('Command completed: scale_pre_steps')

    def _chmod_job_dir(self, target_dir):
        '''Changes permissions of the given directory to be wide open.

        :param target_dir: The path of the directory to modify.
        :type target_dir: str
        '''
        for root, dirs, files in os.walk(target_dir):
            for _dir in dirs:
                os.chmod(os.path.join(root, _dir), 0777)
            for _dir in files:
                os.chmod(os.path.join(root, _dir), 0777)
