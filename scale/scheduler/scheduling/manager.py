"""Defines the class that manages all scheduling"""
from __future__ import unicode_literals

from django.utils.timezone import now

from job.resources import NodeResources
from job.tasks.manager import task_mgr
from scheduler.cleanup.manager import cleanup_mgr
from scheduler.node.manager import node_mgr
from scheduler.resources.manager import resource_mgr
from scheduler.scheduling.node import SchedulingNode


class SchedulingManager(object):
    """This class manages all scheduling. This class is NOT thread-safe and should only be used within the scheduling
    thread.
    """

    def __init__(self):
        """Constructor
        """

        self._waiting_tasks = {}  # {Task ID: int}

    def perform_scheduling(self):
        """Organizes and analyzes the cluster resources, schedules new job executions, and launches tasks
        """

        # TODO: implement
        when = now()

        nodes = self._prepare_nodes(when)

    def _prepare_nodes(self, when):
        """Prepares the nodes to use for scheduling

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The dict of nodes stored by node ID
        :rtype: dict
        """

        nodes = node_mgr.get_nodes()
        cleanup_mgr.update_nodes(nodes)

        tasks = task_mgr.get_all_tasks()
        tasks_by_agent_id = {}  # {Agent ID: Task}
        for task in tasks:
            if task.agent_id not in tasks_by_agent_id:
                tasks_by_agent_id[task.agent_id] = [task]
            else:
                tasks_by_agent_id[task.agent_id].append(task)

        agent_resources = resource_mgr.refresh_agent_resources(tasks, when)

        scheduling_nodes = {}  # {Node ID: SchedulingNode}
        for node in nodes:
            agent_id = node.agent_id   # Grab agent ID once since it could change while we are scheduling

            if agent_id in tasks_by_agent_id:
                node_tasks = tasks_by_agent_id[agent_id]
            else:
                node_tasks = []
            if agent_id in agent_resources:
                offered_resources, watermark_resources = agent_resources[agent_id]
            else:
                offered_resources = NodeResources()
                watermark_resources = NodeResources()

            scheduling_node = SchedulingNode(agent_id, node, node_tasks, offered_resources, watermark_resources)
            scheduling_nodes[scheduling_node.node_id] = scheduling_node
        return scheduling_nodes
