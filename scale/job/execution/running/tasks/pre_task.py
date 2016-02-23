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

    def complete(self, task_results):
        """See :meth:`job.execution.running.tasks.base_task.Task.complete`
        """

        if self._task_id != task_results.task_id:
            return

        JobExecution.objects.pre_steps_completed(self._job_exe_id, task_results.when, task_results.exit_code,
                                                 task_results.stdout, task_results.stderr)
        JobExecution.objects.set_log_urls(self._job_exe_id, None, None)

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
            if task_results.exit_code in PRE_EXIT_CODE_DICT:
                error = PRE_EXIT_CODE_DICT[task_results.exit_code]()

        JobExecution.objects.pre_steps_failed(self._job_exe_id, task_results.when, task_results.exit_code,
                                              task_results.stdout, task_results.stderr)
        JobExecution.objects.set_log_urls(self._job_exe_id, None, None)

        return error

    def running(self, when, stdout_url, stderr_url):
        """See :meth:`job.execution.running.tasks.base_task.Task.running`
        """

        JobExecution.objects.pre_steps_started(self._job_exe_id, when)
        JobExecution.objects.set_log_urls(self._job_exe_id, stdout_url, stderr_url)
