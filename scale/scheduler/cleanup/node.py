"""Defines the class that handles a node's cleanup"""
from __future__ import unicode_literals

import threading

from job.execution.running.tasks.cleanup_task import CleanupTask


class NodeCleanup(object):
    """This class manages all of the cleanup for a node. This class is thread-safe."""

    def __init__(self, node):
        """Constructor

        :param node: The node
        :type node: :class:`scheduler.node.node_class.Node`
        """

        self._current_task = None
        self._lock = threading.Lock()
        self._node = node

    def get_next_task(self):
        """Returns the next cleanup task to schedule, possibly None

        :returns: The next cleanup task to schedule, possibly None
        :rtype: :class:`job.execution.running.tasks.cleanup_task.CleanupTask`
        """

        with self._lock:
            self._create_next_task()  # This is needed to check for node agent ID change

            # No task returned if node is paused, no task to schedule, or task is already scheduled
            if self._node.is_paused or self._current_task is None or self._current_task.has_been_scheduled:
                return None

            return self._current_task

    def _create_next_task(self):
        """Creates the next cleanup task that needs to be run for this node
        """

        with self._lock:
            # If we have a current task, check that node's agent ID has not changed
            if self._current_task and self._current_task.agent_id != self._node.agent_id:
                self._current_task = None

            if self._current_task:
                return

            # TODO: implement passing the cleanup details into the task that it needs
            self._current_task = CleanupTask(self._node.agent_id)
