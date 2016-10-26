"""Defines the class for a job execution pre-task"""
from __future__ import unicode_literals

from job.execution.running.tasks.base_task import Task
from job.management.commands.scale_pre_steps import EXIT_CODE_DICT as PRE_EXIT_CODE_DICT
from job.resources import NodeResources


class PreTask(Task):
    """Represents a job execution pre-task
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

    def complete(self, task_results):
        """See :meth:`job.execution.running.tasks.base_task.Task.complete`
        """

        if self._task_id != task_results.task_id:
            return

        # Support duplicate calls to complete(), task updates may repeat
        self._has_ended = True
        self._results = task_results

        # The pre-task requires subsequent tasks to query the job execution again since the pre-task determines what the
        # command_arguments field will be
        return True

    def get_resources(self):
        """See :meth:`job.execution.running.tasks.base_task.Task.get_resources`
        """

        return NodeResources(cpus=self._cpus, mem=self._mem, disk=self._disk_total)

    def fail(self, task_results, error=None):
        """See :meth:`job.execution.running.tasks.base_task.Task.fail`
        """

        if self._task_id != task_results.task_id:
            return None

        # Support duplicate calls to fail(), task updates may repeat
        if not error and self._has_started:
            # Check scale_pre_steps command to see if exit code maps to a specific error
            if task_results.exit_code and task_results.exit_code in PRE_EXIT_CODE_DICT:
                error = PRE_EXIT_CODE_DICT[task_results.exit_code]()
        if not error:
            error = self.consider_general_error(task_results)

        self._has_ended = True
        self._results = task_results

        return error

    def populate_job_exe_model(self, job_exe):
        """See :meth:`job.execution.running.tasks.base_task.Task.populate_job_exe_model`
        """

        if self._has_started:
            job_exe.pre_started = self._started
        if self._has_ended:
            job_exe.pre_completed = self._results.when
            job_exe.pre_exit_code = self._results.exit_code
