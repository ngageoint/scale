"""Defines the class that represents running job executions"""
from __future__ import unicode_literals

import threading

from job.resources import NodeResources


class RunningJobExecution(object):
    """This class represents a currently running job execution. This class is thread-safe."""

    def __init__(self, job_exe):
        """Constructor

        :param job_exe: The job execution, which must be in RUNNING status and have its related node, job, job_type and
            job_type_rev models populated
        :type job_exe: :class:`job.models.JobExecution`
        """

        self._id = job_exe.id
        self._job_type_id = job_exe.job.job_type_id
        self._lock = threading.Lock()
        self._node_id = job_exe.node.id

        # TODO: Future refactor: replace ScaleJobExecution with the new task system, add unit tests
        from scheduler.scale_job_exe import ScaleJobExecution
        self.scale_job_exe = ScaleJobExecution(job_exe, job_exe.cpus_scheduled, job_exe.mem_scheduled,
                                               job_exe.disk_in_scheduled, job_exe.disk_out_scheduled,
                                               job_exe.disk_total_scheduled)

    @property
    def id(self):
        """Returns the ID of this job execution

        :returns: The ID of the job execution
        :rtype: int
        """

        return self._id

    @property
    def job_type_id(self):
        """Returns the job type ID of this job execution

        :returns: The job type ID of the job execution
        :rtype: int
        """

        return self._job_type_id

    @property
    def node_id(self):
        """Returns the ID of this job execution's node

        :returns: The ID of the node
        :rtype: int
        """

        return self._node_id

    # TODO: Future refactor: have current_task() method
    def current_task_id(self):
        """Returns the ID of the current task

        :returns: The ID of the current task, possibly None
        :rtype: str
        """

        with self._lock:
            return self.scale_job_exe.current_task()

    def execution_canceled(self):
        """Cancels this job execution and returns the ID of the current task

        :returns: The ID of the current task, possibly None
        :rtype: str
        """

        with self._lock:
            task_id = self.scale_job_exe.current_task_id
            self.scale_job_exe.current_task_id = None
            self.scale_job_exe.remaining_task_ids = []
            return task_id

    def execution_lost(self, when):
        """Fails this job execution for its node becoming lost and returns the ID of the current task

        :param when: The time that the node was lost
        :type when: :class:`datetime.datetime`
        :returns: The ID of the current task, possibly None
        :rtype: str
        """

        with self._lock:
            from scheduler.scheduler_errors import get_node_lost_error
            error = get_node_lost_error()
            from queue.models import Queue
            Queue.objects.handle_job_failure(self.scale_job_exe.job_exe_id, when, error)
            task_id = self.scale_job_exe.current_task_id
            self.scale_job_exe.current_task_id = None
            self.scale_job_exe.remaining_task_ids = []
            return task_id

    def execution_timed_out(self, when):
        """Fails this job execution for timing out and returns the ID of the current task

        :param when: The time that the job execution timed out
        :type when: :class:`datetime.datetime`
        :returns: The ID of the current task, possibly None
        :rtype: str
        """

        with self._lock:
            from scheduler.scheduler_errors import get_timeout_error
            error = get_timeout_error()
            from queue.models import Queue
            Queue.objects.handle_job_failure(self.scale_job_exe.job_exe_id, when, error)
            task_id = self.scale_job_exe.current_task_id
            self.scale_job_exe.current_task_id = None
            self.scale_job_exe.remaining_task_ids = []
            return task_id

    def is_finished(self):
        """Indicates whether this job execution is finished with all tasks

        :returns: True if all tasks are finished, False otherwise
        :rtype: bool
        """

        with self._lock:
            return self.scale_job_exe.is_finished()

    def is_next_task_ready(self):
        """Indicates whether the next task in this job execution is ready

        :returns: True if the next task is ready, False otherwise
        :rtype: bool
        """

        with self._lock:
            return self.scale_job_exe.current_task_id is None and len(self.scale_job_exe.remaining_task_ids) > 0

    def next_task_resources(self):
        """Returns the resources that are required by the next task in this job execution. Returns None if there are no
        remaining tasks.

        :returns: The resources required by the next task, possibly None
        :rtype: :class:`job.resources.NodeResources`
        """

        with self._lock:
            if len(self.scale_job_exe.remaining_task_ids) == 0:
                return None

            cpus = self.scale_job_exe.cpus
            mem = self.scale_job_exe.mem
            if not self.scale_job_exe.remaining_task_ids:
                disk = 0.0
            else:
                disk = self.scale_job_exe._get_task_disk_required(self.scale_job_exe.remaining_task_ids[0])

            return NodeResources(cpus=cpus, mem=mem, disk=disk)

    def start_next_task(self):
        """Starts the next task in the job execution and returns it. Returns None if the next task is not ready or no
        tasks remain.

        :returns: The next Mesos task to schedule
        :rtype: :class:`mesos_pb2.TaskInfo`
        """

        with self._lock:
            if self.scale_job_exe.current_task_id is not None or len(self.scale_job_exe.remaining_task_ids) < 1:
                return None

            return self.scale_job_exe.start_next_task()

    def task_completed(self, task_id, status):
        """Completes a Mesos task for this job execution

        :param task_id: The ID of the task that was completed
        :type task_id: str
        :param status: The task status
        :type status: :class:`mesos_pb2.TaskStatus`
        """

        with self._lock:
            self.scale_job_exe.task_completed(task_id, status)

    def task_failed(self, task_id, status):
        """Fails a Mesos task for this job execution

        :param task_id: The ID of the task that failed
        :type task_id: str
        :param status: The task status
        :type status: :class:`mesos_pb2.TaskStatus`
        """

        with self._lock:
            self.scale_job_exe.task_failed(task_id, status)

    def task_running(self, task_id, status):
        """Tells this job execution that one of its tasks has started running

        :param task_id: The ID of the task that has started running
        :type task_id: str
        :param status: The task status
        :type status: :class:`mesos_pb2.TaskStatus`
        """

        with self._lock:
            self.scale_job_exe.task_running(task_id, status)
