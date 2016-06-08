"""Defines the abstract base class used for cleaning up job executions"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod
import logging


logger = logging.getLogger(__name__)


class JobExecutionCleaner(object):
    """Abstract class for a cleaner that cleans up after a job execution
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def cleanup_job_execution(self, job_exe):
        """Cleans up the given job execution on the node on which it previously ran. The job_exe model will have its
        related job and job_type fields populated.

        :param job_exe: The job execution model with related job and job_type fields
        :type job_exe: :class:`job.models.JobExecution`
        """

        pass


class NormalJobExecutionCleaner(JobExecutionCleaner):
    """Cleaner for the execution of normal jobs (non-system jobs with pre and post tasks)
    """

    def cleanup_job_execution(self, job_exe):
        """See :meth:`job.execution.job_exe_cleaner.JobExecutionCleaner.cleanup_job_execution`
        """

        logger.info('Cleaning up a non-system job')

        # TODO: the normal cleanup on the host is now obsolete with moving everything into Docker volumes, need to
        # investigate this to see if doing job execution clean up still makes sense or if this should be removed

        # TODO: commenting this out since it doesn't currently work, need to grab Docker container IDs to work
        # save_job_exe_metrics(job_exe)
