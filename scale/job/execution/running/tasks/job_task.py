"""Defines the class for a job execution job task"""
from __future__ import unicode_literals

from job.execution.running.tasks.base_task import Task
from job.models import JobExecution
from job.resources import NodeResources


class JobTask(Task):
    """Represents a job execution job task (runs the actual job/algorithm)
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(JobTask, self).__init__('%i_job' % job_exe.id, job_exe)

    def complete(self, task_results):
        """See :meth:`job.execution.running.tasks.base_task.Task.complete`
        """

        if self._task_id != task_results.task_id:
            return

        JobExecution.objects.job_completed(self._job_exe_id, task_results.when, task_results.exit_code,
                                           task_results.stdout, task_results.stderr, None)
        JobExecution.objects.set_log_urls(self._job_exe_id, None, None)

    def get_resources(self):
        """See :meth:`job.execution.running.tasks.base_task.Task.get_resources`
        """

        # Input files have already been written, only disk space for output files is required
        return NodeResources(cpus=self._cpus, mem=self._mem, disk=self._disk_out)

    def fail(self, task_results, error=None):
        """See :meth:`job.execution.running.tasks.base_task.Task.fail`
        """

        if self._task_id != task_results.task_id:
            return None

        if not error:
            # Use job's error mapping here to determine error
            error = self._error_mapping.get_error(task_results.exit_code)

        JobExecution.objects.job_failed(self._job_exe_id, task_results.when, task_results.exit_code,
                                        task_results.stdout, task_results.stderr)
        JobExecution.objects.set_log_urls(self._job_exe_id, None, None)

        return error

    def running(self, when, stdout_url, stderr_url):
        """See :meth:`job.execution.running.tasks.base_task.Task.running`
        """

        JobExecution.objects.job_started(self._job_exe_id, when)
        JobExecution.objects.set_log_urls(self._job_exe_id, stdout_url, stderr_url)
