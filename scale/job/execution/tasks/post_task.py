"""Defines the class for a job execution post-task"""
from __future__ import unicode_literals

import datetime

from error.exceptions import get_error_by_exit_code
from job.execution.tasks.exe_task import JobExecutionTask
from job.resources import NodeResources


class PostTask(JobExecutionTask):
    """Represents a job execution post-task. This class is thread-safe.
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(PostTask, self).__init__(job_exe.get_post_task_id(), job_exe)

        self._uses_docker = True
        self._docker_image = self._create_scale_image_name()
        self._force_docker_pull = False
        self._docker_params = job_exe.get_execution_configuration().get_post_task_docker_params()
        self._is_docker_privileged = False
        self._command_arguments = 'scale_post_steps -i %i' % job_exe.id
        self._running_timeout_threshold = datetime.timedelta(hours=1)
        self.timeout_error_name = 'post-timeout'

    def determine_error(self, task_update):
        """See :meth:`job.execution.tasks.exe_task.JobExecutionTask.determine_error`
        """

        with self._lock:
            if self._task_id != task_update.task_id:
                return None

            error = None
            if self._has_started:
                # Check to see if exit code maps to a specific error
                if task_update.exit_code:
                    error = get_error_by_exit_code(task_update.exit_code)
            if not error:
                error = self._consider_general_error(task_update)

            return error

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        with self._lock:
            # Post task does not require any local disk space
            return NodeResources(cpus=self._cpus, mem=self._mem)

    def populate_job_exe_model(self, job_exe):
        """See :meth:`job.execution.tasks.exe_task.JobExecutionTask.populate_job_exe_model`
        """

        with self._lock:
            if self._has_started:
                job_exe.post_started = self._started
            if self._has_ended:
                job_exe.post_completed = self._ended
                job_exe.post_exit_code = self._exit_code
