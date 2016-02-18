"""Defines the abstract base class for all job execution tasks"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod


class Task(object):
    """Abstract base class for a job execution task
    """

    __metaclass__ = ABCMeta

    def __init__(self, task_id, job_exe):
        """Constructor

        :param task_id: The unique ID of the task
        :type task_id: str
        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, job_type, and
            job_type_rev models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        self._task_id = task_id

        # Keep job execution values that should not change over time
        self._job_exe_id = job_exe.id
        self._cpus = job_exe.cpus_scheduled
        self._mem = job_exe.mem_scheduled
        self._disk_in = job_exe.disk_in_scheduled
        self._disk_out = job_exe.disk_out_scheduled
        self._disk_total = job_exe.disk_total_scheduled

    @property
    def id(self):
        """Returns the unique ID of the task

        :returns: The task ID
        :rtype: str
        """

        return self._task_id

    @abstractmethod
    def get_resources(self):
        """Returns the resources that are required/have been scheduled for this task

        :returns: The scheduled resources for this task
        :rtype: :class:`job.resources.NodeResources`
        """

        raise NotImplementedError()
