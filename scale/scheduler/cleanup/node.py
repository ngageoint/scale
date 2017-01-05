"""Defines the class that handles a node's cleanup"""
from __future__ import unicode_literals

import logging
import threading

from job.execution.tasks.cleanup_task import CleanupTask

from job.tasks.update import TaskStatusUpdate
from scheduler.sync.scheduler_manager import scheduler_mgr


JOB_EXES_WARNING_THRESHOLD = 100
MAX_JOB_EXES_PER_CLEANUP = 25


logger = logging.getLogger(__name__)


class NodeCleanup(object):
    """This class manages all of the cleanup for a node. This class is thread-safe."""

    def __init__(self, node):
        """Constructor

        :param node: The node
        :type node: :class:`scheduler.node.node_class.Node`
        """

        self._current_task = None
        self._job_exes = {}  # {Job Exe ID: RunningJobExecution}
        self._lock = threading.Lock()
        self._node = node

    def add_job_execution(self, job_exe):
        """Adds a job execution that needs to be cleaned up

        :param job_exe: The job execution to add
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        with self._lock:
            self._job_exes[job_exe.id] = job_exe

    def get_next_task(self):
        """Returns the next cleanup task to launch, possibly None

        :returns: The next cleanup task to launch, possibly None
        :rtype: :class:`job.execution.tasks.cleanup_task.CleanupTask`
        """

        with self._lock:
            self._create_next_task()

            # No task returned if node is paused, no task to launched, or task has already been launched
            if self._node.is_paused or self._current_task is None or self._current_task.has_been_launched:
                return None

            return self._current_task

    def handle_task_timeout(self, task):
        """Handles the timeout of the given cleanup task

        :param task: The task
        :type task: :class:`job.tasks.base_task.Task`
        """

        with self._lock:
            if not self._current_task or self._current_task.id != task.id:
                return

            logger.warning('Cleanup task on host %s timed out', self._node.hostname)
            if self._current_task.has_ended:
                self._current_task = None

    def handle_task_update(self, task_update):
        """Handles the given task update

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if not self._current_task or self._current_task.id != task_update.task_id:
                return

            if task_update.status == TaskStatusUpdate.FINISHED:
                if self._current_task.is_initial_cleanup:
                    # Initial cleanup is done
                    self._node.initial_cleanup_completed()
                else:
                    # Clear job executions that were cleaned up
                    for job_exe in self._current_task.job_exes:
                        del self._job_exes[job_exe.id]
            elif task_update.status == TaskStatusUpdate.FAILED:
                logger.warning('Cleanup task on host %s failed', self._node.hostname)
            elif task_update.status == TaskStatusUpdate.KILLED:
                logger.warning('Cleanup task on host %s killed', self._node.hostname)
            if self._current_task.has_ended:
                self._current_task = None

    def _create_next_task(self):
        """Creates the next cleanup task that needs to be run for this node. Caller must have obtained the thread lock.
        """

        # If we have a current task, check that node's agent ID has not changed
        if self._current_task and self._current_task.agent_id != self._node.agent_id:
            self._current_task = None

        if self._current_task:
            # Current task already exists
            return

        total_job_exes = self._job_exes.values()
        count = len(total_job_exes)
        if count > JOB_EXES_WARNING_THRESHOLD:
            logger.warning('Node %s has %d job executions waiting to be cleaned up', self._node.hostname, count)

        cleanup_job_exes = []
        if self._node.is_initial_cleanup_completed:
            if count == 0:
                # No job executions to clean, so no new task
                return
            for job_exe in total_job_exes:
                cleanup_job_exes.append(job_exe)
                if len(cleanup_job_exes) >= MAX_JOB_EXES_PER_CLEANUP:
                    break

        self._current_task = CleanupTask(scheduler_mgr.framework_id, self._node.agent_id, cleanup_job_exes)
