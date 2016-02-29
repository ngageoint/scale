"""Defines the class that manages the syncing of the scheduler with the node models"""
from __future__ import unicode_literals

import threading

from mesos_api import api
from node.models import Node


class NodeManager(object):
    """This class manages the syncing of the scheduler with the node models. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._new_agent_ids = set()
        self._nodes = {}  # {Agent ID: Node}
        self._online_nodes = set()  # {Agent ID}
        self._lock = threading.Lock()

    def add_agent_ids(self, agent_ids):
        """Adds the list of agent IDs to the manager so they can be looked up and registered in the database

        :param agent_ids: The list of agent IDs to add
        :type agent_ids: [str]
        """

        with self._lock:
            for agent_id in agent_ids:
                if agent_id not in self._nodes:
                    self._new_agent_ids.add(agent_id)
                self._online_nodes.add(agent_id)

    def get_node(self, agent_id):
        """Returns the node with the given agent ID, possibly None

        :param agent_id: The agent ID of the node
        :type agent_id: str
        :returns: The node for the given agent ID or None
        :rtype: :class:`node.models.Node`
        """

        with self._lock:
            if agent_id in self._nodes:
                return self._nodes[agent_id]
            return None

    def get_nodes(self):
        """Returns a list of all nodes

        :returns: The list of all nodes
        :rtype: [:class:`node.models.Node`]
        """

        with self._lock:
            return list(self._nodes.values())

    def lost_node(self, agent_id):
        """Informs the manager that the node with the given agent ID was lost and has gone offline

        :param agent_id: The agent ID of the lost node
        :type agent_id: str
        """

        with self._lock:
            self._online_nodes.discard(agent_id)

    def sync_with_database(self, master_hostname, master_port):
        """Syncs with the database to retrieve updated node models and queries Mesos for unknown agent IDs

        :param master_hostname: The name of the Mesos master host
        :type master_hostname: str
        :param master_port: The port used by the Mesos master
        :type master_port: int
        """

        # Get current node IDs and new, unknown agent IDs
        with self._lock:
            new_agent_ids = set(self._new_agent_ids)
            node_ids = []
            for node in self._nodes.values():
                node_ids.append(node.id)

        # Query for unknown agent IDs
        # TODO: refactor register_node() to handle multiple nodes at once
        updated_nodes = []
        for slave_info in api.get_slaves(master_hostname, master_port):
            if slave_info.slave_id in new_agent_ids:
                node = Node.objects.register_node(slave_info.hostname, slave_info.port, slave_info.slave_id)
                updated_nodes.append(node)

        # Query database for existing nodes
        updated_nodes.extend(Node.objects.filter(id__in=node_ids).iterator())

        # Update with results
        with self._lock:
            self._new_agent_ids -= new_agent_ids
            self._nodes = {}
            for node in updated_nodes:
                node.is_online = node.slave_id in self._online_nodes
                self._nodes[node.slave_id] = node
