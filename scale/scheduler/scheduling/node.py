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
        :type tasks: :class:`job.tasks.base_task.Task`
        :param offered_resources: The resources currently offered to the node
        :type offered_resources: :class:`job.resources.NodeResources`
        :param watermark_resources: The node's resource watermark
        :type watermark_resources: :class:`job.resources.NodeResources`
        """

        self.agent_id = agent_id  # Set agent ID separately from node since it can change during scheduling
        self.hostname = node.hostname
        self.node_id = node.id
        self.is_ready_for_new_job = node.is_ready_for_new_job()
        self.is_ready_for_next_job_task = node.is_ready_for_next_job_task()

        self._allocated_tasks = []
        self._current_tasks = tasks
        self._allocated_resources = NodeResources()
        self._offered_resources = offered_resources
        self._remaining_resources = NodeResources()
        self._remaining_resources.add(offered_resources)
        self._watermark_resources = watermark_resources
