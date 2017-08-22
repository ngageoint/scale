"""Defines the abstract base class for all job execution tasks"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

from error.models import Error
from job.tasks.base_task import Task


JOB_TASK_ID_PREFIX = 'scale_job'


class JobExecutionTask(Task):
    """Abstract base class for a job execution task
    """

    __metaclass__ = ABCMeta

    def __init__(self, task_id, agent_id, job_exe, job_type):
        """Constructor

        :param task_id: The unique ID of the task
        :type task_id: string
        :param agent_id: The ID of the agent on which the execution is running
        :type agent_id: string
        :param job_exe: The job execution model, related fields will only have IDs populated
        :type job_exe: :class:`job.models.JobExecution`
        :param job_type: The job type model
        :type job_type: :class:`job.models.JobType`
        """

        task_name = '%s %s' % (job_type.title, job_type.version)
        if not job_type.is_system:
            task_name = 'Scale %s' % task_name
        super(JobExecutionTask, self).__init__(task_id, task_name, agent_id)

        # Public, read-only info
        self.job_exe_id = job_exe.id

        # Internal job execution info
        self._base_task_id = task_id  # This is the base task ID in case this task gets lost
        self._lost_count = 0

        # Sub-classes should set this
        self.task_type = None
        self.timeout_error_name = None

    @abstractmethod
    def determine_error(self, task_update):
        """Attempts to determine the error that caused this task to fail

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        :returns: The error that caused this task to fail, possibly None
        :rtype: :class:`error.models.Error`
        """

        raise NotImplementedError()

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
                return Error.objects.get_error('docker-task-launch')
            else:
                return Error.objects.get_error('task-launch')
        else:
            if task_update.reason == 'REASON_EXECUTOR_TERMINATED' and self._uses_docker:
                return Error.objects.get_error('docker-terminated')
        return None
