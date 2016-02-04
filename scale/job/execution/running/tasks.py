'''Defines the classes for the tasks that make up a job execution'''
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

from job.resources import NodeResources


class Task(object):
    '''Abstract base class for a job execution task
    '''

    __metaclass__ = ABCMeta

    def __init__(self, task_id, job_exe):
        '''Constructor

        :param task_id: The unique ID of the task
        :type task_id: str
        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, job_type, and
            job_type_rev models populated
        :type job_exe: :class:`job.models.JobExecution`
        '''

        self._task_id = task_id

        # Keep job execution values that should not change over time
        self._job_exe_id = job_exe.id
        self._cpus = job_exe.cpus_scheduled
        self._mem = job_exe.mem_scheduled
        self._disk_in = job_exe.disk_in_scheduled
        self._disk_out = job_exe.disk_out_scheduled
        self._disk_total = job_exe.disk_total_scheduled

    def are_resources_enough(self, resources):
        '''Indicates whether the given node resources are sufficient to run the task

        :param resources: The available node resources
        :type resources: :class:`job.resources.NodeResources`
        :returns: True if the resources are enough to run this task, False otherwise
        :rtype: bool
        '''

        required_resources = self.get_resources()
        enough_cpus = resources.cpus >= required_resources.cpus
        enough_mem = resources.mem >= required_resources.mem
        enough_disk = resources.disk >= required_resources.disk

        return enough_cpus and enough_mem and enough_disk

    def get_id(self):
        '''Returns the unique ID of the task

        :returns: The task ID
        :rtype: str
        '''

        return self._task_id

    @abstractmethod
    def get_resources(self):
        '''Returns the resources that are required/have been scheduled for this task

        :returns: The scheduled resources for this task
        :rtype: :class:`job.resources.NodeResources`
        '''

        raise NotImplementedError()


class JobTask(Task):
    '''Represents a job execution job task (runs the actual job/algorithm)
    '''

    def __init__(self, job_exe):
        '''Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        '''

        super(JobTask, self).__init__('%i_job' % job_exe.id, job_exe)

    def get_resources(self):
        '''See :meth:`job.execution.tasks.Task.get_resources`
        '''

        return NodeResources(cpus=self._cpus, mem=self._mem, disk=self._disk_out)


class PostTask(Task):
    '''Represents a job execution post-task
    '''

    def __init__(self, job_exe):
        '''Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        '''

        super(PostTask, self).__init__('%i_post' % job_exe.id, job_exe)

    def get_resources(self):
        '''See :meth:`job.execution.tasks.Task.get_resources`
        '''

        return NodeResources(cpus=self._cpus, mem=self._mem)


class PreTask(Task):
    '''Represents a job execution pre-task
    '''

    def __init__(self, job_exe):
        '''Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
        models populated
        :type job_exe: :class:`job.models.JobExecution`
        '''

        super(PreTask, self).__init__('%i_pre' % job_exe.id, job_exe)

    def get_resources(self):
        '''See :meth:`job.execution.tasks.Task.get_resources`
        '''

        return NodeResources(cpus=self._cpus, mem=self._mem, disk=self._disk_total)


class TaskFactory(object):
    '''A factory that produces the tasks for a task manager. This class can be overridden to produce custom task
    implementations.
    '''

    def create_job_task(self, job_exe):
        '''Creates and returns a job-task for the given job execution

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
            models populated
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The job execution job-task
        :rtype: :class:`job.execution.tasks.JobTask`
        '''

        return JobTask(job_exe)

    def create_post_task(self, job_exe):
        '''Creates and returns a post-task for the given job execution

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
            models populated
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The job execution post-task
        :rtype: :class:`job.execution.tasks.PostTask`
        '''

        return PostTask(job_exe)

    def create_pre_task(self, job_exe):
        '''Creates and returns a pre-task for the given job execution

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, and job_type
            models populated
        :type job_exe: :class:`job.models.JobExecution`
        :returns: The job execution pre-task
        :rtype: :class:`job.execution.tasks.PreTask`
        '''

        return PreTask(job_exe)
