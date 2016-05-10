"""Defines methods for cleaning up job executions"""
from __future__ import unicode_literals

import logging

from django.utils.timezone import now

from job.execution.job_exe_cleaner import NormalJobExecutionCleaner
from job.models import JobExecution
from util.retry import retry_database_query


logger = logging.getLogger(__name__)


# JobExecutionCleaner objects registered for specific job type names
# Other apps can register JobExecutionCleaners in their .ready() method
# {Job Type Name: JobExecutionCleaner}
REGISTERED_CLEANERS = {}

DEFAULT_CLEANER = NormalJobExecutionCleaner()


def cleanup_job_exe(job_exe_id):
    """Cleans up a job execution

    :param job_exe_id: The job execution ID
    :type job_exe_id: int
    """

    logger.info('Cleaning up job execution %s', str(job_exe_id))

    job_exe = _get_job_exe(job_exe_id)
    job_type_name = job_exe.job.job_type.name

    # Run appropriate cleaner for job type
    if job_type_name in REGISTERED_CLEANERS:
        cleaner = REGISTERED_CLEANERS[job_type_name]
    else:
        cleaner = DEFAULT_CLEANER
    cleaner.cleanup_job_execution(job_exe)

    _complete_cleanup(job_exe_id)
    logger.info('Successfully cleaned up job execution %s', str(job_exe_id))


@retry_database_query
def _complete_cleanup(job_exe_id):
    """Mark the cleanup as completed

    :param job_exe_id: The job execution ID
    :type job_exe_id: int
    """

    JobExecution.objects.cleanup_completed(job_exe_id, now())


@retry_database_query
def _get_job_exe(job_exe_id):
    """Returns the job execution to be cleaned with its related job and job type models

    :param job_exe_id: The job execution ID
    :type job_exe_id: int
    :returns: The job execution model
    :rtype: :class:`job.models.JobExecution`
    """

    return JobExecution.objects.get_job_exe_with_job_and_job_type(job_exe_id)
