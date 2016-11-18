"""Defines the abstract base class for all tasks"""
from __future__ import unicode_literals

import datetime
import threading
from abc import ABCMeta, abstractmethod

from job.execution.running.tasks.update import TaskStatusUpdate
from util.exceptions import ScaleLogicBug


# Amount of time for the last status update to go stale and require reconciliation
RECONCILIATION_THRESHOLD = datetime.timedelta(minutes=10)


class Task(object):
    """Abstract base class for a task
    """

    __metaclass__ = ABCMeta

    def __init__(self, task_id, task_name, agent_id):
        """Constructor

        :param task_id: The unique ID of the task
        :type task_id: string
        :param task_name: The name of the task
        :type task_name: string
        :param agent_id: The ID of the agent on which the task is scheduled
        :type agent_id: string
        """

        # Basic attributes
        self._task_id = task_id
        self._task_name = task_name
        self._agent_id = agent_id
        self._lock = threading.Lock()
        self._has_been_scheduled = False
        self._scheduled = None
        self._last_status_update = None
        self._has_started = False
        self._started = None
        self._has_ended = False
        self._ended = None
        self._exit_code = None

        # These values will vary by different task subclasses
        self._uses_docker = False
        self._docker_image = None
        self._docker_params = []
        self._is_docker_privileged = False
        self._command = 'echo "Hello Scale"'
        self._command_arguments = None

    @property
    def agent_id(self):
        """Returns the ID of the agent that the task is running on

        :returns: The agent ID
        :rtype: string
        """

        return self._agent_id

    @property
    def command(self):
        """Returns the command to execute for the task

        :returns: The command to execute
        :rtype: string
        """

        return self._command

    @property
    def command_arguments(self):
        """Returns the command to execute for the task

        :returns: The command to execute
        :rtype: string
        """

        return self._command_arguments

    @property
    def docker_image(self):
        """Returns the name of the Docker image to run for this task, possibly None

        :returns: The Docker image name
        :rtype: string
        """

        return self._docker_image

    @property
    def docker_params(self):
        """Returns the Docker parameters used to run this task

        :returns: The Docker parameters
        :rtype: [:class:`job.configuration.configuration.job_configuration.DockerParam`]
        """

        return self._docker_params

    @property
    def has_been_scheduled(self):
        """Indicates whether this task has been scheduled

        :returns: True if this task has been scheduled, False otherwise
        :rtype: bool
        """

        return self._has_been_scheduled

    @property
    def has_ended(self):
        """Indicates whether this task has ended

        :returns: True if this task has ended, False otherwise
        :rtype: bool
        """

        return self._has_ended

    @property
    def has_started(self):
        """Indicates whether this task has started

        :returns: True if this task has started, False otherwise
        :rtype: bool
        """

        return self._has_started

    @property
    def id(self):
        """Returns the unique ID of the task

        :returns: The task ID
        :rtype: string
        """

        return self._task_id

    @property
    def is_docker_privileged(self):
        """Indicates whether this task's Docker container should be run in privileged mode

        :returns: True if the container should be run in privileged mode, False otherwise
        :rtype: bool
        """

        return self._is_docker_privileged

    @property
    def name(self):
        """Returns the name of the task

        :returns: The task name
        :rtype: string
        """

        return self._task_name

    @property
    def started(self):
        """When this task started, possibly None

        :returns: When this task started
        :rtype: :class:`datetime.datetime`
        """

        return self._started

    @property
    def uses_docker(self):
        """Indicates whether this task uses Docker or not

        :returns: True if this task uses Docker, False otherwise
        :rtype: bool
        """

        return self._uses_docker

    @abstractmethod
    def get_resources(self):
        """Returns the resources that are required/have been scheduled for this task

        :returns: The scheduled resources for this task
        :rtype: :class:`job.resources.NodeResources`
        """

        raise NotImplementedError()

    def needs_reconciliation(self, when):
        """Indicates whether this task needs to be reconciled due to its latest status update being stale

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: Whether this task needs to be reconciled
        :rtype: bool
        """

        with self._lock:
            if not self._last_status_update:
                return False  # Has not been scheduled yet
            time_since_last_update = when - self._last_status_update
            return time_since_last_update > RECONCILIATION_THRESHOLD

    def schedule(self, when):
        """Marks this task as having been scheduled

        :param when: The time that the task was scheduled
        :type when: :class:`datetime.datetime`

        :raises :class:`util.exceptions.ScaleLogicBug`: If the task has already started
        """

        with self._lock:
            if self._has_started:
                raise ScaleLogicBug('Trying to schedule a task that has already started')

            self._has_been_scheduled = True
            self._scheduled = when
            self._last_status_update = when

    def update(self, task_update):
        """Handles the given task update

        :param task_update: The task update
        :type task_update: :class:`job.execution.running.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if self._task_id != task_update.task_id:
                return

            self._last_status_update = task_update.when

            # Support duplicate calls as task updates may repeat
            if task_update.status == TaskStatusUpdate.RUNNING:
                # Mark task as having started if it isn't already
                if not self._has_started:
                    self._has_started = True
                    self._started = task_update.when
            elif task_update.status == TaskStatusUpdate.LOST:
                # Reset task to initial state (unless already ended)
                if not self._has_ended:
                    self._has_been_scheduled = False
                    self._scheduled = None
                    self._last_status_update = None
                    self._has_started = False
                    self._started = None
            elif task_update.status in TaskStatusUpdate.TERMINAL_STATUSES:
                # Mark task as having ended if it isn't already
                if not self._has_ended:
                    self._has_ended = True
                    self._ended = task_update.when
                    self._exit_code = task_update.exit_code
