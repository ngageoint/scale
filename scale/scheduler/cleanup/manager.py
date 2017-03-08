"""Defines the class that manages all scheduler cleanup tasks"""
from __future__ import unicode_literals

import threading


class CleanupManager(object):
    """This class manages all of the scheduler cleanup. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._lock = threading.Lock()
        self._nodes = {}  # {Node ID: Node}

    def add_job_execution(self, job_exe):
        """Adds a job execution that needs to be cleaned up

        :param job_exe: The job execution to add
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        with self._lock:
            self._nodes[job_exe.node_id].add_job_execution(job_exe)

    def update_nodes(self, nodes):
        """Updates the manager with the latest copies of the nodes

        :param nodes: The list of updated nodes
        :type nodes: [:class:`scheduler.node.node_class.Node`]
        """

        with self._lock:
            for node in nodes:
                if node.id not in self._nodes:
                    self._nodes[node.id] = node


cleanup_mgr = CleanupManager()
