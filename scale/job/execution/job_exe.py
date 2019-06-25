"""Defines the class that represents running job executions"""
from __future__ import unicode_literals

import datetime
import logging
import threading

from django.utils.timezone import now

from error.models import get_builtin_error, get_unknown_error
from job.execution.tasks.json.results.task_results import TaskResults
from job.execution.tasks.main_task import MainTask
from job.execution.tasks.post_task import PostTask
from job.execution.tasks.pre_task import PreTask
from job.execution.tasks.pull_task import PullTask
from job.models import JobExecutionEnd
from job.tasks.update import TaskStatusUpdate


RESOURCE_STARVATION_THRESHOLD = datetime.timedelta(minutes=10)


logger = logging.getLogger(__name__)


class RunningJobExecution(object):
    """This class represents a currently running job execution. This class is thread-safe."""

    def __init__(self, agent_id, job_exe, job_type, configuration, priority):
        """Constructor

        :param agent_id: The ID of the agent on which the execution is running
        :type agent_id: string
        :param job_exe: The job execution model, related fields will only have IDs populated
        :type job_exe: :class:`job.models.JobExecution`
        :param job_type: The job type model
        :type job_type: :class:`job.models.JobType`
        :param configuration: The job execution configuration, including secret values
        :type configuration: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        :param priority: The priority of the job execution
        :type priority: int
        """

        # Public, read-only info
        self.id = job_exe.id
        self.agent_id = agent_id
        self.cluster_id = job_exe.get_cluster_id()
        self.job_id = job_exe.job_id
        self.exe_num = job_exe.exe_num
        self.job_type_id = job_exe.job_type_id
        self.node_id = job_exe.node_id
        self.priority = priority
        self.queued = job_exe.queued
        self.started = job_exe.started
        self.docker_volumes = configuration.get_named_docker_volumes()

        # Keep job_exe model for generating job_exe_end model
        self._job_exe = job_exe

        # Internal task and status info
        self._lock = threading.Lock()  # Protects the following fields
        self._all_tasks = []
        self._current_task = None
        self._error = None
        self._finished = None
        self._has_been_starved = False
        self._last_task_finished = None
        self._remaining_tasks = []
        self._status = 'RUNNING'

        # Create tasks
        for task_type in configuration.get_task_types():
            task = None
            if task_type == 'pull':
                task = PullTask(agent_id, job_exe, job_type, configuration)
            elif task_type == 'pre':
                task = PreTask(agent_id, job_exe, job_type, configuration)
            elif task_type == 'main':
                task = MainTask(agent_id, job_exe, job_type, configuration)
            elif task_type == 'post':
                task = PostTask(agent_id, job_exe, job_type, configuration)
            self._all_tasks.append(task)
        for task in self._all_tasks:
            self._remaining_tasks.append(task)


    @property
    def current_task(self):
        """Returns the currently running task of the job execution, or None if no task is currently running

        :returns: The current task, possibly None
        :rtype: :class:`job.tasks.base_task.Task`
        """

        return self._current_task

    @property
    def error(self):
        """Returns this job execution's error, None if there is no error

        :returns: The error, possibly None
        :rtype: :class:`error.models.Error`
        """

        return self._error

    @property
    def error_category(self):
        """Returns the category of this job execution's error, None if there is no error

        :returns: The error category, possibly None
        :rtype: bool
        """

        if self._error:
            return self._error.category
        return None

    @property
    def finished(self):
        """When this job execution finished, possibly None

        :returns: When this job execution finished, possibly None
        :rtype: :class:`datetime.datetime`
        """

        return self._finished

    @property
    def status(self):
        """Returns the status of this job execution

        :returns: The status of the job execution
        :rtype: string
        """

        return self._status

    def check_for_starvation(self, when):
        """Checks this job execution to see if it has been starved of resources for its next task

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: Whether this job execution has been starved
        :rtype: bool
        """

        with self._lock:
            if self._has_been_starved:
                return self._has_been_starved

            if self._current_task or not self._remaining_tasks:
                return False

            if self._last_task_finished and when > self._last_task_finished + RESOURCE_STARVATION_THRESHOLD:
                self._has_been_starved = True
                error = get_builtin_error('resource-starvation')
                self._set_final_status('FAILED', when, error)
                logger.warning('Job execution %d has failed due to resource starvation', self.id)

            return self._has_been_starved

    def create_job_exe_end_model(self):
        """Creates and returns a job execution end model for this job execution. Caller must ensure that this job
        execution is finished before calling.

        :returns: The job execution end model
        :rtype: :class:`job.models.JobExecutionEnd`
        """

        task_results = TaskResults(do_validate=False)
        task_results.add_task_results(self._all_tasks)
        error_id = self._error.id if self._error else None

        return self._job_exe.create_job_exe_end_model(task_results, self._status, error_id, self._finished)

    def execution_canceled(self, when):
        """Cancels this job execution

        :param when: The time that the execution was canceled
        :type when: :class:`datetime.datetime`
        """

        with self._lock:
            if self._current_task:
                # Execution is canceled, so kill the current task
                self._current_task.force_kill()
            self._set_final_status('CANCELED', when)

    def execution_lost(self, when):
        """Fails this job execution for its node becoming lost

        :param when: The time that the node was lost
        :type when: :class:`datetime.datetime`
        """

        error = get_builtin_error('node-lost')

        with self._lock:
            if self._current_task:
                self._current_task.force_reconciliation()
            self._set_final_status('FAILED', when, error)

    def execution_timed_out(self, task, when):
        """Fails this job execution for timing out

        :param task: The task that timed out
        :type task: :class:`job.tasks.exe_task.JobExecutionTask`
        :param when: The time that the job execution timed out
        :type when: :class:`datetime.datetime`
        """

        if task.has_started:
            error_name = task.timeout_error_name
        else:
            error_name = 'launch-timeout'
        error = get_builtin_error(error_name)

        with self._lock:
            self._set_final_status('FAILED', when, error)

    def get_container_names(self):
        """Returns the list of container names for all tasks in this job execution

        :returns: The list of all container names
        :rtype: [string]
        """

        containers = []
        with self._lock:
            for task in self._all_tasks:
                if task.container_name:
                    containers.append(task.container_name)
            return containers

    def is_finished(self):
        """Indicates whether this job execution is finished with all tasks

        :returns: True if all tasks are finished, False otherwise
        :rtype: bool
        """

        with self._lock:
            return not self._current_task and not self._remaining_tasks

    def is_next_task_ready(self):
        """Indicates whether the next task in this job execution is ready

        :returns: True if the next task is ready, False otherwise
        :rtype: bool
        """

        with self._lock:
            return not self._current_task and self._remaining_tasks

    def next_task(self):
        """Returns the next task in this job execution. Returns None if there are no remaining tasks.

        :returns: The next task, possibly None
        :rtype: :class:`job.tasks.base_task.Task`
        """

        with self._lock:
            if not self._remaining_tasks:
                return None

            next_task = self._remaining_tasks[0]
            return next_task

    def start_next_task(self):
        """Starts the next task in the job execution and returns it. Returns None if the next task is not ready or no
        tasks remain.

        :returns: The new task that was started, possibly None
        :rtype: :class:`job.tasks.base_task.Task`
        """

        with self._lock:
            if self._current_task or not self._remaining_tasks:
                return None

            self._current_task = self._remaining_tasks.pop(0)
            return self._current_task

    def task_update(self, task_update):
        """Updates a task for this job execution

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        if task_update.status == TaskStatusUpdate.FINISHED:
            self._task_complete(task_update)
        elif task_update.status == TaskStatusUpdate.LOST:
            self._task_lost(task_update)
        elif task_update.status in [TaskStatusUpdate.FAILED, TaskStatusUpdate.KILLED]:
            self._task_fail(task_update)

    def _set_final_status(self, status, when, error=None):
        """Sets the final status for this job execution and removes all remaining tasks. The current task remains since
        it may need to be killed. Caller must have obtained lock.

        :param status: The status
        :type status: string
        :param when: The time that the job execution finished
        :type when: :class:`datetime.datetime`
        :param error: The error, possibly None
        :type error: :class:`error.models.Error`
        """

        if self._status == 'RUNNING':
            self._remaining_tasks = []
            self._status = status
            self._finished = when
            self._error = error

    def _task_complete(self, task_update):
        """Completes a task for this job execution

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if self._current_task and self._current_task.id == task_update.task_id:
                when = now()
                self._current_task = None
                self._last_task_finished = when
                if not self._remaining_tasks:
                    self._set_final_status('COMPLETED', when)

    def _task_fail(self, task_update):
        """Fails a task for this job execution

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if self._current_task and self._current_task.id == task_update.task_id:
                when = now()
                error = self._current_task.determine_error(task_update)
                if not error:
                    error = get_unknown_error()
                self._current_task = None
                self._last_task_finished = when
                self._set_final_status('FAILED', when, error)

    def _task_lost(self, task_update):
        """Tells this job execution that one of its tasks was lost

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if not self._current_task or self._current_task.id != task_update.task_id:
                return

            if self._status == 'RUNNING':
                # Re-run lost task with new task ID if the job execution is still running
                self._current_task.update_task_id_for_lost_task()  # Note: This changes the task ID!
                self._remaining_tasks.insert(0, self._current_task)
            self._current_task = None
            self._last_task_finished = now()
