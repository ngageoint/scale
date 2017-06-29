"""Defines the class that manages the scheduler nodes"""
from __future__ import unicode_literals

import logging
import threading

from node.models import Node
from scheduler.node.node_class import Node as SchedulerNode


logger = logging.getLogger(__name__)


class NodeManager(object):
    """This class manages the scheduler nodes. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._agents = {}  # {Agent ID: Agent}
        self._new_agents = {}  # {Agent ID: Agent}
        self._nodes = {}  # {Hostname: SchedulerNode}
        self._lock = threading.Lock()

    def clear(self):
        """Clears all node data from the manager. This method is intended for testing only.
        """

        with self._lock:
            self._agents = {}
            self._new_agents = {}
            self._nodes = {}

    def generate_status_json(self, status_dict):
        """Generates the portion of the status JSON that describes the nodes

        :param status_dict: The status JSON dict
        :type status_dict: dict
        """

        nodes_list = []
        status_dict['nodes'] = nodes_list
        with self._lock:
            for node in self._nodes.values():
                node.generate_status_json(nodes_list)

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
                tasks.extend(node.get_next_tasks(when))
        return tasks

    def get_node(self, agent_id):
        """Returns the node with the given agent ID, possibly None

        :param agent_id: The agent ID of the node
        :type agent_id: string
        :returns: The node, possibly None
        :rtype: :class:`scheduler.node.node_class.Node`
        """

        with self._lock:
            if agent_id not in self._agents:
                return None
            hostname = self._agents[agent_id].hostname
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
            if task.agent_id not in self._agents:
                return
            hostname = self._agents[task.agent_id].hostname
            self._nodes[hostname].handle_task_timeout(task)

    def handle_task_update(self, task_update):
        """Handles the given task update for a task

        :param task_update: The task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        with self._lock:
            if task_update.agent_id not in self._agents:
                return
            hostname = self._agents[task_update.agent_id].hostname
            self._nodes[hostname].handle_task_update(task_update)

    def lost_node(self, agent_id):
        """Informs the manager that the node with the given agent ID was lost and has gone offline

        :param agent_id: The agent ID of the lost node
        :type agent_id: string
        """

        with self._lock:
            if agent_id in self._agents:
                hostname = self._agents[agent_id].hostname
                self._nodes[hostname].update_from_mesos(is_online=False)
                logger.warning('Node %s has gone offline', hostname)
            if agent_id in self._new_agents:
                del self._new_agents[agent_id]

    def register_agents(self, agents):
        """Adds the list of online agents to the manager so they can be registered

        :param agents: The list of online agents to register
        :type agents: list
        """

        with self._lock:
            for agent in agents:
                agent_id = agent.agent_id
                if agent_id in self._agents:
                    # Agent already known, mark its node as online
                    hostname = self._agents[agent_id].hostname
                    self._nodes[hostname].update_from_mesos(is_online=True)
                else:
                    # Unknown agent ID, save it to be registered as a node
                    self._new_agents[agent_id] = agent

    def sync_with_database(self, scheduler_config):
        """Syncs with the database to retrieve updated node models and queries Mesos for unknown agent IDs

        :param scheduler_config: The scheduler configuration
        :type scheduler_config: :class:`scheduler.configuration.SchedulerConfiguration`
        """

        with self._lock:
            # Gather up all host names and new agents
            hostnames = set(self._nodes.keys())
            new_agents = {}  # {Agent ID: Agent}
            for agent in self._new_agents.values():
                new_agents[agent.agent_id] = agent
                hostnames.add(agent.hostname)

        # Get all existing node models needed (online and/or active)
        node_models = {}
        for node_model in Node.objects.get_scheduler_nodes(hostnames):
            node_models[node_model.hostname] = node_model
        # Create new nodes for host names that have never been seen before
        new_hostnames = []
        new_agent_ids = []
        for agent in new_agents.values():
            if agent.hostname not in node_models:
                new_hostnames.append(agent.hostname)
                new_agent_ids.append(agent.agent_id)
        if new_hostnames:
            logger.info('Creating %d new node(s) in the database', len(new_hostnames))
            for node_model in Node.objects.create_nodes(new_hostnames, new_agent_ids):
                node_models[node_model.hostname] = node_model

        with self._lock:
            # Handle new agents
            for new_agent in new_agents.values():
                agent_id = new_agent.agent_id
                hostname = new_agent.hostname
                # For is_online, check if new agent ID is still in set or gone (i.e. removed by lost_node())
                is_online = agent_id in self._new_agents
                if is_online:
                    logger.info('Node %s online with new agent ID %s', hostname, agent_id)
                else:
                    logger.warning('Node %s received new agent ID %s, but quickly went offline', hostname, agent_id)
                if hostname in self._nodes:
                    # Host name already exists, must be a new agent ID
                    old_agent_id = self._nodes[hostname].agent_id
                    self._nodes[hostname].update_from_mesos(agent_id=agent_id, is_online=is_online)
                    if old_agent_id in self._agents:
                        del self._agents[old_agent_id]
                else:
                    # Host name does not exist, register a new node
                    node_model = node_models[hostname]
                    self._nodes[hostname] = SchedulerNode(agent_id, node_model, scheduler_config)
                    self._nodes[hostname].update_from_mesos(is_online=is_online)
                self._agents[agent_id] = new_agent
            # Update nodes from database models
            for node_model in node_models.values():
                hostname = node_model.hostname
                if hostname in self._nodes:
                    # Host name already exists, update model information
                    node = self._nodes[hostname]
                    node.update_from_model(node_model, scheduler_config)
                    if node.should_be_removed():
                        logger.info('Node %s removed since it is both offline and deprecated', hostname)
                        del self._nodes[hostname]
                        if node.agent_id in self._agents:
                            del self._agents[node.agent_id]
                else:
                    # Host name does not exist, must be an active node with no agent ID yet
                    logger.info('Active node %s registered from the database (currently offline)', hostname)
                    self._nodes[hostname] = SchedulerNode('', node_model, scheduler_config)
                    self._nodes[hostname].update_from_mesos(is_online=False)
            # Finished this batch of new agents
            for new_agent in new_agents.values():
                if new_agent.agent_id in self._new_agents:
                    del self._new_agents[new_agent.agent_id]


node_mgr = NodeManager()
