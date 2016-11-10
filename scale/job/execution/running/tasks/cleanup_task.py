"""Defines the class for a cleanup task"""
from __future__ import unicode_literals

import threading

from job.execution.running.tasks.base_task import Task
from job.resources import NodeResources


class AtomicCounter(object):
    """Represents an atomic counter
    """

    def __init__(self):
        """Constructor
        """

        self._counter = 0
        self._lock = threading.Lock()

    def get_next(self):
        """Returns the next integer

        :returns: The next integer
        :rtype: int
        """

        with self._lock:
            self._counter += 1
            return self._counter


COUNTER = AtomicCounter()


class CleanupTask(Task):
    """Represents a task that cleans up after job executions. This class is thread-safe.
    """

    def __init__(self, agent_id, job_exes):
        """Constructor

        :param agent_id: The agent ID
        :type agent_id: string
        :param job_exes: The list of job executions to clean up
        :type job_exes: [:class:`job.execution.running.job_exe.RunningJobExecution`]
        """

        task_id = 'scale_cleanup_%s_%d' % (agent_id, COUNTER.get_next())
        super(CleanupTask, self).__init__(task_id, 'Scale Cleanup', agent_id)

        self._job_exes = job_exes
        self._is_initial_cleanup = not self._job_exes  # This is an initial clean up if job_exes is empty

        self._uses_docker = False
        self._docker_image = None
        self._docker_params = []
        self._is_docker_privileged = False
        # TODO: set up command
        self._command = ''
        self._command_arguments = ''

    @property
    def is_initial_cleanup(self):
        """Indicates whether this is an initial clean up job (True) or not (False)

        :returns: Whether this is an initial clean up job
        :rtype: bool
        """

        with self._lock:
            return self._is_initial_cleanup

    @property
    def job_exes(self):
        """Returns the list of job executions to clean up

        :returns: The list of job executions to clean up
        :rtype: [:class:`job.execution.running.job_exe.RunningJobExecution`]
        """

        with self._lock:
            return self._job_exes

    def get_resources(self):
        """See :meth:`job.execution.running.tasks.base_task.Task.get_resources`
        """

        return NodeResources(cpus=0.1, mem=32)
