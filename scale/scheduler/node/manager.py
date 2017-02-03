"""Defines the class that manages the scheduler nodes"""
from __future__ import unicode_literals

import logging
import threading

from mesos_api import api
from node.models import Node
from scheduler.node.node_class import Node as SchedulerNode


logger = logging.getLogger(__name__)


class NodeManager(object):
    """This class manages the scheduler nodes. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._agent_ids = {}  # {Agent ID: Hostname}
        self._new_agent_ids = set()
        self._nodes = {}  # {Hostname: SchedulerNode}
        self._lock = threading.Lock()

    def clear(self):
        """Clears all node data from the manager. This method is intended for testing only.
        """

        with self._lock:
            self._agent_ids = {}
            self._new_agent_ids = set()
            self._nodes = {}

    def get_next_tasks(self, when):
        """Returns the next node tasks to schedule

        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: A list of the next node tasks to schedule
        :rtype: [:class:`job.tasks.base_task.Task`]
        """

        tasks = []
        with self._lock:
            for node in self._nodes.values():
                task = node.get_next_task(when)
                if task:
                    tasks.append(task)
        return tasks

    def get_node(self, agent_id):
        """Returns the node with the given agent ID, possibly None

        :param agent_id: The agent ID of the node
        :type agent_id: string
        :returns: The node, possibly None
        :rtype: :class:`scheduler.node.node_class.Node`
        """

        with self._lock:
            if agent_id not in self._agent_ids:
                return None
            hostname = self._agent_ids[agent_id]
            return self._nodes[hostname]

    def get_nodes(self):
        """Returns a list of all nodes

        :returns: The list of all nodes
        :rtype: [:class:`scheduler.node.node_class.Node`]
        """

        with self._lock:
            return list(self._nodes.values())

    def handle_task_timeout(self, task):
        """Handles the timeout of the given task

        :param task: The task
        :type task: :class:`job.tasks.base_task.Task`
        """

        with self._lock:
            if task.agent_id not in self._agent_ids:
                return
            node_id = self._agent_ids[task.agent_id]
            self._nodes[node_id].handle_task_timeout(task)

    def handle_task_update(self, task_update):
        """Handles the given task update for a task

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if task_update.agent_id not in self._agent_ids:
                return
            node_id = self._agent_ids[task_update.agent_id]
            self._nodes[node_id].handle_task_update(task_update)

    def lost_node(self, agent_id):
        """Informs the manager that the node with the given agent ID was lost and has gone offline

        :param agent_id: The agent ID of the lost node
        :type agent_id: string
        """

        with self._lock:
            if agent_id in self._agent_ids:
                hostname = self._agent_ids[agent_id]
                self._nodes[hostname].update_from_mesos(is_online=False)
                logger.warning('Node %s has gone offline', hostname)
            if agent_id in self._new_agent_ids:
                self._new_agent_ids.discard(agent_id)

    def register_agent_ids(self, agent_ids):
        """Adds the list of online agent IDs to the manager so they can be registered

        :param agent_ids: The list of online agent IDs to add
        :type agent_ids: [string]
        """

        with self._lock:
            for agent_id in agent_ids:
                if agent_id in self._agent_ids:
                    # Agent ID already known, mark its node as online
                    hostname = self._agent_ids[agent_id]
                    self._nodes[hostname].update_from_mesos(is_online=True)
                else:
                    # Unknown agent ID, save it to be registered as a node
                    self._new_agent_ids.add(agent_id)

    def sync_with_database(self, master_hostname, master_port):
        """Syncs with the database to retrieve updated node models and queries Mesos for unknown agent IDs

        :param master_hostname: The name of the Mesos master host
        :type master_hostname: string
        :param master_port: The port used by the Mesos master
        :type master_port: int
        """

        # Get existing node IDs and hostnames, and new/unknown agent IDs
        with self._lock:
            new_agent_ids = set(self._new_agent_ids)
            node_ids = []
            node_hostnames = self._nodes.keys()
            for node in self._nodes.values():
                node_ids.append(node.id)

        # Query Mesos to get node details for unknown agent IDs
        # Unknown agent IDs are either existing nodes with a new agent ID or entirely new nodes
        # TODO: refactor register_node() to handle multiple nodes at once
        # TODO: consider refactoring node model to remove port and agent/slave ID
        nodes_with_new_agent_id = {}  # {hostname: slave_info}
        new_node_models = []
        for slave_info in api.get_slaves(master_hostname, master_port):
            if slave_info.slave_id in new_agent_ids:
                node_model = Node.objects.register_node(slave_info.hostname, slave_info.port, slave_info.slave_id)
                if slave_info.hostname in node_hostnames:
                    # New agent ID for existing node
                    nodes_with_new_agent_id[slave_info.hostname] = slave_info
                else:
                    # Entirely new node
                    new_node_models.append(node_model)

        # Query database for existing node details
        existing_node_models = list(Node.objects.filter(id__in=node_ids).iterator())

        with self._lock:
            # Add new nodes
            for node_model in new_node_models:
                self._nodes[node_model.hostname] = SchedulerNode(node_model.slave_id, node_model)
                self._agent_ids[node_model.slave_id] = node_model.hostname
                logger.info('New node %s registered with agent ID %s', node_model.hostname, node_model.slave_id)
            # Update nodes with new agent IDs
            for hostname, slave_info in nodes_with_new_agent_id.items():
                old_agent_id = self._nodes[hostname].agent_id
                self._nodes[hostname].update_from_mesos(agent_id=slave_info.slave_id, port=slave_info.port)
                del self._agent_ids[old_agent_id]
                self._agent_ids[slave_info.slave_id] = hostname
                logger.info('Node %s registered with new agent ID %s', hostname, slave_info.slave_id)
            # Update nodes from database models
            for node_model in existing_node_models:
                self._nodes[node_model.hostname].update_from_model(node_model)
            # Update online flag for nodes with new agent IDs
            for new_agent_id in new_agent_ids:
                hostname = self._agent_ids[new_agent_id]
                # Check if new agent ID is still in set or gone (i.e. removed by lost_node())
                self._nodes[hostname].update_from_mesos(is_online=(new_agent_id in self._new_agent_ids))
            self._new_agent_ids -= new_agent_ids  # Batch of new agent IDs has been processed


node_mgr = NodeManager()
