'''Defines the manager for handling the tasks within a job execution'''
from __future__ import unicode_literals

import threading

from job.models import JobExecution


class JobExeTaskManager(object):
    '''This class manages the tasks that make up a running job execution. This class is thread-safe.
    '''

    # TODO: need this?
    @staticmethod
    def get_job_exe_id(task_id):
        '''Returns the job execution ID for the given task ID

        :param task_id: The task ID
        :type task_id: str
        :returns: The job execution ID
        :rtype: int
        '''

        return int(task_id.split('_')[0])

    def __init__(self, job_exe, task_factory):
        '''Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, job_type, and
            job_type_rev models populated
        :type job_exe: :class:`job.models.JobExecution`
        :param task_factory: The factory to use for creating the job execution tasks
        :type task_factory: :class:`job.execution.tasks.TaskFactory`
        '''

        # Keep job execution values that should not change over time
        self._job_exe_id = job_exe.id
        self._job_type_name = job_exe.get_job_type_name()
        self._cpus = job_exe.cpus_scheduled
        self._mem = job_exe.mem_scheduled
        self._disk_in = job_exe.disk_in_scheduled
        self._disk_out = job_exe.disk_out_scheduled
        self._disk_total = job_exe.disk_total_scheduled

        self._current_task = None
        self._remaining_tasks = []
        self._lock = threading.Lock()

        # Create tasks
        pre_task_id = None
        if not job_exe.is_system():
            pre_task = task_factory.create_pre_task(job_exe)
            pre_task_id = pre_task.get_id()
            self._remaining_tasks.append(pre_task)

        job_task = task_factory.create_job_task(job_exe)
        job_task_id = job_task.get_id()
        self._remaining_tasks.append(job_task)

        post_task_id = None
        if not job_exe.is_system():
            post_task = task_factory.create_post_task(job_exe)
            post_task_id = post_task.get_id()
            self._remaining_tasks.append(post_task)

        JobExecution.objects.set_task_ids(self._job_exe_id, pre_task_id, job_task_id, post_task_id)

    def __repr__(self):
        return '<JobExeTaskManager: %r %r>' % (self._job_exe_id, self._job_type_name)

    def get_current_task(self):
        '''Returns the current task for this job execution

        :returns: The current task, possibly None
        :rtype: :class:`job.execution.tasks.Task`
        '''

        with self._lock:
            return self._current_task

    def is_finished(self):
        '''Indicates whether this job execution is finished with all tasks

        :returns: True if all tasks are finished, False otherwise
        :rtype: bool
        '''

        with self._lock:
            return not self._current_task and not self._remaining_tasks

    def is_next_task_ready(self, resources):
        '''Indicates whether the next task for this job execution is ready and able to run with the given node resources

        :param resources: The available node resources
        :type resources: :class:`job.resources.NodeResources`
        :returns: True if the next task is ready, False otherwise
        :rtype: bool
        '''

        with self._lock:
            if self._current_task:
                # Still currently running a task
                return False

            if not self._remaining_tasks:
                # No more tasks remaining
                return False

            next_task = self._remaining_tasks[0]
            return next_task.are_resources_enough(resources)

    def start_next_task(self, resources):
        '''Starts the next task for this job execution and returns it. Returns None if the next task could not be
        started.

        :param resources: The available node resources
        :type resources: :class:`job.resources.NodeResources`
        :returns: The next task that was just started
        :rtype: :class:`job.execution.tasks.Task`
        '''

        with self._lock:
            if not self.is_next_task_ready(resources):
                return None

            self._current_task = self._remaining_tasks.pop(0)

            return self._current_task
