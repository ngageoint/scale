'''Defines methods for cleaning up job executions'''
from __future__ import unicode_literals

import logging
import os
import shutil

from django.utils.timezone import now

import job.settings as settings
from job.execution.file_system import get_job_exe_dir
from job.execution.job_exe_cleaner import NormalJobExecutionCleaner
from job.models import JobExecution


logger = logging.getLogger(__name__)


# JobExecutionCleaner objects registered for specific job type names
# Other apps can register JobExecutionCleaners in their .ready() method
# {Job Type Name: JobExecutionCleaner}
REGISTERED_CLEANERS = {}

DEFAULT_CLEANER = NormalJobExecutionCleaner()


def cleanup_job_exe(job_exe_id):
    '''Cleans up a job execution

    :param job_exe_id: The job execution ID
    :type job_exe_id: int
    '''

    logger.info('Cleaning up job execution %s', str(job_exe_id))

    node_work_dir = settings.NODE_WORK_DIR
    job_exe_dir = get_job_exe_dir(job_exe_id, node_work_dir)
    job_exe = JobExecution.objects.get_job_exe_with_job_and_job_type(job_exe_id)
    job_type_name = job_exe.job.job_type.name

    # Run appropriate cleaner for job type
    if job_type_name in REGISTERED_CLEANERS:
        cleaner = REGISTERED_CLEANERS[job_type_name]
    else:
        cleaner = DEFAULT_CLEANER
    cleaner.cleanup_job_execution(job_exe)

    # Delete job execution directory
    if os.path.exists(job_exe_dir):
        logger.info('Deleting %s', job_exe_dir)
        shutil.rmtree(job_exe_dir)

    JobExecution.objects.cleanup_completed(job_exe_id, now())
    logger.info('Successfully cleaned up job execution %s', str(job_exe_id))
