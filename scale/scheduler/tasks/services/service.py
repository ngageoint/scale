"""Defines the abstract base class for all system services"""
from __future__ import unicode_literals

import logging
from abc import ABCMeta, abstractmethod

from job.tasks.update import TaskStatusUpdate


logger = logging.getLogger(__name__)


class Service(object):
    """Abstract base class for a system service"""

    __metaclass__ = ABCMeta

    def __init__(self):
        """Constructor
        """

        # Override these in sub-classes
        self._name = 'base'
        self._title = 'Base'
        self._description = None

        self._tasks = {}  # {Task ID: Task}

    def generate_status_json(self):
        """Generates the portion of the status JSON that describes this service

        :returns: The dict containing the status for this service
        :rtype: dict
        """

        actual_count = self.get_actual_task_count()
        desired_count = self.get_desired_task_count()

        return {'name': self._name, 'title': self._title, 'description': self._description,
                'actual_count': actual_count, 'desired_count': desired_count}

    def get_actual_task_count(self):
        """Returns the actual number of tasks currently running for this service

        :returns: The actual number of tasks
        :rtype: int
        """

        return len(self._tasks.values())

    @abstractmethod
    def get_desired_task_count(self):
        """Returns the number of tasks that are desired for this service

        :returns: The desired number of tasks
        :rtype: int
        """

    def get_tasks_to_kill(self):
        """Returns a list of service tasks that need to be killed

        :returns: The list of service tasks to kill
        :rtype: list
        """

        tasks_to_kill = []
        num_tasks_to_kill = max(self.get_actual_task_count() - self.get_desired_task_count(), 0)
        if num_tasks_to_kill > 0:
            logger.info('%s service is over-scheduled, killing %d task(s)', self._title, num_tasks_to_kill)
            for task in self._tasks.values()[:num_tasks_to_kill]:
                tasks_to_kill.append(task)
        return tasks_to_kill

    def get_tasks_to_schedule(self):
        """Returns a list of service tasks that need to be scheduled

        :returns: The list of service tasks to schedule
        :rtype: list
        """

        tasks = []

        num_tasks_to_create = max(self.get_desired_task_count() - self.get_actual_task_count(), 0)
        if num_tasks_to_create > 0:
            logger.info('%s service is under-scheduled, creating %d task(s)', self._title, num_tasks_to_create)
            for _ in range(num_tasks_to_create):
                new_task = self._create_service_task()
                self._tasks[new_task.id] = new_task

        for task in self._tasks.values():
            if not task.has_been_launched:
                tasks.append(task)

        return tasks

    def handle_task_update(self, task_update):
        """Handles the given service task update

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        if task_update.task_id not in self._tasks:
            return

        task = self._tasks[task_update.task_id]

        if task_update.status == TaskStatusUpdate.FINISHED:
            logger.info('%s service: task completed', self._title)
        elif task_update.status == TaskStatusUpdate.FAILED:
            logger.warning('%s service: task failed', self._title)
        elif task_update.status == TaskStatusUpdate.KILLED:
            logger.info('%s service: task killed', self._title)
        elif task_update.status == TaskStatusUpdate.LOST:
            logger.warning('%s service: task lost', self._title)

        if task.has_ended:
            del self._tasks[task.id]

    @abstractmethod
    def _create_service_task(self):
        """Creates a new service task

        :returns: The new service task
        :rtype: :class:`scheduler.tasks.system_task.SystemTask`
        """
