"""Defines the class that represents nodes in the scheduler"""
from __future__ import unicode_literals

import datetime
import logging
import threading
from collections import namedtuple

from django.utils.timezone import now

from job.tasks.health_task import HealthTask
from job.tasks.pull_task import PullTask
from job.tasks.update import TaskStatusUpdate
from scheduler.cleanup.node import NodeCleanup
from scheduler.sync.scheduler_manager import scheduler_mgr


logger = logging.getLogger(__name__)
NodeError = namedtuple('NodeError', ['name', 'description', 'daemon_bad', 'pull_bad'])
NodeState = namedtuple('NodeState', ['state', 'description'])


class ActiveError(object):
    """This class represents an active error for this node."""

    def __init__(self, error):
        """Constructor

        :param error: The node error
        :type error: :class:`scheduler.node.node_class.NodeError`
        """

        self.error = error
        self.started = None
        self.last_updated = None


class Node(object):
    """This class represents a node in the scheduler. It combines information retrieved from the database node models as
    well as run-time information retrieved from Mesos. This class is thread-safe."""

    # Node Errors
    BAD_DAEMON_ERR = NodeError(name='BAD_DAEMON', description='Docker daemon is not responding', daemon_bad=True,
                               pull_bad=True)
    CLEANUP_ERR = NodeError(name='CLEANUP', description='Failed to perform cleanup', daemon_bad=False, pull_bad=False)
    HEALTH_TIMEOUT_ERR = NodeError(name='HEALTH_TIMEOUT', description='Node health check timed out', daemon_bad=False,
                                   pull_bad=False)
    IMAGE_PULL_ERR = NodeError(name='IMAGE_PULL', description='Failed to pull Scale image', daemon_bad=False,
                               pull_bad=False)
    LOW_DOCKER_SPACE_ERR = NodeError(name='LOW_DOCKER_SPACE', description='Low Docker disk space', daemon_bad=False,
                                     pull_bad=True)
    HEALTH_ERRORS = [BAD_DAEMON_ERR, HEALTH_TIMEOUT_ERR]

    # Error thresholds
    CLEANUP_ERR_THRESHOLD = datetime.timedelta(minutes=2)
    HEALTH_ERR_THRESHOLD = datetime.timedelta(minutes=2)
    IMAGE_PULL_ERR_THRESHOLD = datetime.timedelta(minutes=5)

    # Normal health check threshold
    NORMAL_HEALTH_THRESHOLD = datetime.timedelta(minutes=5)

    # Node States
    INACTIVE = NodeState(state='INACTIVE', description='Inactive, ignored by Scale')
    OFFLINE = NodeState(state='OFFLINE', description='Offline/unavailable')
    PAUSED = NodeState(state='PAUSED', description='Paused, no new jobs will be scheduled')
    DEGRADED = NodeState(state='DEGRADED', description='Degraded ability to run jobs')
    INITIAL_CLEANUP = NodeState(state='INITIAL_CLEANUP', description='Performing initial cleanup')
    IMAGE_PULL = NodeState(state='IMAGE_PULL', description='Pulling Scale image')
    READY = NodeState(state='READY', description='Ready for new jobs')

    def __init__(self, agent_id, node):
        """Constructor

        :param agent_id: The Mesos agent ID for the node
        :type agent_id: string
        :param node: The node model
        :type node: :class:`node.models.Node`
        """

        self._active_errors = {}  # {Error name: ActiveError}
        self._agent_id = agent_id
        self._cleanup = NodeCleanup()
        self._cleanup_task = None
        self._health_task = None
        self._hostname = node.hostname  # Never changes
        self._id = node.id  # Never changes
        self._is_active = node.is_active
        self._is_daemon_bad = False
        self._is_health_check_normal = True
        self._is_image_pulled = False
        self._is_initial_cleanup_completed = False
        self._is_online = True
        self._is_paused = node.is_paused
        self._is_pull_bad = False
        self._last_heath_task = None
        self._lock = threading.Lock()
        self._port = node.port
        self._pull_task = None
        self._state = self.INACTIVE
        self._update_state()

    @property
    def agent_id(self):
        """Returns the agent ID of the node

        :returns: The agent ID
        :rtype: string
        """

        return self._agent_id

    @property
    def hostname(self):
        """Returns the hostname of the node

        :returns: The hostname
        :rtype: string
        """

        return self._hostname

    @property
    def id(self):
        """Returns the ID of the node

        :returns: The node ID
        :rtype: int
        """

        return self._id

    @property
    def is_active(self):
        """Indicates whether this node is active (True) or not (False)

        :returns: Whether this node is active
        :rtype: bool
        """

        return self._is_active

    def add_job_execution(self, job_exe):
        """Adds a job execution that needs to be cleaned up

        :param job_exe: The job execution to add
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        with self._lock:
            self._cleanup.add_job_execution(job_exe)

    def get_next_tasks(self, when):
        """Returns the next node tasks to launch

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The list of node tasks to launch
        :rtype: [:class:`job.tasks.base_task.Task`]
        """

        with self._lock:
            self._create_next_tasks(when)

            tasks = []

            # Check if ready for cleanup task and it hasn't been launched yet
            if self._is_ready_for_cleanup_task(when):
                if self._cleanup_task and not self._cleanup_task.has_been_launched:
                    tasks.append(self._cleanup_task)

            # Check if ready for health check task and it hasn't been launched yet
            if self._is_ready_for_health_task(when) and self._health_task and not self._health_task.has_been_launched:
                tasks.append(self._health_task)

            # Check if ready for pull task and it hasn't been launched yet
            if self._is_ready_for_pull_task(when) and self._pull_task and not self._pull_task.has_been_launched:
                tasks.append(self._pull_task)

            return tasks

    def handle_task_timeout(self, task):
        """Handles the timeout of the given node task

        :param task: The task
        :type task: :class:`job.tasks.base_task.Task`
        """

        with self._lock:
            if self._cleanup_task and self._cleanup_task.id == task.id:
                logger.warning('Cleanup task on host %s timed out', self._hostname)
                if self._cleanup_task.has_ended:
                    self._cleanup_task = None
                self._error_active(Node.CLEANUP_ERR)
            elif self._health_task and self._health_task.id == task.id:
                logger.warning('Health check task on host %s timed out', self._hostname)
                if self._health_task.has_ended:
                    self._health_task = None
                self._is_health_check_normal = False
                self._last_heath_task = now()
                self._error_inactive_all_health()
                self._error_active(Node.HEALTH_TIMEOUT_ERR)
            elif self._pull_task and self._pull_task.id == task.id:
                logger.warning('Scale image pull task on host %s timed out', self._hostname)
                if self._pull_task.has_ended:
                    self._pull_task = None
                self._error_active(Node.IMAGE_PULL_ERR)
            self._update_state()

    def handle_task_update(self, task_update):
        """Handles the given task update

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if self._cleanup_task and self._cleanup_task.id == task_update.task_id:
                self._handle_cleanup_task_update(task_update)
            elif self._health_task and self._health_task.id == task_update.task_id:
                self._handle_health_task_update(task_update)
            elif self._pull_task and self._pull_task.id == task_update.task_id:
                self._handle_pull_task_update(task_update)
            self._update_state()

    def is_ready_for_new_job(self):
        """Indicates whether this node is ready to launch a new job execution

        :returns: True if this node is ready to launch a new job execution, False otherwise
        :rtype: bool
        """

        return self._state == Node.READY

    def is_ready_for_next_job_task(self):
        """Indicates whether this node is ready to launch the next task of a job execution

        :returns: True if this node is ready to launch a job task, False otherwise
        :rtype: bool
        """

        return self._state not in [Node.INACTIVE, Node.OFFLINE]

    def update_from_mesos(self, agent_id=None, port=None, is_online=None):
        """Updates this node's data from Mesos

        :param agent_id: The Mesos agent ID for the node
        :type agent_id: string
        :param port: The Mesos port of the node
        :type port: int
        :param is_online: Whether the Mesos agent is online
        :type is_online: bool
        """

        with self._lock:
            if agent_id:
                self._agent_id = agent_id
            if port:
                self._port = port
            if is_online is not None:
                self._is_online = is_online
            self._update_state()

    def update_from_model(self, node):
        """Updates this node's data from the database model

        :param node: The node model
        :type node: :class:`node.models.Node`
        """

        if self.id != node.id:
            raise Exception('Trying to update node from incorrect database model')

        with self._lock:
            self._is_active = node.is_active
            self._is_paused = node.is_paused
            self._update_state()

    def _create_next_tasks(self, when):
        """Creates the next tasks that needs to be run for this node. Caller must have obtained the thread lock.

        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        # If we have a cleanup task, check that node's agent ID has not changed
        if self._cleanup_task and self._cleanup_task.agent_id != self._agent_id:
            self._cleanup_task = None

        if not self._cleanup_task and self._is_ready_for_cleanup_task(when):
            self._cleanup_task = self._cleanup.create_next_task(self._agent_id, self._hostname,
                                                                self._is_initial_cleanup_completed)

        # If we have a health task, check that node's agent ID has not changed
        if self._health_task and self._health_task.agent_id != self._agent_id:
            self._health_task = None

        if not self._health_task and self._is_ready_for_health_task(when):
            self._health_task = HealthTask(scheduler_mgr.framework_id, self._agent_id)

        # If we have a pull task, check that node's agent ID has not changed
        if self._pull_task and self._pull_task.agent_id != self._agent_id:
            self._pull_task = None

        if not self._pull_task and self._is_ready_for_pull_task(when):
            self._pull_task = PullTask(scheduler_mgr.framework_id, self._agent_id)

    def _image_pull_completed(self):
        """Tells this node that its image pull task has succeeded. Caller must have obtained the thread lock.
        """

        logger.info('Node %s has finished pulling the Scale image', self._hostname)
        self._is_image_pulled = True

    def _initial_cleanup_completed(self):
        """Tells this node that its initial cleanup task has succeeded. Caller must have obtained the thread lock.
        """

        logger.info('Node %s has completed initial clean up', self._hostname)
        self._is_initial_cleanup_completed = True

    def _is_ready_for_cleanup_task(self, when):
        """Indicates whether this node is ready to launch a cleanup task. Caller must have obtained the thread lock.

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: True if this node is ready to launch a cleanup task, False otherwise
        :rtype: bool
        """

        if self._state in [Node.INITIAL_CLEANUP, Node.IMAGE_PULL, Node.READY]:
            return True
        elif self._state == Node.DEGRADED:
            # The cleanup task can be scheduled during DEGRADED state as long as the Docker daemon is OK
            if self._is_daemon_bad:
                return False

            # Schedule cleanup task if threshold has passed since last cleanup task error
            if Node.CLEANUP_ERR.name in self._active_errors:
                last_updated = self._active_errors[Node.CLEANUP_ERR.name].last_updated
                return when - last_updated > Node.CLEANUP_ERR_THRESHOLD
            # No cleanup error
            return True

        return False

    def _is_ready_for_health_task(self, when):
        """Indicates whether this node is ready to launch a health check task. Caller must have obtained the thread
        lock.

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: True if this node is ready to launch a health check task, False otherwise
        :rtype: bool
        """

        if self._state in [Node.INACTIVE, Node.OFFLINE]:
            return False
        elif not self._is_health_check_normal:
            # Schedule health task if threshold has passed since last health task error
            return when - self._last_heath_task > Node.HEALTH_ERR_THRESHOLD

        # Node is normal, use normal threshold for when to schedule next health check
        return not self._last_heath_task or (when - self._last_heath_task > Node.NORMAL_HEALTH_THRESHOLD)

    def _is_ready_for_pull_task(self, when):
        """Indicates whether this node is ready to launch the pull task for the Scale Docker image. Caller must have
        obtained the thread lock.

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: True if this node is ready to launch a pull task, False otherwise
        :rtype: bool
        """

        if self._state == Node.IMAGE_PULL:
            return True
        elif self._state == Node.DEGRADED:
            # The pull task can be scheduled during DEGRADED state if other conditions match IMAGE_PULL state and the
            # DEGRADED errors do not affect the ability to do an image pull

            # Make sure initial cleanup is done, image pull is not done, and image pull on the node works
            if not self._is_initial_cleanup_completed or self._is_image_pulled or self._is_pull_bad:
                return False

            # Schedule pull task if threshold has passed since last pull task error
            if Node.IMAGE_PULL_ERR.name in self._active_errors:
                last_updated = self._active_errors[Node.IMAGE_PULL_ERR.name].last_updated
                return when - last_updated > Node.IMAGE_PULL_ERR_THRESHOLD
            # No pull error
            return True

        return False

    def _error_active(self, error):
        """Indicates that the given error is now active. Caller must have obtained the thread lock.

        :param error: The node error
        :type error: :class:`scheduler.node.node_class.NodeError`
        """

        when = now()
        if error.name in self._active_errors:
            active_error = self._active_errors[error.name]
        else:
            active_error = ActiveError(error)
            active_error.started = when
            self._active_errors[error.name] = active_error
        active_error.last_updated = when

    def _error_inactive(self, error):
        """Indicates that the given error is now inactive. Caller must have obtained the thread lock.

        :param error: The node error
        :type error: :class:`scheduler.node.node_class.NodeError`
        """

        if error.name in self._active_errors:
            del self._active_errors[error.name]

    def _error_inactive_all_health(self):
        """Inactivates all health-related node errors. Caller must have obtained the thread lock.
        """

        for error in Node.HEALTH_ERRORS:
            self._error_inactive(error)

    def _handle_cleanup_task_update(self, task_update):
        """Handles the given task update for a cleanup task. Caller must have obtained the thread lock.

        :param task_update: The cleanup task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        if task_update.status == TaskStatusUpdate.FINISHED:
            if self._cleanup_task.is_initial_cleanup:
                self._initial_cleanup_completed()
            else:
                # Clear job executions that were cleaned up
                self._cleanup.delete_job_executions(self._cleanup_task.job_exes)
            self._error_inactive(Node.CLEANUP_ERR)
        elif task_update.status == TaskStatusUpdate.FAILED:
            logger.warning('Cleanup task on host %s failed', self._hostname)
            self._error_active(Node.CLEANUP_ERR)
        elif task_update.status == TaskStatusUpdate.KILLED:
            logger.warning('Cleanup task on host %s killed', self._hostname)
        if self._cleanup_task.has_ended:
            self._cleanup_task = None

    def _handle_health_task_update(self, task_update):
        """Handles the given task update for a health check task. Caller must have obtained the thread lock.

        :param task_update: The health check task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        if task_update.status == TaskStatusUpdate.FINISHED:
            self._is_health_check_normal = True
            self._last_heath_task = now()
            self._error_inactive_all_health()
        elif task_update.status == TaskStatusUpdate.FAILED:
            logger.warning('Health check task on host %s failed', self._hostname)
            self._is_health_check_normal = False
            self._last_heath_task = now()
            self._error_inactive_all_health()
            if task_update.exit_code == HealthTask.BAD_DAEMON_CODE:
                logger.warning('Docker daemon not responding on host %s', self._hostname)
                self._error_active(Node.BAD_DAEMON_ERR)
            elif task_update.exit_code == HealthTask.LOW_DOCKER_SPACE_CODE:
                logger.warning('Low Docker disk space on host %s', self._hostname)
                self._error_active(Node.LOW_DOCKER_SPACE_ERR)
            else:
                logger.error('Unknown failed health check exit code: %s', str(task_update.exit_code))
        elif task_update.status == TaskStatusUpdate.KILLED:
            logger.warning('Health check task on host %s killed', self._hostname)
        if self._health_task.has_ended:
            self._health_task = None

    def _handle_pull_task_update(self, task_update):
        """Handles the given task update for a pull task. Caller must have obtained the thread lock.

        :param task_update: The pull task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        if task_update.status == TaskStatusUpdate.FINISHED:
            self._image_pull_completed()
            self._error_inactive(Node.IMAGE_PULL_ERR)
        elif task_update.status == TaskStatusUpdate.FAILED:
            self._error_active(Node.IMAGE_PULL_ERR)
            logger.warning('Scale image pull task on host %s failed', self._hostname)
        elif task_update.status == TaskStatusUpdate.KILLED:
            logger.warning('Scale image pull task on host %s killed', self._hostname)
        if self._pull_task.has_ended:
            self._pull_task = None

    def _update_state(self):
        """Updates the node's state. Caller must have obtained the node's thread lock.
        """

        self._is_daemon_bad = False
        self._is_pull_bad = False
        for active_error in self._active_errors.values():
            self._is_daemon_bad = self._is_daemon_bad or active_error.error.daemon_bad
            self._is_pull_bad = self._is_pull_bad or active_error.error.pull_bad

        if not self._is_active:
            self._state = self.INACTIVE
        elif not self._is_online:
            self._state = self.OFFLINE
        elif self._is_paused:
            self._state = self.PAUSED
        elif self._active_errors:
            self._state = self.DEGRADED
        elif not self._is_initial_cleanup_completed:
            self._state = self.INITIAL_CLEANUP
        elif not self._is_image_pulled:
            self._state = self.IMAGE_PULL
        else:
            self._state = self.READY
