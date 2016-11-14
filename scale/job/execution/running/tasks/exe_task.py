"""Defines the abstract base class for all job execution tasks"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

from django.conf import settings

from error.models import Error
from job.execution.running.tasks.base_task import Task


class JobExecutionTask(Task):
    """Abstract base class for a job execution task. A job execution consists of three tasks: the pre-task,
    the job-task, and the post-task.
    """

    __metaclass__ = ABCMeta

    def __init__(self, task_id, job_exe):
        """Constructor

        :param task_id: The unique ID of the task
        :type task_id: string
        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, job_type, and
            job_type_rev models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        task_name = '%s %s' % (job_exe.job.job_type.title, job_exe.job.job_type.version)
        if not job_exe.is_system:
            task_name = 'Scale %s' % task_name
        super(JobExecutionTask, self).__init__(task_id, task_name, job_exe.node.slave_id)

        # Keep job execution values that should not change
        self._job_exe_id = job_exe.id
        self._cpus = job_exe.cpus_scheduled
        self._mem = job_exe.mem_scheduled
        self._disk_in = job_exe.disk_in_scheduled
        self._disk_out = job_exe.disk_out_scheduled
        self._disk_total = job_exe.disk_total_scheduled
        self._error_mapping = job_exe.get_error_interface()  # This can change, but not worth re-queuing

    @property
    def job_exe_id(self):
        """Returns the job execution ID of the task

        :returns: The job execution ID
        :rtype: int
        """

        with self._lock:
            return self._job_exe_id

    def complete(self, task_results):
        """Completes this task and indicates whether following tasks should update their cached job execution values

        :param task_results: The task results
        :type task_results: :class:`job.execution.running.tasks.results.TaskResults`
        :returns: True if following tasks should update their cached job execution values, False otherwise
        :rtype: bool
        """

        with self._lock:
            if self._task_id != task_results.task_id:
                return

            # Support duplicate calls to complete(), task updates may repeat
            self._has_ended = True
            self._ended = task_results.when
            self._last_status_update = task_results.when

            return False

    def consider_general_error(self, task_results):
        """Looks at the task results and considers a general task error for the cause of the failure. This is the
        'catch-all' option for specific task types (pre, job, post) to try if they cannot determine a specific error. If
        this method cannot determine an error cause, None will be returned.

        :param task_results: The task results
        :type task_results: :class:`job.execution.running.tasks.results.TaskResults`
        :returns: The error that caused this task to fail, possibly None
        :rtype: :class:`error.models.Error`
        """

        with self._lock:
            if not self._has_started:
                if self._uses_docker:
                    return Error.objects.get_builtin_error('docker-task-launch')
                else:
                    return Error.objects.get_builtin_error('task-launch')
            return None

    def create_scale_image_name(self):
        """Creates the full image name to use for running the Scale Docker image

        :returns: The full Scale Docker image name
        :rtype: string
        """

        return '%s:%s' % (settings.SCALE_DOCKER_IMAGE, settings.DOCKER_VERSION)

    @abstractmethod
    def fail(self, task_results, error=None):
        """Fails this task, possibly returning error information

        :param task_results: The task results
        :type task_results: :class:`job.execution.running.tasks.results.TaskResults`
        :param error: The error that caused this task to fail, possibly None
        :type error: :class:`error.models.Error`
        :returns: The error that caused this task to fail, possibly None
        :rtype: :class:`error.models.Error`
        """

        raise NotImplementedError()

    @abstractmethod
    def populate_job_exe_model(self, job_exe):
        """Populates the job execution model with the relevant information from this task

        :param job_exe: The job execution model
        :type job_exe: :class:`job.models.JobExecution`
        """

        raise NotImplementedError()

    def refresh_cached_values(self, job_exe):
        """Refreshes the task's cached job execution values with the given model

        :param job_exe: The job execution model
        :type job_exe: :class:`job.models.JobExecution`
        """

        pass

    def start(self, when):
        """Starts this task and marks it as running

        :param when: The time that the task started running
        :type when: :class:`datetime.datetime`
        """

        with self._lock:
            if self._has_ended:
                raise Exception('Trying to start a task that has already ended')

            # Support duplicate calls to start(), task updates may repeat
            self._has_started = True
            self._started = when
            self._last_status_update = when
