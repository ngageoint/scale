"""Defines the class that manages all scheduling"""
from __future__ import unicode_literals

from django.utils.timezone import now

from job.execution.manager import job_exe_mgr
from job.resources import NodeResources
from job.tasks.manager import task_mgr
from scheduler.cleanup.manager import cleanup_mgr
from scheduler.node.manager import node_mgr
from scheduler.resources.manager import resource_mgr
from scheduler.scheduling.node import SchedulingNode

# It is considered a resource shortage if a task waits this many generations without being scheduled
TASK_SHORTAGE_WAIT_COUNT = 10


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

        when = now()

        nodes = self._prepare_nodes(when)

        fulfilled_nodes = self._schedule_waiting_tasks(nodes, when)

        # TODO: grab job type info

        # TODO: schedule new job_exes, including queries for job_exes and jobs, after queries do start_next_task()

        # TODO: grab offers and launch tasks

    def _prepare_nodes(self, when):
        """Prepares the nodes to use for scheduling

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The dict of scheduling nodes stored by node ID
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

    def _schedule_waiting_tasks(self, nodes, when):
        """Schedules all waiting tasks for which there are sufficient resources and updates the resource manager with
        any resource shortages. All scheduling nodes that have fulfilled all of their waiting tasks will be returned so
        new job executions can be added to them.

        :param nodes: The dict of scheduling nodes stored by node ID
        :type nodes: dict
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The dict of scheduling nodes stored by node ID that have no more waiting tasks
        :rtype: dict
        """

        fulfilled_nodes = {}  # {Node ID: SchedulingNode}
        waiting_tasks = []

        # Schedule waiting node tasks first
        for node in nodes.values():
            has_waiting_tasks = node.accept_node_tasks(when, waiting_tasks)
            if node.is_ready_for_next_job_task and not has_waiting_tasks:
                # A node can only be fulfilled if it is able to run waiting tasks and it has no more waiting tasks
                fulfilled_nodes[node.node_id] = node

        # Schedule job executions waiting for their next task
        # TODO: fail job_exes with a "node lost" error if job_exe's node does not appear in the dict or is offline or
        # changed agent ID
        # TODO: fail job_exes if they are starving to get resources for their next task
        for running_job_exe in job_exe_mgr.get_ready_job_exes():
            if running_job_exe.node_id in nodes:
                node = nodes[running_job_exe.node_id]
                has_waiting_tasks = node.accept_job_exe(running_job_exe, waiting_tasks)
                if has_waiting_tasks and node.node_id in fulfilled_nodes:
                    # Node has tasks waiting for resources
                    del fulfilled_nodes[node.node.node_id]

        # Update waiting task counts and calculate shortages
        agent_shortages = {}  # {Agent ID: NodeResources}
        new_waiting_tasks = {}  # {Task ID: int}
        for task in waiting_tasks:
            if task.id in self._waiting_tasks:
                count = self._waiting_tasks[task.id] + 1
            else:
                count = 1
            new_waiting_tasks[task.id] = count
            if count >= TASK_SHORTAGE_WAIT_COUNT:
                # This task has waited too long for resources, generate a shortage
                if task.agent_id in agent_shortages:
                    agent_shortages[task.agent_id].add(task.get_resources())
                else:
                    resources = NodeResources()
                    resources.add(task.get_resources())
                    agent_shortages[task.agent_id] = resources
        self._waiting_tasks = new_waiting_tasks
        resource_mgr.set_agent_shortages(agent_shortages)

        return fulfilled_nodes
