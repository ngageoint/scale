"""Defines the class for a job execution job task"""
from __future__ import unicode_literals

import datetime

from error.exceptions import get_error_by_exit_code
from job.execution.tasks.exe_task import JobExecutionTask


JOB_TYPE_TIMEOUT_ERRORS = {}  # {Job type name: error name}


class MainTask(JobExecutionTask):
    """Represents a job execution main task (runs the actual job/algorithm). This class is thread-safe.
    """

    def __init__(self, agent_id, job_exe, job_type, configuration):
        """Constructor

        :param agent_id: The ID of the agent on which the execution is running
        :type agent_id: string
        :param job_exe: The job execution model, related fields will only have IDs populated
        :type job_exe: :class:`job.models.JobExecution`
        :param job_type: The job type model
        :type job_type: :class:`job.models.JobType`
        :param configuration: The job execution configuration, including secret values
        :type configuration: :class:`job.configuration.json.execution.exe_config.ExecutionConfiguration`
        """

        super(MainTask, self).__init__(configuration.get_task_id('main'), agent_id, job_exe, job_type)

        # Set base task fields
        self._is_system = job_type.is_system
        self._uses_docker = job_type.uses_docker
        if self._uses_docker:
            if self._is_system:
                self._docker_image = self._create_scale_image_name()
            else:
                self._docker_image = job_type.docker_image
            self._docker_params = configuration.get_docker_params('main')
            self._is_docker_privileged = job_type.docker_privileged
        self._command_arguments = configuration.get_args('main')
        if job_type.is_long_running:
            self._running_timeout_threshold = None
        else:
            self._running_timeout_threshold = datetime.timedelta(seconds=job_exe.timeout)

        # Set job execution task fields
        # Determine error to use if this task times out
        if job_type.name in JOB_TYPE_TIMEOUT_ERRORS:
            self.timeout_error_name = JOB_TYPE_TIMEOUT_ERRORS[job_type.name]
        else:
            self.timeout_error_name = 'system-timeout' if self._is_system else 'timeout'

        # Private fields for this class
        self._error_mapping = job_type.get_error_interface()
        self._resources = configuration.get_resources('main')

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

        return self._resources
