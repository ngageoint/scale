"""Defines the class for a job execution pre-task"""
from __future__ import unicode_literals

from job.execution.running.tasks.base_task import Task
from job.resources import NodeResources


class PreTask(Task):
    """Represents a job execution pre-task
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(PreTask, self).__init__('%i_pre' % job_exe.id, job_exe)

    def get_resources(self):
        """See :meth:`job.execution.running.tasks.base_task.Task.get_resources`
        """

        return NodeResources(cpus=self._cpus, mem=self._mem, disk=self._disk_total)
