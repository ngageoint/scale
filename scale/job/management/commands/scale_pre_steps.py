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
import job.settings as settings
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
        exe_id = options.get('job_exe_id')

        logger.info('Command starting: scale_pre_steps - Job Execution ID: %i', exe_id)
        try:
            node_work_dir = settings.NODE_WORK_DIR

            job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(exe_id)

            job_dir = file_system.get_job_exe_dir(exe_id, node_work_dir)
            input_dir = file_system.get_job_exe_input_dir(exe_id, node_work_dir)
            output_dir = file_system.get_job_exe_output_dir(exe_id, node_work_dir)
            job_dirs = [job_dir, input_dir, output_dir]
            for target_dir in job_dirs:
                self._create_job_dir(exe_id, target_dir)

            job_interface = job_exe.get_job_interface()
            job_data = job_exe.job.get_job_data()
            job_environment = job_exe.get_job_environment()
            job_interface.perform_pre_steps(job_data, job_environment, exe_id)
            command_args = job_interface.fully_populate_command_argument(job_data, job_environment, exe_id)

            # This shouldn't be necessary once we have user namespaces in docker
            self._chmod_job_dir(file_system.get_job_exe_output_data_dir(exe_id))

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

            logger.info('Executing job: %i -> %s', exe_id, ' '.join(command_args))
            JobExecution.objects.pre_steps_command_arguments(exe_id, command_args)
        except Exception as e:
            logger.exception('Job Execution %i: Error performing pre-job steps', exe_id)

            exit_code = -1
            if isinstance(e, DatabaseError):
                exit_code = DB_EXIT_CODE
            elif isinstance(e, NfsError):
                exit_code = NFS_EXIT_CODE
            elif isinstance(e, IOError):
                exit_code = IO_EXIT_CODE
            sys.exit(exit_code)
        logger.info('Command completed: scale_pre_steps')

    def _create_job_dir(self, exe_id, target_dir):
        '''Creates the given work directory for an execution.

        :param exe_id: The unique identifier of the job execution.
        :type exe_id: int
        :param target_dir: The path of the directory to create.
        :type target_dir: str
        '''
        if not os.path.exists(target_dir):
            logger.info('Job Execution %i: Creating %s', exe_id, target_dir)
            os.makedirs(target_dir, mode=0777)

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
