"""Defines the class that manages job executions"""
from __future__ import unicode_literals

import logging
import threading

from django.utils.timezone import now

from job.execution.metrics import TotalJobExeMetrics
from job.execution.tasks.exe_task import JOB_TASK_ID_PREFIX
from job.messages.job_exe_end import CreateJobExecutionEnd
from job.models import Job, JobExecution


logger = logging.getLogger(__name__)


class JobExecutionManager(object):
    """This class manages all running and finished job executions. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._job_exe_end_models = []  # Holds job_exe_end models to send in next messages
        self._running_job_exes = {}  # {Cluster ID: RunningJobExecution}
        self._running_job_messages = []  # Holds running job messages to send
        self._lock = threading.Lock()
        self._metrics = TotalJobExeMetrics(now())

    def add_canceled_job_exes(self, job_exe_ends):
        """Adds the given job_exe_end models for job executions canceled off of the queue

        :param job_exe_ends: The job_exe_end models to add
        :type job_exe_ends: list
        """

        with self._lock:
            self._job_exe_end_models.extend(job_exe_ends)

    def clear(self):
        """Clears all data from the manager. This method is intended for testing only.
        """

        self._running_job_exes = {}
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

    def get_messages(self):
        """Returns all messages related to jobs and executions that need to be sent

        :returns: The list of job-related messages to send
        :rtype: list
        """

        with self._lock:
            messages = self._running_job_messages
            self._running_job_messages = []

            message = None
            for job_exe_end in self._job_exe_end_models:
                if not message:
                    message = CreateJobExecutionEnd()
                elif not message.can_fit_more():
                    messages.append(message)
                    message = CreateJobExecutionEnd()
                message.add_job_exe_end(job_exe_end)
            if message:
                messages.append(message)
            self._job_exe_end_models = []

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

        finished_job_exe = None
        if task_update.task_id.startswith(JOB_TASK_ID_PREFIX):
            cluster_id = JobExecution.parse_cluster_id(task_update.task_id)
            with self._lock:
                if cluster_id in self._running_job_exes:
                    job_exe = self._running_job_exes[cluster_id]
                    job_exe.task_update(task_update)
                    if job_exe.is_finished():
                        self._handle_finished_job_exe(job_exe)
                        finished_job_exe = job_exe
                        # return job_exe

        # TODO: this can be removed once database operations move to messaging backend
        if finished_job_exe:
            self._handle_finished_job_exe_in_database(finished_job_exe)
            return finished_job_exe

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
        :rtype: list
        """

        lost_exes = []
        finished_job_exes = []
        with self._lock:
            for job_exe in self._running_job_exes.values():
                if job_exe.node_id == node_id:
                    lost_exes.append(job_exe)
                    job_exe.execution_lost(when)
                    if job_exe.is_finished():
                        self._handle_finished_job_exe(job_exe)
                        finished_job_exes.append(job_exe)

        # TODO: this can be removed once database operations move to messaging backend
        for finished_job_exe in finished_job_exes:
            self._handle_finished_job_exe_in_database(finished_job_exe)

        return lost_exes

    def schedule_job_exes(self, job_exes, messages):
        """Adds newly scheduled running job executions to the manager

        :param job_exes: A list of the running job executions to add
        :type job_exes: list
        :param messages: The messages for the running jobs
        :type messages: list
        """

        with self._lock:
            for job_exe in job_exes:
                self._running_job_exes[job_exe.cluster_id] = job_exe
            self._running_job_messages.extend(messages)
            self._metrics.add_running_job_exes(job_exes)

    def sync_with_database(self):
        """Syncs with the database to handle any canceled executions. The current task of each canceled job execution is
        returned so the tasks may be killed.

        :returns: A list of the canceled tasks to kill
        :rtype: [:class:`job.tasks.base_task.Task`]
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

        canceled_tasks = []
        finished_job_exes = []
        when_canceled = now()
        with self._lock:
            for running_job_exe in running_job_exes:
                job_model = job_models[running_job_exe.job_id]
                # If the job has been canceled or the job has a newer execution, this execution must be canceled
                if job_model.status == 'CANCELED' or job_model.num_exes > running_job_exe.exe_num:
                    task = running_job_exe.execution_canceled(when_canceled)
                    if task:
                        # Since it has an outstanding task, we do not remove the canceled job execution at this point.
                        # We wait for the status update of the killed task to come back so that job execution cleanup
                        # occurs after the task is dead.
                        canceled_tasks.append(task)
                    else:
                        if running_job_exe.is_finished():
                            self._handle_finished_job_exe(running_job_exe)
                            finished_job_exes.append(running_job_exe)

        # TODO: this can be removed once database operations move to messaging backend
        for finished_job_exe in finished_job_exes:
            self._handle_finished_job_exe_in_database(finished_job_exe)

        return canceled_tasks

    def _handle_finished_job_exe(self, running_job_exe):
        """Handles the finished job execution. Caller must have obtained the manager lock.

        :param running_job_exe: The finished job execution
        :type running_job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        # Create job_exe_end model for the finished job execution and send it in next messages
        self._job_exe_end_models.append(running_job_exe.create_job_exe_end_model())

        # Remove the finished job execution and update the metrics
        del self._running_job_exes[running_job_exe.cluster_id]
        self._metrics.job_exe_finished(running_job_exe)

    def _handle_finished_job_exe_in_database(self, running_job_exe):
        """Handles the finished job execution by performing any needed database operations. This is a stop gap until
        these database operations move to the messaging backend.

        :param running_job_exe: The finished job execution
        :type running_job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        """

        # TODO: handling job completion and failure here for now, later these will be sent via messaging backend in a
        # background thread
        from queue.models import Queue
        job_id = running_job_exe.job_id
        exe_num = running_job_exe.exe_num
        when = running_job_exe.finished
        if running_job_exe.status == 'COMPLETED':
            Queue.objects.handle_job_completion(job_id, exe_num, when)
        elif running_job_exe.status == 'FAILED':
            Queue.objects.handle_job_failure(job_id, exe_num, when, running_job_exe.error)


job_exe_mgr = JobExecutionManager()
