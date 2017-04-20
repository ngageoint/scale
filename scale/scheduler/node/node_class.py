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
from scheduler.node.conditions import NodeConditions
from scheduler.sync.scheduler_manager import scheduler_mgr


logger = logging.getLogger(__name__)
NodeState = namedtuple('NodeState', ['state', 'title', 'description'])


class Node(object):
    """This class represents a node in the scheduler. It combines information retrieved from the database node models as
    well as run-time information retrieved from Mesos. This class is thread-safe."""

    # Thresholds for when to schedule node tasks again that have failed
    CLEANUP_ERR_THRESHOLD = datetime.timedelta(minutes=2)
    HEALTH_ERR_THRESHOLD = datetime.timedelta(minutes=2)
    IMAGE_PULL_ERR_THRESHOLD = datetime.timedelta(minutes=5)

    # Normal health check task threshold
    NORMAL_HEALTH_THRESHOLD = datetime.timedelta(minutes=5)

    # Node States
    inactive_desc = 'Node is inactive and will not run new or existing jobs.'
    inactive_desc += ' If this node has existing jobs, please cancel them or switch the node to active.'
    INACTIVE = NodeState(state='INACTIVE', title='Inactive', description=inactive_desc)
    OFFLINE = NodeState(state='OFFLINE', title='Offline',
                        description='Node is offline/unavailable, so no jobs can currently run on it.')
    paused_desc = 'Node is paused, so no new jobs will be scheduled. Existing jobs will continue to run.'
    PAUSED = NodeState(state='PAUSED', title='Paused', description=paused_desc)
    degraded_desc = 'Node has an error condition, putting it in a degraded state.'
    degraded_desc += ' New jobs will not be scheduled, and the node will attempt to continue to run existing jobs.'
    DEGRADED = NodeState(state='DEGRADED', title='Degraded', description=degraded_desc)
    cleanup_desc = 'Node is performing an initial cleanup step to remove existing Docker containers and volumes.'
    INITIAL_CLEANUP = NodeState(state='INITIAL_CLEANUP', title='Cleaning up', description=cleanup_desc)
    pull_desc = 'Node is pulling the Scale Docker image.'
    IMAGE_PULL = NodeState(state='IMAGE_PULL', title='Pulling image', description=pull_desc)
    READY = NodeState(state='READY', title='Ready', description='Node is ready to run new jobs.')

    def __init__(self, agent_id, node):
        """Constructor

        :param agent_id: The Mesos agent ID for the node
        :type agent_id: string
        :param node: The node model
        :type node: :class:`node.models.Node`
        """

        self._hostname = str(node.hostname)  # Never changes
        self._id = node.id  # Never changes

        self._agent_id = agent_id
        self._cleanup = NodeCleanup()
        self._cleanup_task = None
        self._conditions = NodeConditions(self._hostname)
        self._health_task = None
        self._is_active = node.is_active
        self._is_image_pulled = False
        self._is_initial_cleanup_completed = False
        self._is_online = True
        self._is_paused = node.is_paused
        self._last_heath_task = None
        self._lock = threading.Lock()
        self._port = node.port
        self._pull_task = None
        self._state = None
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
            self._conditions.update_cleanup_count(self._cleanup.get_num_job_exes())

    def generate_status_json(self, nodes_list):
        """Generates the portion of the status JSON that describes this node

        :param nodes_list: The list of nodes within the status JSON
        :type nodes_list: list
        """

        with self._lock:
            state_dict = {'name': self._state.state, 'title': self._state.title, 'description': self._state.description}
            node_dict = {'id': self._id, 'hostname': self._hostname, 'agent_id': self._agent_id,
                         'is_active': self._is_active, 'state': state_dict}
            self._conditions.generate_status_json(node_dict)
        nodes_list.append(node_dict)

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
                self._conditions.handle_cleanup_task_timeout()
            elif self._health_task and self._health_task.id == task.id:
                logger.warning('Health check task on host %s timed out', self._hostname)
                if self._health_task.has_ended:
                    self._health_task = None
                self._last_heath_task = now()
                self._conditions.handle_health_task_timeout()
            elif self._pull_task and self._pull_task.id == task.id:
                logger.warning('Scale image pull task on host %s timed out', self._hostname)
                if self._pull_task.has_ended:
                    self._pull_task = None
                self._conditions.handle_pull_task_timeout()
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

    def should_be_removed(self):
        """Indicates whether this node should be removed from the scheduler. If the node is no longer active and is also
        no longer online, there's no reason for the scheduler to continue to track it.

        :returns: True if this node should be removed from the scheduler
        :rtype: bool
        """

        return not self._is_active and not self._is_online

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
            if self._conditions.is_daemon_bad:
                return False

            # Schedule cleanup task if threshold has passed since last cleanup task error
            last_cleanup_error = self._conditions.last_cleanup_task_error()
            if last_cleanup_error:
                return when - last_cleanup_error > Node.CLEANUP_ERR_THRESHOLD
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
        elif not self._conditions.is_health_check_normal:
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
            if not self._is_initial_cleanup_completed or self._is_image_pulled or self._conditions.is_pull_bad:
                return False

            # Schedule pull task if threshold has passed since last pull task error
            last_pull_error = self._conditions.last_image_pull_task_error()
            if last_pull_error:
                return when - last_pull_error > Node.IMAGE_PULL_ERR_THRESHOLD
            # No pull error
            return True

        return False

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
                self._conditions.update_cleanup_count(self._cleanup.get_num_job_exes())
            self._conditions.handle_cleanup_task_completed()
        elif task_update.status == TaskStatusUpdate.FAILED:
            logger.warning('Cleanup task on host %s failed', self._hostname)
            self._conditions.handle_cleanup_task_failed()
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
            self._last_heath_task = now()
            self._conditions.handle_health_task_completed()
        elif task_update.status == TaskStatusUpdate.FAILED:
            logger.warning('Health check task on host %s failed', self._hostname)
            self._last_heath_task = now()
            self._conditions.handle_health_task_failed(task_update)
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
            self._conditions.handle_pull_task_completed()
        elif task_update.status == TaskStatusUpdate.FAILED:
            logger.warning('Scale image pull task on host %s failed', self._hostname)
            self._conditions.handle_pull_task_failed()
        elif task_update.status == TaskStatusUpdate.KILLED:
            logger.warning('Scale image pull task on host %s killed', self._hostname)
        if self._pull_task.has_ended:
            self._pull_task = None

    def _update_state(self):
        """Updates the node's state. Caller must have obtained the node's thread lock.
        """

        old_state = self._state

        if not self._is_active:
            self._state = self.INACTIVE
        elif not self._is_online:
            self._state = self.OFFLINE
        elif self._is_paused:
            self._state = self.PAUSED
        elif self._conditions.has_active_errors():
            self._state = self.DEGRADED
        elif not self._is_initial_cleanup_completed:
            self._state = self.INITIAL_CLEANUP
        elif not self._is_image_pulled:
            self._state = self.IMAGE_PULL
        else:
            self._state = self.READY

        if old_state != self._state:
            if self._state == self.DEGRADED:
                logger.warning('Host %s is now in %s state', self._hostname, self._state.state)
            else:
                logger.info('Host %s is now in %s state', self._hostname, self._state.state)
