"""Defines the class for a job execution pre-task"""
from __future__ import unicode_literals

from job.execution.tasks.exe_task import JobExecutionTask
from job.management.commands.scale_pre_steps import EXIT_CODE_DICT as PRE_EXIT_CODE_DICT
from job.resources import NodeResources


class PreTask(JobExecutionTask):
    """Represents a job execution pre-task. This class is thread-safe.
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(PreTask, self).__init__(job_exe.get_pre_task_id(), job_exe)

        self._uses_docker = True
        self._docker_image = self.create_scale_image_name()
        self._docker_params = job_exe.get_job_configuration().get_pre_task_docker_params()
        self._is_docker_privileged = False
        self._command_arguments = 'scale_pre_steps -i %i' % job_exe.id

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
                # Check scale_pre_steps command to see if exit code maps to a specific error
                if task_update.exit_code and task_update.exit_code in PRE_EXIT_CODE_DICT:
                    error = PRE_EXIT_CODE_DICT[task_update.exit_code]()
            if not error:
                error = self._consider_general_error(task_update)

            return error

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        with self._lock:
            return NodeResources(cpus=self._cpus, mem=self._mem, disk=self._disk_total)

    def populate_job_exe_model(self, job_exe):
        """See :meth:`job.execution.tasks.exe_task.JobExecutionTask.populate_job_exe_model`
        """

        with self._lock:
            if self._has_started:
                job_exe.pre_started = self._started
            if self._has_ended:
                job_exe.pre_completed = self._ended
                job_exe.pre_exit_code = self._exit_code
