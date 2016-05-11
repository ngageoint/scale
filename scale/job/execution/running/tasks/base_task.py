"""Defines the abstract base class for all job execution tasks"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

from django.conf import settings

from error.models import Error


class Task(object):
    """Abstract base class for a job execution task
    """

    __metaclass__ = ABCMeta

    def __init__(self, task_id, job_exe):
        """Constructor

        :param task_id: The unique ID of the task
        :type task_id: str
        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, job_type, and
            job_type_rev models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        self._task_id = task_id
        self._task_name = 'Job Execution %i (%s)' % (job_exe.id, job_exe.get_job_type_name())
        self._is_running = False

        # Keep job execution values that should not change
        self._job_exe_id = job_exe.id
        self._cpus = job_exe.cpus_scheduled
        self._mem = job_exe.mem_scheduled
        self._disk_in = job_exe.disk_in_scheduled
        self._disk_out = job_exe.disk_out_scheduled
        self._disk_total = job_exe.disk_total_scheduled
        self._error_mapping = job_exe.get_error_interface()  # This can change, but not worth re-queuing

        # Keep node values that should not change
        self._agent_id = job_exe.node.slave_id

        # These values will vary by different task subclasses
        self._uses_docker = False
        self._docker_image = None
        self._docker_params = []
        self._is_docker_privileged = False
        self._command = None
        self._command_arguments = None

    @property
    def agent_id(self):
        """Returns the ID of the agent that the task is running on

        :returns: The agent ID
        :rtype: str
        """

        return self._agent_id

    @property
    def command(self):
        """Returns the command to execute for the task

        :returns: The command to execute
        :rtype: str
        """

        return self._command

    @property
    def command_arguments(self):
        """Returns the command to execute for the task

        :returns: The command to execute
        :rtype: str
        """

        return self._command_arguments

    @property
    def docker_image(self):
        """Returns the name of the Docker image to run for this task, possibly None

        :returns: The Docker image name
        :rtype: str
        """

        return self._docker_image

    @property
    def docker_params(self):
        """Returns the Docker parameters used to run this task

        :returns: The Docker parameters
        :rtype: [:class:`job.configuration.configuration.job_configuration.DockerParam`]
        """

        return self._docker_params

    @property
    def id(self):
        """Returns the unique ID of the task

        :returns: The task ID
        :rtype: str
        """

        return self._task_id

    @property
    def is_docker_privileged(self):
        """Indicates whether this task's Docker container should be run in privileged mode

        :returns: True if the container should be run in privileged mode, False otherwise
        :rtype: bool
        """

        return self._is_docker_privileged

    @property
    def is_running(self):
        """Indicates whether this task is currently running

        :returns: True if the task is running, False otherwise
        :rtype: bool
        """

        return self._is_running

    @property
    def job_exe_id(self):
        """Returns the job execution ID of the task

        :returns: The job execution ID
        :rtype: int
        """

        return self._job_exe_id

    @property
    def name(self):
        """Returns the name of the task

        :returns: The task name
        :rtype: str
        """

        return self._task_name

    @property
    def uses_docker(self):
        """Indicates whether this task uses Docker or not

        :returns: True if this task uses Docker, False otherwise
        :rtype: bool
        """

        return self._uses_docker

    @abstractmethod
    def complete(self, task_results):
        """Completes this task and indicates whether following tasks should update their cached job execution values

        :param task_results: The task results
        :type task_results: :class:`job.execution.running.tasks.results.TaskResults`
        :returns: True if following tasks should update their cached job execution values, False otherwise
        :rtype: bool
        """

        raise NotImplementedError()

    def consider_general_error(self, task_results):
        """Looks at the task results and considers a general task error for the cause of the failure. This is the
        'catch-all' option for specific task types (pre, job, post) to try if they cannot determine a specific error. If
        this method cannot determine an error cause, None will be returned.

        :param task_results: The task results
        :type task_results: :class:`job.execution.running.tasks.results.TaskResults`
        :returns: The error that caused this task to fail, possibly None
        :rtype: :class:`error.models.Error`
        """

        if not self.is_running and not task_results.exit_code:
            if self.uses_docker:
                return Error.objects.get_builtin_error('docker-task-launch')
            else:
                return Error.objects.get_builtin_error('task-launch')
        return None

    def create_scale_image_name(self):
        """Creates the full image name to use for running the Scale Docker image

        :returns: The full Scale Docker image name
        :rtype: string
        """

        # Docker tags do not support the + character, so we replace it with _
        return '%s:%s' % (settings.SCALE_DOCKER_IMAGE, settings.VERSION.replace("+", "_"))

    @abstractmethod
    def get_resources(self):
        """Returns the resources that are required/have been scheduled for this task

        :returns: The scheduled resources for this task
        :rtype: :class:`job.resources.NodeResources`
        """

        raise NotImplementedError()

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

    def refresh_cached_values(self, job_exe):
        """Refreshes the task's cached job execution values with the given model

        :param job_exe: The job execution model
        :type job_exe: :class:`job.models.JobExecution`
        """

        pass

    def running(self, when, stdout_url, stderr_url):
        """Marks this task as having started running

        :param when: The time that the task started running
        :type when: :class:`datetime.datetime`
        :param stdout_url: The URL for the task's stdout logs
        :type stdout_url: str
        :param stderr_url: The URL for the task's stderr logs
        :type stderr_url: str
        """

        self._is_running = True
