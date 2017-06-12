"""Defines the abstract base class for all job execution tasks"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

from error.models import Error
from job.tasks.base_task import Task


JOB_TASK_ID_PREFIX = 'scale_job'


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

        self._base_task_id = task_id  # This is the base task ID in case this task gets lost
        self._lost_count = 0

        self.timeout_error_name = None  # Sub-classes should set this

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

        return self._job_exe_id

    def complete(self, task_update):
        """Completes this task and indicates whether following tasks should update their cached job execution values

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        :returns: True if following tasks should update their cached job execution values, False otherwise
        :rtype: bool
        """

        with self._lock:
            if self._task_id != task_update.task_id:
                return

            # Support duplicate calls to complete(), task updates may repeat
            self._has_ended = True
            self._ended = task_update.timestamp
            self._exit_code = task_update.exit_code
            self._last_status_update = task_update.timestamp

            return False

    @abstractmethod
    def determine_error(self, task_update):
        """Attempts to determine the error that caused this task to fail

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
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

    def update_task_id_for_lost_task(self):
        """Updates this task's ID due to the task being lost. A new, unique ID will prevent race conditions where Scale
        confuses this task with the previous lost task.
        """

        with self._lock:
            self._lost_count += 1
            self._task_id = '%s_lost-%d' % (self._base_task_id, self._lost_count)

    def _consider_general_error(self, task_update):
        """Looks at the task update and considers a general task error for the cause of the failure. This is the
        'catch-all' option for specific task types (pre, job, post) to try if they cannot determine a specific error. If
        this method cannot determine an error cause, None will be returned. Caller must have obtained the task lock.

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        :returns: The error that caused this task to fail, possibly None
        :rtype: :class:`error.models.Error`
        """

        # TODO: in the future, don't use has_started flag to check for launch errors, use correct Mesos error reason
        # instead. This method is inaccurate if no TASK_RUNNING update happens to be received.
        if not self._has_started:
            if self._uses_docker:
                return Error.objects.get_builtin_error('docker-task-launch')
            else:
                return Error.objects.get_builtin_error('task-launch')
        else:
            if task_update.reason == 'REASON_EXECUTOR_TERMINATED' and self._uses_docker:
                return Error.objects.get_builtin_error('docker-terminated')
        return None
