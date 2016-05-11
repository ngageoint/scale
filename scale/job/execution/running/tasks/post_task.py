"""Defines the class for a job execution post-task"""
from __future__ import unicode_literals

from job.execution.running.tasks.base_task import Task
from job.management.commands.scale_post_steps import EXIT_CODE_DICT as POST_EXIT_CODE_DICT
from job.models import JobExecution
from job.resources import NodeResources


class PostTask(Task):
    """Represents a job execution post-task
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(PostTask, self).__init__('%i_post' % job_exe.id, job_exe)

        self._uses_docker = True
        self._docker_image = self.create_scale_image_name()
        self._docker_params = job_exe.get_job_configuration().get_post_task_docker_params()
        self._is_docker_privileged = False
        self._command_arguments = 'scale_post_steps -i %i' % job_exe.id

    def complete(self, task_results):
        """See :meth:`job.execution.running.tasks.base_task.Task.complete`
        """

        if self._task_id != task_results.task_id:
            return

        JobExecution.objects.task_ended(self._job_exe_id, 'post', task_results.when, task_results.exit_code,
                                        task_results.stdout, task_results.stderr)

        return False

    def get_resources(self):
        """See :meth:`job.execution.running.tasks.base_task.Task.get_resources`
        """

        # Post task does not require any local disk space
        return NodeResources(cpus=self._cpus, mem=self._mem)

    def fail(self, task_results, error=None):
        """See :meth:`job.execution.running.tasks.base_task.Task.fail`
        """

        if self._task_id != task_results.task_id:
            return None

        if not error:
            # Check scale_post_steps command to see if exit code maps to a specific error
            if task_results.exit_code and task_results.exit_code in POST_EXIT_CODE_DICT:
                error = POST_EXIT_CODE_DICT[task_results.exit_code]()
        if not error:
            error = self.consider_general_error(task_results)

        JobExecution.objects.task_ended(self._job_exe_id, 'post', task_results.when, task_results.exit_code,
                                        task_results.stdout, task_results.stderr)

        return error

    def running(self, when, stdout_url, stderr_url):
        """See :meth:`job.execution.running.tasks.base_task.Task.running`
        """

        super(PostTask, self).running(when, stdout_url, stderr_url)
        JobExecution.objects.task_started(self._job_exe_id, 'post', when, stdout_url, stderr_url)
