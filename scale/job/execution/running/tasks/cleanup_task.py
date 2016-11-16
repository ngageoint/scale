"""Defines the class for a cleanup task"""
from __future__ import unicode_literals

import threading

from job.execution.running.tasks.base_task import Task
from job.resources import NodeResources


CLEANUP_TASK_ID_PREFIX = 'scale_cleanup'


class AtomicCounter(object):
    """Represents an atomic counter
    """

    def __init__(self):
        """Constructor
        """

        self._counter = 0
        self._lock = threading.Lock()
        # TODO: remove
        from util.lock import DebugLock
        self._lock = DebugLock('AtomicCounter')

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

        task_id = '%s_%s_%d' % (CLEANUP_TASK_ID_PREFIX, agent_id, COUNTER.get_next())
        super(CleanupTask, self).__init__(task_id, 'Scale Cleanup', agent_id)

        self._job_exes = job_exes
        self._is_initial_cleanup = not self._job_exes  # This is an initial clean up if job_exes is empty

        self._uses_docker = False
        self._docker_image = None
        self._docker_params = []
        self._is_docker_privileged = False

        # Command deletes all non-running containers
        delete_containers_cmd = 'docker rm $(docker ps -f status=exited -f status=created -q)'

        # Command loops over specified volumes to delete and deletes it if it exists
        volume_exists_check = '"`docker volume ls -q | grep "$vol"`" == "$vol"'
        volume_delete_cmd = 'docker volume rm $vol'
        echo_cmd = 'echo "$vol not found"'
        delete_volumes_cmd = 'for vol in `%s`; do if [[ %s ]]; then %s; else %s; fi; done'

        if self._is_initial_cleanup:
            # TODO: once we upgrade to a later version of Docker (1.12+), we can delete volumes based on their name
            # starting with "scale_" (and also dangling)
            # Initial clean up deletes all dangling Docker volumes
            volume_list_cmd = 'docker volume ls -f dangling=true -q'
        else:
            # Deletes all volumes for the given job executions
            docker_volumes = []
            for job_exe in self._job_exes:
                docker_volumes.extend(job_exe.docker_volumes)
            volume_list_cmd = 'echo %s' % ' '.join(docker_volumes)
        delete_volumes_cmd = delete_volumes_cmd % (volume_list_cmd, volume_exists_check, volume_delete_cmd, echo_cmd)

        # Command deletes all non-running containers and then deletes appropriate Docker volumes
        self._command = '%s; %s' % (delete_containers_cmd, delete_volumes_cmd)

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
