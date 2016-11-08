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

    def __init__(self, agent_id):
        """Constructor

        :param agent_id: The agent ID
        :type agent_id: string
        """

        task_id = 'scale_cleanup_%s_%d' % (agent_id, COUNTER.get_next())
        super(CleanupTask, self).__init__(task_id, 'Scale Cleanup', agent_id)

    def get_resources(self):
        """See :meth:`job.execution.running.tasks.base_task.Task.get_resources`
        """

        return NodeResources(cpus=0.1, mem=32)
