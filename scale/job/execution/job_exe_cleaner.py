'''Defines the abstract base class used for cleaning up job executions'''
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod
import logging
import os

from job.execution.file_system import get_job_exe_input_data_dir, get_job_exe_input_work_dir, \
    get_job_exe_output_data_dir, get_job_exe_output_work_dir, \
    delete_normal_job_exe_dir_tree
from job.execution.metrics import save_job_exe_metrics
from storage.models import ScaleFile, Workspace


logger = logging.getLogger(__name__)


class JobExecutionCleaner(object):
    '''Abstract class for a cleaner that cleans up after a job execution
    '''

    __metaclass__ = ABCMeta

    @abstractmethod
    def cleanup_job_execution(self, job_exe):
        '''Cleans up the given job execution on the node on which it previously ran. The job_exe model will have its
        related job and job_type fields populated.

        :param job_exe: The job execution model with related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        '''

        pass


class NormalJobExecutionCleaner(JobExecutionCleaner):
    '''Cleaner for the execution of normal jobs (non-system jobs with pre and post tasks)
    '''

    def cleanup_job_execution(self, job_exe):
        '''See :meth:`job.execution.job_exe_cleaner.JobExecutionCleaner.cleanup_job_execution`
        '''

        logger.info('Cleaning up a non-system job')

        download_dir = get_job_exe_input_data_dir(job_exe.id)
        download_work_dir = get_job_exe_input_work_dir(job_exe.id)
        upload_dir = get_job_exe_output_data_dir(job_exe.id)
        upload_work_dir = get_job_exe_output_work_dir(job_exe.id)

        logger.info('Cleaning up download directory')
        ScaleFile.objects.cleanup_download_dir(download_dir, download_work_dir)

        logger.info('Cleaning up upload directories')
        workspace_ids = job_exe.job.get_job_data().get_output_workspace_ids()
        for workspace in Workspace.objects.filter(id__in=workspace_ids):
            logger.info('Cleaning up upload directory for workspace %s', workspace.name)
            ScaleFile.objects.cleanup_upload_dir(upload_dir, upload_work_dir, workspace)

        move_work_dir = os.path.join(upload_work_dir, 'move_source_file_in_workspace')
        if os.path.exists(move_work_dir):
            logger.info('Cleaning up work directory for moving parsed source files')
            ScaleFile.objects.cleanup_move_dir(move_work_dir)
            logger.info('Deleting %s', move_work_dir)
            os.rmdir(move_work_dir)

        delete_normal_job_exe_dir_tree(job_exe.id)

        save_job_exe_metrics(job_exe)
