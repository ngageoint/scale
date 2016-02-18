"""Defines the class for a job execution job task"""
from __future__ import unicode_literals

from job.execution.running.tasks.base_task import Task
from job.resources import NodeResources


class JobTask(Task):
    """Represents a job execution job task (runs the actual job/algorithm)
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(JobTask, self).__init__('%i_job' % job_exe.id, job_exe)

    def get_resources(self):
        """See :meth:`job.execution.tasks.Task.get_resources`
        """

        # Input files have already been written, only disk space for output files is required
        return NodeResources(cpus=self._cpus, mem=self._mem, disk=self._disk_out)
