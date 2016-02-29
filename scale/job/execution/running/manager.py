"""Defines the class that managers the currently running job executions"""
from __future__ import unicode_literals

import threading


class RunningJobExecutionManager(object):
    """This class manages all currently running job execution. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._job_exes = {}
        self._lock = threading.Lock()

    def add_job_exes(self, job_exes):
        """Adds new running job executions to the manager

        :param job_exes: A list of the running job executions to add
        :type job_exes: [:class:`job.execution.running.job_exe.RunningJobExecution`]
        """

        with self._lock:
            for job_exe in job_exes:
                self._job_exes[job_exe.id] = job_exe

    def get_all_job_exes(self):
        """Returns all running job executions

        :returns: A list of running job executions
        :rtype: [:class:`job.execution.running.job_exe.RunningJobExecution`]
        """

        result = []
        with self._lock:
            for job_exe_id in self._job_exes:
                result.append(self._job_exes[job_exe_id])
        return result

    def get_job_exe(self, job_exe_id):
        """Returns the running job execution with the given ID, or None if the job execution does not exist

        :param job_exe_id: The ID of the job execution to return
        :type job_exe_id: int
        :returns: The running job execution with the given ID, possibly None
        :rtype: :class:`job.execution.running.job_exe.RunningJobExecution`
        """

        with self._lock:
            try:
                return self._job_exes[job_exe_id]
            except KeyError:
                return None

    def get_job_exes_on_node(self, node_id):
        """Returns all running job executions that are on the given node

        :param node_id: The ID of the node
        :type node_id: int
        :returns: A list of running job executions
        :rtype: [:class:`job.execution.running.job_exe.RunningJobExecution`]
        """

        result = []
        with self._lock:
            for job_exe_id in self._job_exes:
                job_exe = self._job_exes[job_exe_id]
                if job_exe.node_id == node_id:
                    result.append(self._job_exes[job_exe_id])
        return result

    def get_ready_job_exes(self):
        """Returns all running job executions that are ready to execute their next task

        :returns: A list of running job executions
        :rtype: [:class:`job.execution.running.job_exe.RunningJobExecution`]
        """

        result = []
        with self._lock:
            for job_exe_id in self._job_exes:
                job_exe = self._job_exes[job_exe_id]
                if job_exe.is_next_task_ready():
                    result.append(self._job_exes[job_exe_id])
        return result

    def remove_job_exe(self, job_exe_id):
        """Removes the running job execution with the given ID

        :param job_exe_id: The ID of the job execution to remove
        :type job_exe_id: int
        """

        with self._lock:
            try:
                del self._job_exes[job_exe_id]
            except KeyError:
                pass
