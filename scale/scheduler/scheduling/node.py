"""Defines the class that manages scheduling for a node"""
from __future__ import unicode_literals

from job.resources import NodeResources


class SchedulingNode(object):
    """This class manages scheduling for a node.
    """

    def __init__(self, agent_id, node, tasks, offered_resources, watermark_resources):
        """Constructor

        :param agent_id: The agent ID
        :type agent_id: string
        :param node: The node
        :type node: :class:`scheduler.node.node_class.Node`
        :param tasks: The current tasks running on the node
        :type tasks: [:class:`job.tasks.base_task.Task`]
        :param offered_resources: The resources currently offered to the node
        :type offered_resources: :class:`job.resources.NodeResources`
        :param watermark_resources: The node's resource watermark
        :type watermark_resources: :class:`job.resources.NodeResources`
        """

        self.agent_id = agent_id  # Set agent ID separately from node since it can change during scheduling
        self.hostname = node.hostname
        self.node_id = node.id
        self.is_ready_for_new_job = node.is_ready_for_new_job()  # Cache this for consistency
        self.is_ready_for_next_job_task = node.is_ready_for_next_job_task()  # Cache this for consistency

        self._node = node

        self._allocated_job_exes = []  # Job executions that have been allocated resources from this node
        self._allocated_tasks = []  # Tasks that have been allocated resources from this node
        self._current_tasks = tasks
        self._allocated_resources = NodeResources()
        self._offered_resources = offered_resources
        self._remaining_resources = NodeResources()
        self._remaining_resources.add(offered_resources)
        self._watermark_resources = watermark_resources

    def accept_job_exe(self, job_exe, waiting_tasks):
        """Asks the node if it can accept the next task for the given job execution. If the next task is waiting on
        resources, the task is added to the given waiting list.

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
