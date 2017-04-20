"""Defines the class that manages job executions"""
from __future__ import unicode_literals

import logging
import threading

from django.db import DatabaseError
from django.utils.timezone import now

from job.execution.metrics import TotalJobExeMetrics
from job.execution.tasks.exe_task import JOB_TASK_ID_PREFIX
from job.models import JobExecution

logger = logging.getLogger(__name__)


class JobExecutionManager(object):
    """This class manages all running and finished job executions. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._running_job_exes = {}  # {ID: RunningJobExecution}
        self._lock = threading.Lock()
        self._metrics = TotalJobExeMetrics(now())

    def generate_status_json(self, nodes_list, when):
        """Generates the portion of the status JSON that describes the job execution metrics

        :param nodes_list: The list of nodes within the status JSON
        :type nodes_list: list
        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        with self._lock:
            self._metrics.generate_status_json(nodes_list, when)

    def get_ready_job_exes(self):
        """Returns all running job executions that are ready to execute their next task

        :returns: A list of running job executions
        :rtype: [:class:`job.execution.job_exe.RunningJobExecution`]
        """

        ready_exes = []
        with self._lock:
            for job_exe_id in self._running_job_exes:
                job_exe = self._running_job_exes[job_exe_id]
                if job_exe.is_next_task_ready():
                    ready_exes.append(job_exe)
        return ready_exes

    def get_running_job_exe(self, job_exe_id):
        """Returns the running job execution with the given ID, or None if the job execution does not exist

        :param job_exe_id: The ID of the job execution to return
        :type job_exe_id: int
        :returns: The running job execution with the given ID, possibly None
        :rtype: :class:`job.execution.job_exe.RunningJobExecution`
        """

        with self._lock:
            if job_exe_id in self._running_job_exes:
                return self._running_job_exes[job_exe_id]
            return None

    def get_running_job_exes(self):
        """Returns all currently running job executions

        :returns: A list of running job executions
        :rtype: [:class:`job.execution.job_exe.RunningJobExecution`]
        """

        running_job_exes = []
        with self._lock:
            for job_exe_id in self._running_job_exes:
                running_job_exes.append(self._running_job_exes[job_exe_id])
        return running_job_exes

    def handle_task_timeout(self, task, when):
        """Handles the timeout of the given task

        :param task: The task
        :type task: :class:`job.tasks.base_task.Task`
        :param when: The time that the time out occurred
        :type when: :class:`datetime.datetime`
        """

        if task.id.startswith(JOB_TASK_ID_PREFIX):
            job_exe_id = JobExecution.get_job_exe_id(task.id)
            with self._lock:
                if job_exe_id in self._running_job_exes:
                    job_exe = self._running_job_exes[job_exe_id]
                    try:
                        job_exe.execution_timed_out(task, when)
                    except DatabaseError:
                        logger.exception('Error failing timed out job execution %i', job_exe_id)
                    # We do not remove timed out job executions at this point. We wait for the status update of the
                    # killed task to come back so that job execution cleanup occurs after the task is dead.

    def handle_task_update(self, task_update):
        """Handles the given task update and returns the associated job execution if it has finished

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        :returns: The job execution if it has finished, None otherwise
        :rtype: :class:`job.execution.job_exe.RunningJobExecution`
        """

        if task_update.task_id.startswith(JOB_TASK_ID_PREFIX):
            job_exe_id = JobExecution.get_job_exe_id(task_update.task_id)
            with self._lock:
                if job_exe_id in self._running_job_exes:
                    job_exe = self._running_job_exes[job_exe_id]
                    job_exe.task_update(task_update)
                    if job_exe.is_finished():
                        self._handle_finished_job_exe(job_exe)
                        return job_exe

        return None

    def init_with_database(self):
        """Initializes the job execution metrics with the execution history from the database
        """

        with self._lock:
            self._metrics.init_with_database()

    def lost_node(self, node_id, when):
        """Informs the manager that the node with the given ID was lost and has gone offline

        :param node_id: The ID of the lost node
        :type node_id: int
        :param when: The time that the node was lost
        :type when: :class:`datetime.datetime`
        :returns: A list of the lost job executions that had been running on the node
        :rtype: [:class:`job.execution.job_exe.RunningJobExecution`]
        """

        lost_exes = []
        with self._lock:
            for job_exe_id in self._running_job_exes.keys():
                job_exe = self._running_job_exes[job_exe_id]
                if job_exe.node_id == node_id:
                    lost_exes.append(job_exe)
                    try:
                        job_exe.execution_lost(when)
                    except DatabaseError:
                        logger.exception('Error failing lost job execution: %s', job_exe.id)
                    if job_exe.is_finished():
                        self._handle_finished_job_exe(job_exe)
        return lost_exes

    def schedule_job_exes(self, job_exes):
        """Adds newly scheduled running job executions to the manager

        :param job_exes: A list of the running job executions to add
        :type job_exes: [:class:`job.execution.job_exe.RunningJobExecution`]
        """

        with self._lock:
            for job_exe in job_exes:
                self._running_job_exes[job_exe.id] = job_exe
            self._metrics.add_running_job_exes(job_exes)

    def sync_with_database(self):
        """Syncs with the database to handle any canceled executions. The current task of each canceled job execution is
        returned so the tasks may be killed.

        :returns: A list of the canceled tasks to kill
        :rtype: [:class:`job.tasks.base_task.Task`]
        """

        with self._lock:
            job_exe_ids = list(self._running_job_exes.keys())

        canceled_tasks = []
        canceled_models = list(JobExecution.objects.filter(id__in=job_exe_ids, status='CANCELED').iterator())

        with self._lock:
            for job_exe_model in canceled_models:
                if job_exe_model.id in self._running_job_exes:
                    canceled_job_exe = self._running_job_exes[job_exe_model.id]
                    try:
                        task = canceled_job_exe.execution_canceled()
                        if task:
                            canceled_tasks.append(task)
                    except DatabaseError:
                        logger.exception('Error canceling job execution %i', job_exe_model.id)
                    # We do not remove canceled job executions at this point. We wait for the status update of the
                    # killed task to come back so that job execution cleanup occurs after the task is dead.

        return canceled_tasks

    def _handle_finished_job_exe(self, job_exe):
        """Handles the finished job execution. Caller must have obtained the manager lock.

        :param job_exe: The finished job execution
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        del self._running_job_exes[job_exe.id]
        self._metrics.job_exe_finished(job_exe)


job_exe_mgr = JobExecutionManager()
