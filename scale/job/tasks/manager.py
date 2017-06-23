"""Defines the class that managers the currently running tasks"""
from __future__ import unicode_literals

import logging
import threading

from job.tasks.update import TaskStatusUpdate


logger = logging.getLogger(__name__)


class TaskManager(object):
    """This class manages all currently running tasks. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._tasks = {}  # {Task ID: Task}
        self._lock = threading.Lock()

    def get_all_tasks(self):
        """Returns all of current tasks

        :returns: The list of all current tasks
        :rtype: [:class:`job.tasks.base_task.Task`]
        """

        with self._lock:
            return list(self._tasks.values())

    def get_task(self, task_id):
        """Returns the task with the given ID, possibly None

        :param task_id: The task ID
        :type task_id: int
        :returns: The task with the given ID
        :rtype: :class:`job.tasks.base_task.Task`
        """

        with self._lock:
            return self._tasks[task_id] if task_id in self._tasks else None

    def get_tasks_to_reconcile(self, when):
        """Returns all of the tasks that need to be reconciled

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The list of tasks that require reconciliation
        :rtype: [:class:`job.tasks.base_task.Task`]
        """

        tasks = []
        with self._lock:
            for task in self._tasks.values():
                if task.needs_reconciliation(when):
                    tasks.append(task)
        return tasks

    def get_timeout_tasks(self, when):
        """Returns all of the tasks that have timed out

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The list of tasks that timed out
        :rtype: [:class:`job.tasks.base_task.Task`]
        """

        tasks = []
        with self._lock:
            for task in self._tasks.values():
                if task.check_timeout(when):
                    tasks.append(task)
        return tasks

    def handle_task_update(self, task_update):
        """Handles the given task update

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if task_update.task_id not in self._tasks:
                return
            task = self._tasks[task_update.task_id]
            task.update(task_update)
            if task.has_ended or task_update.status == TaskStatusUpdate.LOST:
                # Task is no longer launched/running so remove it from manager
                del self._tasks[task.id]

    def launch_tasks(self, tasks, when):
        """Adds the new tasks to the manager and marks them as launched

        :param tasks: The tasks to add and launch
        :type tasks: [:class:`job.tasks.base_task.Task`]
        :param when: The time that the tasks were launched
        :type when: :class:`datetime.datetime`
        """

        with self._lock:
            for task in tasks:
                if task.id not in self._tasks:
                    task.launch(when)
                    self._tasks[task.id] = task
                else:
                    logger.error('Attempted to launch a task that has already been launched')


task_mgr = TaskManager()
