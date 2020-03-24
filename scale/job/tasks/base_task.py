"""Defines the abstract base class for all tasks"""
from __future__ import unicode_literals

import datetime
import logging
import threading
from abc import ABCMeta, abstractmethod

from django.conf import settings

from job.tasks.update import TaskStatusUpdate

# Default timeout thresholds for tasks (None means no timeout)
BASE_RUNNING_TIMEOUT_THRESHOLD = datetime.timedelta(hours=1)
BASE_STAGING_TIMEOUT_THRESHOLD = datetime.timedelta(minutes=2)

# Reconciliation thresholds for tasks
RUNNING_RECON_THRESHOLD = datetime.timedelta(minutes=10)
STAGING_RECON_THRESHOLD = datetime.timedelta(seconds=30)


logger = logging.getLogger(__name__)


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
        :param agent_id: The ID of the agent on which the task is launched
        :type agent_id: string
        """

        # Basic attributes
        self._task_id = task_id
        self._task_name = task_name
        self.agent_id = agent_id
        self._container_name = None
        self._lock = threading.Lock()
        self._has_been_launched = False
        self._launched = None
        self._force_recon = False
        self._needs_killed = False
        self._last_status_update = None
        self._has_started = False
        self._started = None
        self._has_timed_out = False
        self._has_ended = False
        self._ended = None
        self.final_status = None
        self._exit_code = None

        # These values will vary by different task subclasses
        self._uses_docker = True
        self._docker_image = None
        self._docker_params = []
        self._is_docker_privileged = False
        self._command = None
        self._command_arguments = None
        self._running_timeout_threshold = BASE_RUNNING_TIMEOUT_THRESHOLD
        self._staging_timeout_threshold = BASE_STAGING_TIMEOUT_THRESHOLD

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
    def container_name(self):
        """Returns the container name for the task, possibly None

        :returns: The container name
        :rtype: string
        """

        return self._container_name

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
        :rtype: :func:`list`
        """

        return self._docker_params

    @property
    def ended(self):
        """When this task ended, possibly None

        :returns: When this task ended
        :rtype: :class:`datetime.datetime`
        """

        return self._ended

    @property
    def exit_code(self):
        """Returns the exit code for this task, possibly None

        :returns: The exit code
        :rtype: int
        """

        return self._exit_code

    @property
    def has_been_launched(self):
        """Indicates whether this task has been launched

        :returns: True if this task has been launched, False otherwise
        :rtype: bool
        """

        return self._has_been_launched

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
    def has_timed_out(self):
        """Indicates whether this task has timed out

        :returns: True if this task has timed out, False otherwise
        :rtype: bool
        """

        return self._has_timed_out

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
    def launched(self):
        """When this task launched, possibly None

        :returns: When this task launched
        :rtype: :class:`datetime.datetime`
        """

        return self._launched

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

    def check_timeout(self, when):
        """Checks this task's progress against the given current time and times out the task if it has exceeded a
        timeout threshold

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: Whether this task has timed out
        :rtype: bool
        """

        with self._lock:
            if not self._has_been_launched or self._has_timed_out or self._has_ended:
                return self._has_timed_out

            if self._has_started:
                # Task has started so check running threshold
                running_time = when - self._started
                timed_out = self._running_timeout_threshold and running_time > self._running_timeout_threshold
            else:
                # Task is still staging so check staging threshold
                staging_time = when - self._launched
                timed_out = self._staging_timeout_threshold and staging_time > self._staging_timeout_threshold
                if timed_out:
                    timeout_in_mins = int(self._staging_timeout_threshold.total_seconds() / 60)
                    logger.error('Task %s failed to start running within %d minutes', self._task_id, timeout_in_mins)

            if timed_out:
                self._has_timed_out = True
                self._needs_killed = True

            return self._has_timed_out

    def force_kill(self):
        """Sets a task setting to force kill messages for this task
        """

        self._needs_killed = True

    def force_reconciliation(self):
        """Sets a task setting to force immediate reconciliation for this task
        """

        self._force_recon = True

    @abstractmethod
    def get_resources(self):
        """Returns the resources that are required/have been scheduled for this task

        :returns: The scheduled resources for this task
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

    def needs_killed(self):
        """Indicates whether this task needs to be killed

        :returns: Whether this task needs to be killed
        :rtype: bool
        """

        with self._lock:
            if not self._last_status_update:
                return False  # Has not been launched yet
            if self._has_ended:
                return False
            return self._needs_killed

    def needs_reconciliation(self, when):
        """Indicates whether this task needs to be reconciled due to its latest status update being stale

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: Whether this task needs to be reconciled
        :rtype: bool
        """

        with self._lock:
            if not self._last_status_update:
                return False  # Has not been launched yet
            if self._force_recon:
                return True
            time_since_last_update = when - self._last_status_update
            if self._has_started:
                return time_since_last_update > RUNNING_RECON_THRESHOLD
            return time_since_last_update > STAGING_RECON_THRESHOLD

    def launch(self, when):
        """Marks this task as having been launched

        :param when: The time that the task was launched
        :type when: :class:`datetime.datetime`
        """

        with self._lock:
            if self._has_been_launched:
                logger.error('Tried to launch a task that has already been launched')
                return

            self._has_been_launched = True
            self._launched = when
            self._last_status_update = when

    def update(self, task_update):
        """Handles the given task update

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if self._task_id != task_update.task_id:
                return

            self._force_recon = False
            self._last_status_update = task_update.timestamp
            if self._has_ended:  # Ended tasks no longer update
                return

            # Support duplicate calls as task updates may repeat
            if task_update.status == TaskStatusUpdate.RUNNING:
                # Mark task as having started if it isn't already
                if not self._has_started:
                    self._has_started = True
                    self._started = task_update.timestamp
                    self._parse_container_name(task_update)
            elif task_update.status == TaskStatusUpdate.LOST:
                # Reset task to initial state before launch
                self._has_been_launched = False
                self._launched = None
                self._last_status_update = None
                self._has_started = False
                self._started = None
            elif task_update.status in TaskStatusUpdate.TERMINAL_STATUSES:
                # Mark task as having ended
                self._has_ended = True
                self._ended = task_update.timestamp
                self.final_status = task_update.status
                self._exit_code = task_update.exit_code

    def _create_scale_image_name(self):
        """Creates the full image name to use for running the Scale Docker image

        :returns: The full Scale Docker image name
        :rtype: string
        """

        return '%s:%s' % (settings.SCALE_DOCKER_IMAGE, settings.DOCKER_VERSION)

    def _parse_container_name(self, task_update):
        """Tries to parse the container name out of the task update. Assumes caller already has the task lock.

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        if 'Config' in task_update.data and 'Env' in task_update.data['Config']:
            env_list = task_update.data['Config']['Env']
            if isinstance(env_list, list):
                for env_string in env_list:
                    env_split = env_string.split('=')
                    if len(env_split) == 2:
                        env_name = env_split[0]
                        env_value = env_split[1]
                        if env_name == 'MESOS_CONTAINER_NAME':
                            self._container_name = env_value
