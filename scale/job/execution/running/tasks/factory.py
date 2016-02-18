"""Defines the factory class for creating job execution tasks"""
from __future__ import unicode_literals

from job.execution.running.tasks.job_task import JobTask
from job.execution.running.tasks.post_task import PostTask
from job.execution.running.tasks.pre_task import PreTask


class TaskFactory(object):
    """A factory that produces the job execution tasks. This class can be overridden to produce custom task
    implementations.
    """

    def create_job_task(self, job_exe):
        """Creates and returns a job-task for the given job execution

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
            models populated
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The job execution job-task
        :rtype: :class:`job.execution.tasks.JobTask`
        """

        return JobTask(job_exe)

    def create_post_task(self, job_exe):
        """Creates and returns a post-task for the given job execution

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
            models populated
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The job execution post-task
        :rtype: :class:`job.execution.tasks.PostTask`
        """

        return PostTask(job_exe)

    def create_pre_task(self, job_exe):
        """Creates and returns a pre-task for the given job execution

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
            models populated
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The job execution pre-task
        :rtype: :class:`job.execution.tasks.PreTask`
        """

        return PreTask(job_exe)
