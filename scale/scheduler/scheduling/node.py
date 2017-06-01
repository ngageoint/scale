"""Defines the class that manages scheduling for a node"""
from __future__ import unicode_literals

from job.resources import NodeResources


class SchedulingNode(object):
    """This class manages scheduling for a node.
    """

    def __init__(self, agent_id, node, tasks, resource_set):
        """Constructor

        :param agent_id: The agent ID
        :type agent_id: string
        :param node: The node
        :type node: :class:`scheduler.node.node_class.Node`
        :param tasks: The current tasks running on the node
        :type tasks: [:class:`job.tasks.base_task.Task`]
        :param resource_set: The set of resources for the node
        :type resource_set: :class:`scheduler.resources.agent.ResourceSet`
        """

        self.agent_id = agent_id  # Set agent ID separately from node since it can change during scheduling
        self.hostname = node.hostname
        self.node_id = node.id
        self.is_ready_for_new_job = node.is_ready_for_new_job()  # Cache this for consistency
        self.is_ready_for_next_job_task = node.is_ready_for_next_job_task()  # Cache this for consistency

        self._node = node

        self._allocated_job_exes = []  # Job executions (already on this node) that have been allocated resources
        self._allocated_new_job_exes = []  # New job executions that have been allocated resources to start on this node
        self._allocated_tasks = []  # Tasks that have been allocated resources from this node
        self._current_tasks = tasks
        self._allocated_resources = NodeResources()
        self._offered_resources = resource_set.offered_resources
        self._remaining_resources = NodeResources()
        self._remaining_resources.add(self._offered_resources)
        self._task_resources = resource_set.task_resources
        self._watermark_resources = resource_set.watermark_resources

    def accept_job_exe_next_task(self, job_exe, waiting_tasks):
        """Asks the node if it can accept the next task for the given job execution. If the next task is waiting on
        resources, the task is added to the given waiting list. This should be used for job executions that have already
        been scheduled on this node, not new job executions.

        :param job_exe: The job execution to accept
        :type job_exe: :class:`job.execution.job_exe.RunningJobExecution`
        :param waiting_tasks: List of tasks that are waiting for resources
        :type waiting_tasks: [:class:`job.tasks.base_task.Task`]
        :returns: True if waiting tasks were added to the list, False otherwise
        :rtype: bool
        """

        if not self.is_ready_for_next_job_task:
            return False

        task = job_exe.next_task()
        if not task:
            return False
        task_resources = task.get_resources()
        if self._remaining_resources.is_sufficient_to_meet(task_resources):
            self._allocated_job_exes.append(job_exe)
            self._allocated_resources.add(task_resources)
            self._remaining_resources.subtract(task_resources)
            return False

        # Not enough resources, so add task to waiting list
        waiting_tasks.append(task)
        return True

    def accept_new_job_exe(self, job_exe):
        """Asks the node if it can accept the given new job execution

        :param job_exe: The new job execution
        :type job_exe: :class:`queue.job_exe.QueuedJobExecution`
        :returns: True if the new job execution was accepted, False otherwise
        :rtype: bool
        """

        resources = job_exe.required_resources
        if self._remaining_resources.is_sufficient_to_meet(resources):
            self._allocated_new_job_exes.append(job_exe)
            self._allocated_resources.add(resources)
            self._remaining_resources.subtract(resources)
            job_exe.accepted(self.node_id, resources)
            return True

        return False

    def accept_node_tasks(self, when, waiting_tasks):
        """Asks the node to accept any node tasks that need to be scheduled. If any node tasks are waiting on resources,
        those tasks are added to the given waiting list.

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :param waiting_tasks: List of tasks that are waiting for resources
        :type waiting_tasks: [:class:`job.tasks.base_task.Task`]
        :returns: True if waiting tasks were added to the list, False otherwise
        :rtype: bool
        """

        result = False
        for task in self._node.get_next_tasks(when):
            task_resources = task.get_resources()
            if self._remaining_resources.is_sufficient_to_meet(task_resources):
                self._allocated_tasks.append(task)
                self._allocated_resources.add(task_resources)
                self._remaining_resources.subtract(task_resources)
            else:
                waiting_tasks.append(task)
                result = True
        return result

    def score_job_exe_for_reservation(self, job_exe):
        """Returns an integer score (lower is better) indicating how well this node is a fit for reserving (temporarily
        block additional job executions) for the given job execution. If the job execution cannot reserve this node,
        None is returned.

        :param job_exe: The job execution to score
        :type job_exe: :class:`queue.job_exe.QueuedJobExecution`
        :returns: The integer score indicating how good of a fit reserving this node is for this job execution, possibly
            None
        :rtype: int
        """

        if not self._watermark_resources.is_sufficient_to_meet(job_exe.required_resources):
            return None

        # TODO: right now all nodes are considered equal for reservation, in the future use average job type duration
        # and current running node tasks to predict which node will be available quickest to run the job execution
        return 1

    def score_job_exe_for_scheduling(self, job_exe, job_type_resources):
        """Returns an integer score (lower is better) indicating how well the given job execution fits on this node for
        scheduling. If the job execution cannot be scheduled on this node, None is returned.

        :param job_exe: The job execution to score
        :type job_exe: :class:`queue.job_exe.QueuedJobExecution`
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        :returns: The integer score indicating how good of a fit this job execution is for this node, possibly None
        :rtype: int
        """

        if not self._remaining_resources.is_sufficient_to_meet(job_exe.required_resources):
            return None

        # Calculate our best guess of the total resources still available to Scale on this node by starting with the
        # watermark resource level and subtracting resources for currently running and allocated tasks
        total_resources_available = NodeResources()
        total_resources_available.add(self._watermark_resources)
        total_resources_available.subtract(self._task_resources)
        total_resources_available.subtract(self._allocated_resources)
        total_resources_available.subtract(job_exe.required_resources)

        # Score is the number of job types that can fit within the estimated resources on this node still available to
        # Scale. A better (lower) score indicates a higher utilization of this node, reducing resource fragmentation.
        score = 0
        for job_type_resource in job_type_resources:
            if total_resources_available.is_sufficient_to_meet(job_type_resource):
                score += 1

        return True
