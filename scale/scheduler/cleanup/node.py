"""Defines the class that handles a node's cleanup"""
from __future__ import unicode_literals

import logging

from job.execution.tasks.cleanup_task import CleanupTask
from scheduler.manager import scheduler_mgr


JOB_EXES_WARNING_THRESHOLD = 100
MAX_JOB_EXES_PER_CLEANUP = 25


logger = logging.getLogger(__name__)


class NodeCleanup(object):
    """This class manages all of the cleanup for a node."""

    def __init__(self):
        """Constructor
        """

        self._job_exes = {}  # {Job Exe ID: RunningJobExecution}

    def add_job_execution(self, job_exe):
        """Adds a job execution that needs to be cleaned up

        :param job_exe: The job execution to add
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        self._job_exes[job_exe.id] = job_exe

    def delete_job_executions(self, job_exes):
        """Deletes the given job executions since they have been cleaned up

        :param job_exes: The job executions to delete
        :type job_exes: [:class:`job.execution.job_exe.RunningJobExecution`]
        """

        for job_exe in job_exes:
            if job_exe.id in self._job_exes:
                del self._job_exes[job_exe.id]

    def create_next_task(self, agent_id, hostname, is_initial_cleanup_completed):
        """Creates and returns the next cleanup task that needs to be run, possibly None

        :param agent_id: The node's agent ID
        :type agent_id: string
        :param hostname: The node's hostname
        :type hostname: string
        :param is_initial_cleanup_completed: Indicates if node's initial cleanup is completed
        :type is_initial_cleanup_completed: bool
        :returns: The next cleanup task, possibly None
        :rtype: :class:`job.tasks.base_task.Task`
        """

        total_job_exes = self._job_exes.values()
        count = len(total_job_exes)
        if count > JOB_EXES_WARNING_THRESHOLD:
            logger.warning('Node %s has %d job executions waiting to be cleaned up', hostname, count)

        cleanup_job_exes = []
        if is_initial_cleanup_completed:
            if count == 0:
                # No job executions to clean, so no task
                return None
            for job_exe in total_job_exes:
                cleanup_job_exes.append(job_exe)
                if len(cleanup_job_exes) >= MAX_JOB_EXES_PER_CLEANUP:
                    break

        return CleanupTask(scheduler_mgr.framework_id, agent_id, cleanup_job_exes)

    def get_num_job_exes(self):
        """Returns the number of job executions waiting to be cleaned up

        :returns: The number of job executions waiting to be cleaned up
        :rtype: int
        """

        return len(self._job_exes.values())
