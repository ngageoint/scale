"""Defines the class for a job execution job task"""
from __future__ import unicode_literals

import datetime

from error.exceptions import get_error_by_exit_code
from job.execution.tasks.exe_task import JobExecutionTask
from node.resources.node_resources import NodeResources
from node.resources.resource import Disk

JOB_TYPE_TIMEOUT_ERRORS = {}  # {Job type name: error name}


class JobTask(JobExecutionTask):
    """Represents a job execution job task (runs the actual job/algorithm). This class is thread-safe.
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(JobTask, self).__init__(job_exe.get_job_task_id(), job_exe)

        self._is_system = job_exe.job.job_type.is_system
        self._uses_docker = job_exe.uses_docker()
        if self._uses_docker:
            if self._is_system:
                self._docker_image = self._create_scale_image_name()
            else:
                self._docker_image = job_exe.get_docker_image()
            self._docker_params = job_exe.get_execution_configuration().get_job_task_docker_params()
            self._is_docker_privileged = job_exe.is_docker_privileged()
        self._command = job_exe.get_job_interface().get_command()
        self._command_arguments = job_exe.command_arguments
        if job_exe.job.job_type.is_long_running:
            self._running_timeout_threshold = None
        else:
            self._running_timeout_threshold = datetime.timedelta(seconds=job_exe.timeout)

        # Determine error to use if this task times out
        job_type_name = job_exe.job.job_type.name
        if job_type_name in JOB_TYPE_TIMEOUT_ERRORS:
            self.timeout_error_name = JOB_TYPE_TIMEOUT_ERRORS[job_type_name]
        else:
            self.timeout_error_name = 'system-timeout' if self._is_system else 'timeout'

    def determine_error(self, task_update):
        """See :meth:`job.execution.tasks.exe_task.JobExecutionTask.determine_error`
        """

        with self._lock:
            if self._task_id != task_update.task_id:
                return None

            error = None
            if self._is_system:
                # System job, check builtin errors
                if task_update.exit_code:
                    error = get_error_by_exit_code(task_update.exit_code)
            else:
                # TODO: in the future, don't use has_started flag to check for launch errors, use correct Mesos error
                # reason instead. This method is inaccurate if no TASK_RUNNING update happens to be received.
                if self._has_started:
                    # Use job's error mapping here to determine error
                    error = self._error_mapping.get_error(task_update.exit_code, 'algorithm-unknown')
            if not error:
                error = self._consider_general_error(task_update)

            return error

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        with self._lock:
            # Input files have already been written, only disk space for output files is required
            resources_without_input_files = self._resources.copy()
            resources_without_input_files.subtract(NodeResources([Disk(self._input_file_size)]))
            return resources_without_input_files

    def populate_job_exe_model(self, job_exe):
        """See :meth:`job.execution.tasks.exe_task.JobExecutionTask.populate_job_exe_model`
        """

        with self._lock:
            if self._has_started:
                job_exe.job_started = self._started
            if self._has_ended:
                job_exe.job_completed = self._ended
                job_exe.job_exit_code = self._exit_code

    def refresh_cached_values(self, job_exe):
        """Refreshes the task's cached job execution values with the given model

        :param job_exe: The job execution model
        :type job_exe: :class:`job.models.JobExecution`
        """

        with self._lock:
            self._command_arguments = job_exe.command_arguments
