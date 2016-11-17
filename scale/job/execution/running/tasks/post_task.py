"""Defines the class for a job execution post-task"""
from __future__ import unicode_literals

from job.execution.running.tasks.exe_task import JobExecutionTask
from job.management.commands.scale_post_steps import EXIT_CODE_DICT as POST_EXIT_CODE_DICT
from job.resources import NodeResources


class PostTask(JobExecutionTask):
    """Represents a job execution post-task. This class is thread-safe.
    """

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        super(PostTask, self).__init__(job_exe.get_post_task_id(), job_exe)

        self._uses_docker = True
        self._docker_image = self.create_scale_image_name()
        self._docker_params = job_exe.get_job_configuration().get_post_task_docker_params()
        self._is_docker_privileged = False
        self._command_arguments = 'scale_post_steps -i %i' % job_exe.id

    def get_resources(self):
        """See :meth:`job.execution.running.tasks.base_task.Task.get_resources`
        """

        with self._lock:
            # Post task does not require any local disk space
            return NodeResources(cpus=self._cpus, mem=self._mem)

    def fail(self, task_results, error=None):
        """See :meth:`job.execution.running.tasks.base_task.Task.fail`
        """

        with self._lock:
            if self._task_id != task_results.task_id:
                return None

            # Support duplicate calls to fail(), task updates may repeat
            if not error and self._has_started:
                # Check scale_post_steps command to see if exit code maps to a specific error
                if task_results.exit_code and task_results.exit_code in POST_EXIT_CODE_DICT:
                    error = POST_EXIT_CODE_DICT[task_results.exit_code]()
            if not error:
                error = self._consider_general_error(task_results)

            self._has_ended = True
            self._ended = task_results.when
            self._last_status_update = task_results.when
            self._exit_code = task_results.exit_code

            return error

    def populate_job_exe_model(self, job_exe):
        """See :meth:`job.execution.running.tasks.base_task.Task.populate_job_exe_model`
        """

        with self._lock:
            if self._has_started:
                job_exe.post_started = self._started
            if self._has_ended:
                job_exe.post_completed = self._ended
                job_exe.post_exit_code = self._exit_code
