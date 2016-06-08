"""Defines the class for a job execution pre-task"""
from __future__ import unicode_literals

from job.execution.running.tasks.base_task import Task
from job.management.commands.scale_pre_steps import EXIT_CODE_DICT as PRE_EXIT_CODE_DICT
from job.models import JobExecution
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

        super(PreTask, self).__init__('%i_pre' % job_exe.id, job_exe)

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

        JobExecution.objects.task_ended(self._job_exe_id, 'pre', task_results.when, task_results.exit_code,
                                        task_results.stdout, task_results.stderr)

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

        if not error:
            # Check scale_pre_steps command to see if exit code maps to a specific error
            if task_results.exit_code and task_results.exit_code in PRE_EXIT_CODE_DICT:
                error = PRE_EXIT_CODE_DICT[task_results.exit_code]()
        if not error:
            error = self.consider_general_error(task_results)

        JobExecution.objects.task_ended(self._job_exe_id, 'pre', task_results.when, task_results.exit_code,
                                        task_results.stdout, task_results.stderr)

        return error

    def running(self, when, stdout_url, stderr_url):
        """See :meth:`job.execution.running.tasks.base_task.Task.running`
        """

        super(PreTask, self).running(when, stdout_url, stderr_url)
        JobExecution.objects.task_started(self._job_exe_id, 'pre', when, stdout_url, stderr_url)
