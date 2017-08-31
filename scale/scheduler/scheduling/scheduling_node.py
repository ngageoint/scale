"""Defines the class that manages scheduling for a node"""
from __future__ import absolute_import
from __future__ import unicode_literals

from job.execution.tasks.exe_task import JobExecutionTask
from node.resources.node_resources import NodeResources


class SchedulingNode(object):
    """This class manages scheduling for a node.
    """

    def __init__(self, agent_id, node, tasks, running_job_exes, resource_set):
        """Constructor

        :param agent_id: The agent ID
        :type agent_id: string
        :param node: The node
        :type node: :class:`scheduler.node.node_class.Node`
        :param tasks: The current tasks running on the node
        :type tasks: list
        :param running_job_exes: The current job executions running on the node
        :type running_job_exes: list
        :param resource_set: The set of resources for the node
        :type resource_set: :class:`scheduler.resources.agent.ResourceSet`
        """

        self.agent_id = agent_id  # Set agent ID separately from node since it can change during scheduling
        self.hostname = node.hostname
        self.node_id = node.id
        self.is_ready_for_new_job = node.is_ready_for_new_job()  # Cache this for consistency
        self.is_ready_for_next_job_task = node.is_ready_for_next_job_task()  # Cache this for consistency
        self.is_ready_for_system_task = node.is_ready_for_system_task()  # Cache this for consistency
        self.allocated_offers = []
        self.allocated_resources = NodeResources()
        self.allocated_tasks = []  # Tasks that have been allocated resources from this node

        self._node = node
        self._allocated_queued_job_exes = []  # New queued job executions that have been allocated resources
        self._allocated_running_job_exes = []  # Running job executions that have been allocated resources
        self._running_job_exes = running_job_exes
        self._running_tasks = tasks

        self._offered_resources = NodeResources()  # The amount of resources that were originally offered
        self._offered_resources.add(resource_set.offered_resources)
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
            self._allocated_running_job_exes.append(job_exe)
            self.allocated_resources.add(task_resources)
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

        if not self.is_ready_for_new_job:
            return False

        resources = job_exe.required_resources
        if self._remaining_resources.is_sufficient_to_meet(resources):
            self._allocated_queued_job_exes.append(job_exe)
            self.allocated_resources.add(resources)
            self._remaining_resources.subtract(resources)
            job_exe.scheduled(self.agent_id, self.node_id, resources)
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
                self.allocated_tasks.append(task)
                self.allocated_resources.add(task_resources)
                self._remaining_resources.subtract(task_resources)
            else:
                waiting_tasks.append(task)
                result = True
        return result

    def accept_system_task(self, system_task):
        """Asks the node if it can accept the given system task

        :param system_task: The system task
        :type system_task: :class:`job.tasks.base_task.Task`
        :returns: True if the system task was accepted, False otherwise
        :rtype: bool
        """

        if not self.is_ready_for_system_task:
            return False

        task_resources = system_task.get_resources()
        if self._remaining_resources.is_sufficient_to_meet(task_resources):
            system_task.agent_id = self.agent_id  # Must set agent ID for task
            self.allocated_tasks.append(system_task)
            self.allocated_resources.add(task_resources)
            self._remaining_resources.subtract(task_resources)
            return True

        return False

    def add_allocated_offers(self, offers):
        """Adds the resource offers that have been allocated to run this node's tasks. If the offer resources are not
        enough to cover the current allocation, job executions and tasks are removed as necessary.

        :param offers: The resource offers to add
        :type offers: list
        """

        offer_resources = NodeResources()
        for offer in offers:
            offer_resources.add(offer.resources)

        self.allocated_offers = offers

        # If the offers are not enough to cover what we allocated, drop all job execution tasks
        if not offer_resources.is_sufficient_to_meet(self.allocated_resources):
            job_exe_resources = NodeResources()
            for job_exe in self._allocated_running_job_exes:
                task = job_exe.next_task()
                if task:
                    job_exe_resources.add(task.get_resources())
            self._allocated_running_job_exes = []
            self.allocated_resources.subtract(job_exe_resources)
            self._remaining_resources.add(job_exe_resources)

        # If the offers are still not enough to cover what we allocated, drop all tasks
        if not offer_resources.is_sufficient_to_meet(self.allocated_resources):
            self.allocated_tasks = []
            self.allocated_resources = NodeResources()
            self._remaining_resources = NodeResources()
            self._remaining_resources.add(self._offered_resources)

    def add_scheduled_job_exes(self, job_exes):
        """Hands the node its queued job executions that have now been scheduled in the database and are now running

        :param job_exes: The running job executions that have now been scheduled in the database
        :type job_exes: list
        """

        self._allocated_queued_job_exes = []
        self._allocated_running_job_exes.extend(job_exes)

    def reset_new_job_exes(self):
        """Resets the allocated new job executions and deallocates any resources associated with them
        """

        if not self._allocated_queued_job_exes:
            return

        resources = NodeResources()
        for new_job_exe in self._allocated_queued_job_exes:
            resources.add(new_job_exe.required_resources)

        self._allocated_queued_job_exes = []
        self.allocated_resources.subtract(resources)
        self._remaining_resources.add(resources)

    def score_job_exe_for_reservation(self, job_exe, job_type_resources):
        """Returns an integer score (lower is better) indicating how well this node is a fit for reserving (temporarily
        blocking additional job executions of lower priority) for the given job execution. If the job execution cannot
        reserve this node, None is returned.

        :param job_exe: The job execution to score
        :type job_exe: :class:`queue.job_exe.QueuedJobExecution`
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        :returns: The integer score indicating how good of a fit reserving this node is for this job execution, possibly
            None
        :rtype: int
        """

        # Calculate available resources for lower priority jobs
        available_resources = NodeResources()
        available_resources.add(self._watermark_resources)
        for running_task in self._running_tasks:  # Remove resources for system tasks
            if not isinstance(running_task, JobExecutionTask):
                available_resources.subtract(running_task.get_resources())
        for running_job_exe in self._running_job_exes:  # Remove resources for existing jobs of equal/higher priority
            if running_job_exe.priority <= job_exe.priority:
                task = running_job_exe.current_task
                if not task:
                    task = running_job_exe.next_task()
                if task:
                    available_resources.subtract(task.get_resources())
        for queued_job_exe in self._allocated_queued_job_exes:  # Remove resources for new jobs of equal/higher priority
            if queued_job_exe.priority <= job_exe.priority:
                available_resources.subtract(queued_job_exe.required_resources)

        # If there are enough resources (unused plus used by lower priority jobs) to eventually run this job, then
        # reserve this node to block lower priority jobs
        if not available_resources.is_sufficient_to_meet(job_exe.required_resources):
            return None

        available_resources.subtract(job_exe.required_resources)
        # Score is the number of job types that can fit within the estimated remaining resources. A better (lower) score
        # indicates a higher utilization of this node, reducing resource fragmentation.
        score = 0
        for job_type_resource in job_type_resources:
            if available_resources.is_sufficient_to_meet(job_type_resource):
                score += 1

        return score

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

        return self._score_resources_for_scheduling(job_exe.required_resources, job_type_resources)

    def score_system_task_for_scheduling(self, system_task, job_type_resources):
        """Returns an integer score (lower is better) indicating how well the given system task fits on this node for
        scheduling. If the system task cannot be scheduled on this node, None is returned.

        :param system_task: The system task to score
        :type system_task: :class:`job.tasks.base_task.Task`
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        :returns: The integer score indicating how good of a fit this system task is for this node, possibly None
        :rtype: int
        """

        return self._score_resources_for_scheduling(system_task.get_resources(), job_type_resources)

    def start_job_exe_tasks(self):
        """Tells the node to start the next task on all scheduled job executions
        """

        for job_exe in self._allocated_running_job_exes:
            task = job_exe.start_next_task()
            if task:
                self.allocated_tasks.append(task)
        self._allocated_running_job_exes = []

    def _score_resources_for_scheduling(self, resources, job_type_resources):
        """Returns an integer score (lower is better) indicating how well the given resources fit on this node for
        scheduling. If the resources cannot be scheduled on this node, None is returned.

        :param resources: The resources to score
        :type resources: :class:`node.resources.node_resources.NodeResources`
        :param job_type_resources: The list of all of the job type resource requirements
        :type job_type_resources: list
        :returns: The integer score indicating how good of a fit these resources are for this node, possibly None
        :rtype: int
        """

        if not self._remaining_resources.is_sufficient_to_meet(resources):
            return None

        # Calculate our best guess of the total resources still available to Scale on this node by starting with the
        # watermark resource level and subtracting resources for currently running and allocated tasks
        total_resources_available = NodeResources()
        total_resources_available.add(self._watermark_resources)
        total_resources_available.subtract(self._task_resources)
        total_resources_available.subtract(self.allocated_resources)
        total_resources_available.subtract(resources)

        # Score is the number of job types that can fit within the estimated resources on this node still available to
        # Scale. A better (lower) score indicates a higher utilization of this node, reducing resource fragmentation.
        score = 0
        for job_type_resource in job_type_resources:
            if total_resources_available.is_sufficient_to_meet(job_type_resource):
                score += 1

        return score
