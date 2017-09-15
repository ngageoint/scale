"""Defines the class that managers the currently running tasks"""
from __future__ import unicode_literals

import logging
import threading

from job.tasks.node_task import NodeTask
from job.tasks.update import TaskStatusUpdate
from scheduler.tasks.system_task import SystemTask


logger = logging.getLogger(__name__)


class TaskManager(object):
    """This class manages all currently running tasks. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._tasks = {}  # {Task ID: Task}
        self._lock = threading.Lock()

    def generate_status_json(self, nodes_list):
        """Generates the portion of the status JSON that describes the currently running node and system tasks

        :param nodes_list: The list of nodes within the status JSON
        :type nodes_list: list
        """

        node_tasks = {}  # {Agent ID: [task]}
        system_tasks = {}  # {Agent ID: [task]}

        with self._lock:
            for task in self._tasks.values():
                if isinstance(task, NodeTask):
                    if task.agent_id in node_tasks:
                        node_tasks[task.agent_id].append(task)
                    else:
                        node_tasks[task.agent_id] = [task]
                elif isinstance(task, SystemTask):
                    if task.agent_id in system_tasks:
                        system_tasks[task.agent_id].append(task)
                    else:
                        system_tasks[task.agent_id] = [task]

        for node_dict in nodes_list:
            agent_id = node_dict['agent_id']
            if agent_id in node_tasks:
                task_dicts = {}  # {task type: task dict}
                for task in node_tasks[agent_id]:
                    if task.task_type in task_dicts:
                        task_dicts[task.task_type]['count'] += 1
                    else:
                        task_dicts[task.task_type] = {'type': task.task_type, 'title': task.title,
                                                      'description': task.description, 'count': 1}
                node_dict['node_tasks'] = task_dicts.values()
            if agent_id in system_tasks:
                task_dicts = {}  # {task type: task dict}
                for task in system_tasks[agent_id]:
                    if task.task_type in task_dicts:
                        task_dicts[task.task_type]['count'] += 1
                    else:
                        task_dicts[task.task_type] = {'type': task.task_type, 'title': task.title,
                                                      'description': task.description, 'count': 1}
                node_dict['system_tasks'] = task_dicts.values()

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
