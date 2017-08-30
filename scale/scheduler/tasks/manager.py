"""Defines the class that manages system tasks"""
from __future__ import unicode_literals

import logging
import threading


logger = logging.getLogger(__name__)


class SystemTaskManager(object):
    """This class manages all Scale system tasks. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._lock = threading.Lock()

    def get_tasks_to_kill(self):
        """Returns a list of system tasks that need to be killed as soon as possible

        :returns: The list of system tasks to kill
        :rtype: list
        """

        # TODO: implement
        return []

    def get_tasks_to_schedule(self):
        """Returns a list of system tasks that need to be scheduled as soon as possible

        :returns: The list of system tasks to schedule
        :rtype: list
        """

        # TODO: implement
        return []

    def handle_task_update(self, task_update):
        """Handles the given task update

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        # TODO: implement
        with self._lock:
            pass


system_task_mgr = SystemTaskManager()
