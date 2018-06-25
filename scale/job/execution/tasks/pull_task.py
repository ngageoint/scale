"""Defines the class for a job execution pull-task"""
from __future__ import unicode_literals

import datetime

from error.models import get_builtin_error
from job.execution.tasks.exe_task import JobExecutionTask


class PullTask(JobExecutionTask):
    """Represents a job execution pull-task. This class is thread-safe.
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
        :type configuration: :class:`job.execution.configuration.json.exe_config.ExecutionConfiguration`
        """

        super(PullTask, self).__init__(configuration.get_task_id('pull'), agent_id, job_exe, job_type)

        # Set base task fields
        self._uses_docker = False
        self._docker_image = None
        self._docker_params = []
        self._is_docker_privileged = False
        self._command = configuration.get_args('pull')
        self._running_timeout_threshold = datetime.timedelta(minutes=30)

        # Set job execution task fields
        self.task_type = 'pull'
        self.timeout_error_name = 'pull-timeout'

        # Private fields for this class
        self._resources = configuration.get_resources('pull')

    def determine_error(self, task_update):
        """See :meth:`job.execution.tasks.exe_task.JobExecutionTask.determine_error`
        """

        with self._lock:
            if self._task_id != task_update.task_id:
                return None

            return get_builtin_error('pull')

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        return self._resources
