"""Defines the class that manages job executions"""
from __future__ import unicode_literals

import logging
import threading

from django.utils.timezone import now

from job.execution.metrics import TotalJobExeMetrics
from job.execution.tasks.exe_task import JOB_TASK_ID_PREFIX
from job.messages.completed_jobs import create_completed_jobs_messages, CompletedJob
from job.messages.failed_jobs import create_failed_jobs_messages, FailedJob
from job.messages.job_exe_end import create_job_exe_end_messages
from job.models import Job, JobExecution


logger = logging.getLogger(__name__)


class JobExecutionManager(object):
    """This class manages all running and finished job executions. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        # Execution information to be sent in command messages
        self._finished_job_exes = []  # Holds finished executions
        self._job_exe_end_models = []  # Holds job_exe_end models to create
        self._running_job_messages = []  # Holds running job messages

        # Current running state
        self._running_job_exes = {}  # {Cluster ID: RunningJobExecution}
        self._lock = threading.Lock()
        self._metrics = TotalJobExeMetrics(now())

    def add_canceled_job_exes(self, job_exe_ends):
        """Adds the given job_exe_end models for job executions canceled off of the queue

        :param job_exe_ends: The job_exe_end models to add
        :type job_exe_ends: :func:`list`
        """

        with self._lock:
            self._job_exe_end_models.extend(job_exe_ends)

    def check_for_starvation(self, when):
        """Checks all of the currently running job executions for resource starvation. If any starved executions are
        found, they are failed and returned.

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: A list of the starved job executions
        :rtype: :func:`list`
        """

        finished_job_exes = []
        with self._lock:
            for job_exe in self._running_job_exes.values():
                if job_exe.check_for_starvation(when):
                    if job_exe.is_finished():
                        self._handle_finished_job_exe(job_exe)
                        finished_job_exes.append(job_exe)

        return finished_job_exes

    def clear(self):
        """Clears all data from the manager. This method is intended for testing only.
        """

        self._running_job_exes = {}
        self._metrics = TotalJobExeMetrics(now())

    def generate_status_json(self, nodes_list, when):
        """Generates the portion of the status JSON that describes the job execution metrics

        :param nodes_list: The list of nodes within the status JSON
        :type nodes_list: :func:`list`
        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        with self._lock:
            self._metrics.generate_status_json(nodes_list, when)

    def get_messages(self):
        """Returns all messages related to jobs and executions that need to be sent

        :returns: The list of job-related messages to send
        :rtype: :func:`list`
        """

        running_job_messages = None
        job_exe_end_models = None
        finished_job_exes = None

        with self._lock:
            finished_job_exes = self._finished_job_exes
            job_exe_end_models = self._job_exe_end_models
            running_job_messages = self._running_job_messages
            self._finished_job_exes = []
            self._job_exe_end_models = []
            self._running_job_messages = []

        # Start with running job messages
        messages = running_job_messages

        # Add messages for creating job_exe_end models
        messages.extend(create_job_exe_end_messages(job_exe_end_models))

         # Add messages for finished job executions
        messages.extend(self._create_finished_job_exe_messages(finished_job_exes))

        return messages

    def get_running_job_exe(self, cluster_id):
        """Returns the running job execution with the given cluster ID, or None if the job execution does not exist

        :param cluster_id: The cluster ID of the job execution to return
        :type cluster_id: int
        :returns: The running job execution with the given cluster ID, possibly None
        :rtype: :class:`job.execution.job_exe.RunningJobExecution`
        """

        with self._lock:
            if cluster_id in self._running_job_exes:
                return self._running_job_exes[cluster_id]
            return None

    def get_running_job_exes(self):
        """Returns all currently running job executions

        :returns: A list of running job executions
        :rtype: [:class:`job.execution.job_exe.RunningJobExecution`]
        """

        with self._lock:
            return list(self._running_job_exes.values())

    def handle_task_timeout(self, task, when):
        """Handles the timeout of the given task

        :param task: The task
        :type task: :class:`job.tasks.base_task.Task`
        :param when: The time that the time out occurred
        :type when: :class:`datetime.datetime`
        """

        if task.id.startswith(JOB_TASK_ID_PREFIX):
            cluster_id = JobExecution.parse_cluster_id(task.id)
            with self._lock:
                if cluster_id in self._running_job_exes:
                    job_exe = self._running_job_exes[cluster_id]
                    # We do not remove the failed job execution at this point. We wait for the status update of the
                    # killed task to come back so that job execution cleanup occurs after the task is dead.
                    job_exe.execution_timed_out(task, when)

    def handle_task_update(self, task_update):
        """Handles the given task update and returns the associated job execution if it has finished

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        :returns: The job execution if it has finished, None otherwise
        :rtype: :class:`job.execution.job_exe.RunningJobExecution`
        """

        if task_update.task_id.startswith(JOB_TASK_ID_PREFIX):
            cluster_id = JobExecution.parse_cluster_id(task_update.task_id)
            with self._lock:
                if cluster_id in self._running_job_exes:
                    job_exe = self._running_job_exes[cluster_id]
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

    def lost_job_exes(self, job_exe_ids, when):
        """Informs the manager that the job executions with the given IDs were lost

        :param job_exe_ids: The IDs of the lost job executions
        :type job_exe_ids: :func:`list`
        :param when: The time that the executions were lost
        :type when: :class:`datetime.datetime`
        :returns: A list of the finished job executions
        :rtype: :func:`list`
        """

        lost_job_exe_ids = set(job_exe_ids)

        finished_job_exes = []
        with self._lock:
            for job_exe in self._running_job_exes.values():
                if job_exe.id in lost_job_exe_ids:
                    job_exe.execution_lost(when)
                    task = job_exe.current_task
                    if task:
                        # Node could be deprecated, so force kill the current task
                        task.force_kill()
                    if job_exe.is_finished():
                        self._handle_finished_job_exe(job_exe)
                        finished_job_exes.append(job_exe)

        return finished_job_exes

    def lost_node(self, node_id, when):
        """Informs the manager that the node with the given ID was lost and has gone offline

        :param node_id: The ID of the lost node
        :type node_id: int
        :param when: The time that the node was lost
        :type when: :class:`datetime.datetime`
        :returns: A list of the finished job executions
        :rtype: :func:`list`
        """

        finished_job_exes = []
        with self._lock:
            for job_exe in self._running_job_exes.values():
                if job_exe.node_id == node_id:
                    job_exe.execution_lost(when)
                    if job_exe.is_finished():
                        self._handle_finished_job_exe(job_exe)
                        finished_job_exes.append(job_exe)

        return finished_job_exes

    def schedule_job_exes(self, job_exes, messages):
        """Adds newly scheduled running job executions to the manager

        :param job_exes: A list of the running job executions to add
        :type job_exes: :func:`list`
        :param messages: The messages for the running jobs
        :type messages: :func:`list`
        """

        with self._lock:
            for job_exe in job_exes:
                self._running_job_exes[job_exe.cluster_id] = job_exe
            self._running_job_messages.extend(messages)
            self._metrics.add_running_job_exes(job_exes)

    def sync_with_database(self):
        """Syncs with the database to handle any canceled executions. Any job executions that are now finished are
        returned.

        :returns: A list of the finished job executions
        :rtype: :func:`list`
        """

        job_ids = []
        running_job_exes = []
        with self._lock:
            for running_job_exe in self._running_job_exes.values():
                job_ids.append(running_job_exe.job_id)
                running_job_exes.append(running_job_exe)

        # Query job models from database to check if any running executions have been canceled
        job_models = {}
        for job in Job.objects.filter(id__in=job_ids):
            job_models[job.id] = job

        finished_job_exes = []
        when_canceled = now()
        with self._lock:
            for running_job_exe in running_job_exes:
                job_model = job_models[running_job_exe.job_id]
                # If the job has been canceled or the job has a newer execution, this execution must be canceled
                if job_model.status == 'CANCELED' or job_model.num_exes > running_job_exe.exe_num:
                    running_job_exe.execution_canceled(when_canceled)
                    if running_job_exe.is_finished():
                        self._handle_finished_job_exe(running_job_exe)
                        finished_job_exes.append(running_job_exe)

        return finished_job_exes

    def _create_finished_job_exe_messages(self, finished_job_exes):
        """Creates messages for finished job executions

        :param finished_job_exes: The finished job executions
        :type finished_job_exes: :func:`list`
        :returns: The messages
        :rtype: :func:`list`
        """

        when = now()

        completed_jobs = []
        failed_jobs = []
        for job_exe in finished_job_exes:
            if job_exe.status == 'COMPLETED':
                completed_jobs.append(CompletedJob(job_exe.job_id, job_exe.exe_num))
            elif job_exe.status == 'FAILED':
                failed_jobs.append(FailedJob(job_exe.job_id, job_exe.exe_num, job_exe.error.id))

        messages = create_completed_jobs_messages(completed_jobs, when)
        messages.extend(create_failed_jobs_messages(failed_jobs, when))

        return messages

    def _handle_finished_job_exe(self, running_job_exe):
        """Handles the finished job execution. Caller must have obtained the manager lock.

        :param running_job_exe: The finished job execution
        :type running_job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        # Create job_exe_end model for the finished job execution and send it in a future message
        self._job_exe_end_models.append(running_job_exe.create_job_exe_end_model())

        # Collect finished job execution to send a future job update message
        self._finished_job_exes.append(running_job_exe)

        # Remove the finished job execution and update the metrics
        del self._running_job_exes[running_job_exe.cluster_id]
        self._metrics.job_exe_finished(running_job_exe)


job_exe_mgr = JobExecutionManager()
