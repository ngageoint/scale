"""Defines the class for a job execution pre-task"""
from __future__ import unicode_literals

import datetime

from error.exceptions import get_error_by_exit_code
from job.execution.tasks.exe_task import JobExecutionTask


PRE_TASK_COMMAND_ARGS = 'scale_pre_steps'


class PreTask(JobExecutionTask):
    """Represents a job execution pre-task. This class is thread-safe.
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

        super(PreTask, self).__init__(configuration.get_task_id('pre'), agent_id, job_exe, job_type)

        # Set base task fields
        self._uses_docker = True
        self._docker_image = self._create_scale_image_name()
        self._docker_params = configuration.get_docker_params('pre')
        self._is_docker_privileged = False
        self._command_arguments = configuration.get_args('pre')
        self._running_timeout_threshold = datetime.timedelta(hours=1)

        # Set job execution task fields
        self.timeout_error_name = 'pre-timeout'

        # Private fields for this class
        self._resources = configuration.get_resources('pre')

    def complete(self, task_update):
        """See :meth:`job.execution.tasks.exe_task.JobExecutionTask.complete`
        """

        with self._lock:
            if self._task_id != task_update.task_id:
                return

            # Support duplicate calls to complete(), task updates may repeat
            self._has_ended = True
            self._ended = task_update.timestamp
            self._exit_code = task_update.exit_code
            self._last_status_update = task_update.timestamp

            # The pre-task requires subsequent tasks to query the job execution again since the pre-task determines what
            # the command_arguments field will be
            return True

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

        return self._resources

    def populate_job_exe_model(self, job_exe):
        """See :meth:`job.execution.tasks.exe_task.JobExecutionTask.populate_job_exe_model`
        """

        with self._lock:
            if self._has_started:
                job_exe.pre_started = self._started
            if self._has_ended:
                job_exe.pre_completed = self._ended
                job_exe.pre_exit_code = self._exit_code
