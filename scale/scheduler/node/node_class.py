"""Defines the class that represents nodes in the scheduler"""
from __future__ import unicode_literals

import datetime
import logging
import threading
from collections import namedtuple

from django.utils.timezone import now

from job.tasks.pull_task import PullTask
from job.tasks.update import TaskStatusUpdate
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
    IMAGE_PULL_ERR_THRESHOLD = datetime.timedelta(minutes=5)
    IMAGE_PULL_ERR = NodeError(name='IMAGE_PULL', description='Unable to pull Scale image', daemon_bad=False,
                               pull_bad=False)

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
        self._hostname = node.hostname  # Never changes
        self._id = node.id  # Never changes
        self._is_active = node.is_active
        self._is_daemon_bad = False
        self._is_image_pulled = False
        self._is_initial_cleanup_completed = False
        self._is_online = True
        self._is_paused = node.is_paused
        self._is_pull_bad = False
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

    @property
    def is_initial_cleanup_completed(self):
        """Indicates whether this node has its initial cleanup completed (True) or not (False)

        :returns: Whether this node has its initial cleanup completed
        :rtype: bool
        """

        return self._is_initial_cleanup_completed

    @property
    def is_online(self):
        """Indicates whether this node is online (True) or not (False)

        :returns: Whether this node is online
        :rtype: bool
        """

        return self._is_online

    @property
    def is_paused(self):
        """Indicates whether this node is paused (True) or not (False)

        :returns: Whether this node is paused
        :rtype: bool
        """

        return self._is_paused

    @property
    def state(self):
        """Returns the state of the node

        :returns: The state
        :rtype: :class:`scheduler.node.node_class.NodeState`
        """

        return self._state

    def initial_cleanup_completed(self):
        """Tells this node that its initial cleanup task has succeeded
        """

        logger.info('Node %s has completed initial clean up', self._hostname)
        with self._lock:
            self._is_initial_cleanup_completed = True
            self._update_state()

    def get_next_task(self):
        """Returns the next node task to launch, possibly None

        :returns: The next node task to launch, possibly None
        :rtype: :class:`job.tasks.base_task.Task`
        """

        with self._lock:
            self._create_next_task()

            # No task returned if node is not ready, no task to launch, or task has already been launched
            if not self._is_ready_for_pull_task() or self._pull_task is None or self._pull_task.has_been_launched:
                return None

            return self._pull_task

    def handle_task_timeout(self, task):
        """Handles the timeout of the given node task

        :param task: The task
        :type task: :class:`job.tasks.base_task.Task`
        """

        with self._lock:
            if not self._pull_task or self._pull_task.id != task.id:
                return

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
            if not self._pull_task or self._pull_task.id != task_update.task_id:
                return

            if task_update.status == TaskStatusUpdate.FINISHED:
                self._is_image_pulled = True
                self._error_inactive(Node.IMAGE_PULL_ERR)
                logger.info('Node %s has finished pulling the Scale image', self._hostname)
            elif task_update.status == TaskStatusUpdate.FAILED:
                self._error_active(Node.IMAGE_PULL_ERR)
                logger.warning('Scale image pull task on host %s failed', self._hostname)
            elif task_update.status == TaskStatusUpdate.KILLED:
                logger.warning('Scale image pull task on host %s killed', self._hostname)
            if self._pull_task.has_ended:
                self._pull_task = None
            self._update_state()

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

    def _create_next_task(self):
        """Creates the next task that needs to be run for this node. Caller must have obtained the thread lock.
        """

        # If we have a pull task, check that node's agent ID has not changed
        if self._pull_task and self._pull_task.agent_id != self._agent_id:
            self._pull_task = None

        if self._pull_task:
            # Pull task already exists
            return

        if self._is_ready_for_pull_task():
            self._pull_task = PullTask(scheduler_mgr.framework_id, self._agent_id)

    def _is_ready_for_pull_task(self):
        """Indicates whether this node is ready to launch the pull task for the Scale Docker image. Caller must have
        obtained the thread lock.

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
                return now() - last_updated > Node.IMAGE_PULL_ERR_THRESHOLD

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
        active_error.last_updated = when

    def _error_inactive(self, error):
        """Indicates that the given error is now inactive. Caller must have obtained the thread lock.

        :param error: The node error
        :type error: :class:`scheduler.node.node_class.NodeError`
        """

        if error.name in self._active_errors:
            del self._active_errors[error.name]

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
