"""Defines the class that manages all scheduler cleanup tasks"""
from __future__ import unicode_literals

import threading

from scheduler.cleanup.node import NodeCleanup


class CleanupManager(object):
    """This class manages all of the scheduler cleanup tasks. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._agent_ids = {}  # {Agent ID: Node ID}
        self._lock = threading.Lock()
        self._nodes = {}  # {Node ID: NodeCleanup}

    # TODO: call this in scheduling thread
    def get_next_tasks(self):
        """Returns the next cleanup tasks to schedule

        :returns: A list of the next cleanup tasks to schedule
        :rtype: [:class:`job.execution.running.tasks.cleanup_task.CleanupTask`]
        """

        tasks = []
        with self._lock:
            for node in self._nodes.values():
                task = node.get_next_task()
                if task:
                    tasks.append(task)
        return tasks

    # TODO: call this when receiving task update from Mesos
    def handle_task_update(self, task_update):
        """Handles the given task update for a cleanup task

        :param task_update: The task update
        :type task_update: :class:`job.execution.running.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if task_update.agent_id not in self._agent_ids:
                return
            node_id = self._agent_ids[task_update.agent_id]
            self._nodes[node_id].handle_task_update(task_update)

    # TODO: call this at start of scheduling thread
    def update_nodes(self, nodes):
        """Updates the manager with the latest copies of the nodes

        :param nodes: The list of updated nodes
        :type nodes: [:class:`scheduler.node.node_class.Node`]
        """

        with self._lock:
            self._agent_ids = {}

            for node in nodes:
                if node.id not in self._nodes:
                    # New node
                    node_cleanup = NodeCleanup(node)
                    self._nodes[node.id] = node_cleanup

                # Re-create agent ID mapping (agent IDs can change over time)
                self._agent_ids[node.agent_id] = node.id

    # TODO: take in finished job exes and track stuff to clean up
