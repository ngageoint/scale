"""Defines the class for a job execution pull-task"""
from __future__ import unicode_literals

import datetime

from error.models import Error
from job.execution.tasks.exe_task import JobExecutionTask
from job.tasks.pull_task import create_pull_command


class PullTask(JobExecutionTask):
    """Represents a job execution pull-task. This class is thread-safe.
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(PullTask, self).__init__(job_exe.get_pull_task_id(), job_exe)

        self._uses_docker = False
        self._docker_image = None
        self._docker_params = []
        self._is_docker_privileged = False
        self._running_timeout_threshold = datetime.timedelta(minutes=15)
        self._staging_timeout_threshold = datetime.timedelta(minutes=2)

        self.timeout_error_name = 'pull-timeout'
        self._command = create_pull_command(job_exe.get_docker_image())

    def determine_error(self, task_update):
        """See :meth:`job.execution.tasks.exe_task.JobExecutionTask.determine_error`
        """

        with self._lock:
            if self._task_id != task_update.task_id:
                return None

            return Error.objects.get_builtin_error('pull')

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        return self._resources
