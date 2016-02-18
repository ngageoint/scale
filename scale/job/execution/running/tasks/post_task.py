"""Defines the class for a job execution post-task"""
from __future__ import unicode_literals

from job.execution.running.tasks.base_task import Task
from job.resources import NodeResources


class PostTask(Task):
    """Represents a job execution post-task
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(PostTask, self).__init__('%i_post' % job_exe.id, job_exe)

    def get_resources(self):
        """See :meth:`job.execution.tasks.Task.get_resources`
        """

        # Post task does not require any local disk space
        return NodeResources(cpus=self._cpus, mem=self._mem)
