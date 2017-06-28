"""Defines the class that manages all scheduler resources"""
from __future__ import unicode_literals

import datetime
import logging
import threading

from mesos_api.unversioned.agent import get_agent_resources
from node.resources.node_resources import NodeResources
from scheduler.resources.agent import AgentResources

# Amount of time between rolling watermark resets
WATERMARK_RESET_PERIOD = datetime.timedelta(minutes=5)


logger = logging.getLogger(__name__)


class ResourceManager(object):
    """This class manages all resources from the cluster nodes. This class is thread-safe."""

    def __init__(self):
        """Constructor
        """

        self._agent_resources = {}  # {Agent ID: AgentResources}
        self._agent_resources_lock = threading.Lock()  # Protects self._agent_resources
        self._last_watermark_reset = None
        self._new_offers = {}  # {Offer ID: ResourceOffer}
        self._new_offers_lock = threading.Lock()  # Protects self._new_offers

    def add_new_offers(self, offers):
        """Adds new resource offers to the manager

        :param offers: The list of new offers to add
        :type offers: [:class:`scheduler.resources.offer.ResourceOffer`]
        """

        with self._new_offers_lock:
            for offer in offers:
                self._new_offers[offer.id] = offer

    def allocate_offers(self, resources, when):
        """Directs all agents to allocate offers sufficient to match the given resources. Any offers that have been held
        too long will automatically be included (including agents that resources were not requested from). It's possible
        that the offer resources returned for an agent are less than requested or that an agent is not included in the
        results.

        :param resources: Dict where agent ID maps to the requested resources
        :type resources: dict
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: Dict where agent ID maps to a list of the allocated offers
        :rtype: dict
        """

        allocated_offers = {}
        with self._agent_resources_lock:
            for agent_resources in self._agent_resources.values():
                if agent_resources.agent_id in resources:
                    requested_resources = resources[agent_resources.agent_id]
                else:
                    requested_resources = NodeResources()
                offer_list = agent_resources.allocate_offers(requested_resources, when)
                if offer_list:
                    allocated_offers[agent_resources.agent_id] = offer_list

        return allocated_offers

    def clear(self):
        """Clears all offer data from the manager. This method is intended for testing only.
        """

        self._agent_resources = {}
        self._last_watermark_reset = None
        self._new_offers = {}

    def generate_status_json(self, status_dict):
        """Generates the portion of the status JSON that describes the resources

        :param status_dict: The status JSON dict
        :type status_dict: dict
        """

        num_offers = 0
        total_running = NodeResources()
        total_offered = NodeResources()
        total_watermark = NodeResources()
        total_resources = NodeResources()

        with self._agent_resources_lock:
            for node_dict in status_dict['nodes']:
                agent_id = node_dict['agent_id']
                is_active = node_dict['is_active']
                if agent_id in self._agent_resources:
                    agent_resources = self._agent_resources[agent_id]
                    if is_active:
                        num_offers += agent_resources.generate_status_json(node_dict, total_running, total_offered,
                                                                           total_watermark, total_resources)
                    else:
                        agent_resources.generate_status_json(node_dict)

        free_resources = total_watermark.copy()
        free_resources.subtract(total_running)
        free_resources.subtract(total_offered)
        unavailable_resources = total_resources.copy()
        unavailable_resources.subtract(total_watermark)
        resources_dict = {}

        total_running.generate_status_json(resources_dict, 'running', total_resources)
        total_offered.generate_status_json(resources_dict, 'offered', total_resources)
        free_resources.generate_status_json(resources_dict, 'free', total_resources)
        unavailable_resources.generate_status_json(resources_dict, 'unavailable', total_resources)
        total_resources.generate_status_json(resources_dict, 'total', None)

        # Fill in any missing values
        for resource in total_resources.resources:
            resource_dict = resources_dict[resource.name]
            if 'running' not in resource_dict:
                resource_dict['running'] = {'value': 0.0, 'percentage': 0.0}
            if 'offered' not in resource_dict:
                resource_dict['offered'] = {'value': 0.0, 'percentage': 0.0}
            if 'free' not in resource_dict:
                resource_dict['free'] = {'value': 0.0, 'percentage': 0.0}
            if 'unavailable' not in resource_dict:
                resource_dict['unavailable'] = {'value': 0.0, 'percentage': 0.0}

        status_dict['num_offers'] = num_offers
        status_dict['resources'] = resources_dict

    def lost_agent(self, agent_id):
        """Informs the manager that the agent with the given ID was lost and has gone offline

        :param agent_id: The ID of the lost agent
        :type agent_id: str
        """

        # Remove new offers from the lost agent
        with self._new_offers_lock:
            for offer in self._new_offers.values():
                if offer.agent_id == agent_id:
                    del self._new_offers[offer.id]

        # Remove the lost agent
        with self._agent_resources_lock:
            if agent_id in self._agent_resources:
                del self._agent_resources[agent_id]

    def refresh_agent_resources(self, tasks, when):
        """Refreshes the agents with the current tasks that are running on them and with the new resource offers that
        have been added to the manager since the last time this method was called. Returns a dict containing all of the
        current offered resources and watermark resources for each agent.

        :param tasks: The current running tasks
        :type tasks: [:class:`job.tasks.base_task.Task`]
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: Dict where agent ID maps to a copy of the set of resources for the agent
        :rtype: dict
        """

        with self._new_offers_lock:
            new_offers = self._new_offers
            self._new_offers = {}

        # Group tasks and new offers by agent ID
        agent_offers = {}  # {Agent ID: [ResourceOffer]}
        agent_tasks = {}  # {Agent ID: [Tasks]}
        for offer in new_offers.values():
            if offer.agent_id not in agent_offers:
                agent_offers[offer.agent_id] = []
            agent_offers[offer.agent_id].append(offer)
        for task in tasks:
            if task.agent_id not in agent_tasks:
                agent_tasks[task.agent_id] = []
            agent_tasks[task.agent_id].append(task)

        results = {}

        with self._agent_resources_lock:
            # Create any new agents if this is their first offer
            for offer in new_offers.values():
                if offer.agent_id not in self._agent_resources:
                    self._agent_resources[offer.agent_id] = AgentResources(offer.agent_id)

            # Refresh agents
            for agent_resources in self._agent_resources.values():
                the_offers = agent_offers[agent_resources.agent_id] if agent_resources.agent_id in agent_offers else []
                the_tasks = agent_tasks[agent_resources.agent_id] if agent_resources.agent_id in agent_tasks else []
                resource_set = agent_resources.refresh_resources(the_offers, the_tasks)
                results[agent_resources.agent_id] = resource_set

            # Reset rolling watermarks if period has passed
            if not self._last_watermark_reset or when > self._last_watermark_reset + WATERMARK_RESET_PERIOD:
                for agent_resources in self._agent_resources.values():
                    agent_resources.reset_watermark()
                self._last_watermark_reset = when

        return results

    def rescind_offers(self, offer_ids):
        """Rescinds the offers with the given IDs from the manager

        :param offer_ids: The list of IDs of the offers to rescind
        :type offer_ids: list
        """

        with self._new_offers_lock:
            for offer_id in offer_ids:
                if offer_id in self._new_offers:
                    del self._new_offers[offer_id]

        with self._agent_resources_lock:
            for agent_resources in self._agent_resources.values():
                agent_resources.rescind_offers(offer_ids)

    def set_agent_shortages(self, agent_shortages):
        """Sets any resource shortages on the appropriate agents

        :param agent_shortages: Dict where resource shortage is stored by agent ID
        :type agent_shortages: dict
        """

        with self._agent_resources_lock:
            for agent_resources in self._agent_resources.values():
                if agent_resources.agent_id in agent_shortages:
                    agent_resources.set_shortage(agent_shortages[agent_resources.agent_id])
                else:
                    agent_resources.set_shortage()

    def sync_with_mesos(self, master_hostname, master_port):
        """Syncs with Mesos to retrieve the resouce totals needed by any agents

        :param master_hostname: The name of the Mesos master host
        :type master_hostname: string
        :param master_port: The port used by the Mesos master
        :type master_port: int
        """

        agents_needing_totals = set()
        with self._agent_resources_lock:
            for agent_resources in self._agent_resources.values():
                if not agent_resources.has_total_resources():
                    agents_needing_totals.add(agent_resources.agent_id)

        resources = {}
        try:
            resources = get_agent_resources(master_hostname, master_port, agents_needing_totals)
        except:
            logger.exception('Error getting agent resource totals from Mesos')

        with self._agent_resources_lock:
            for agent_id in resources:
                self._agent_resources[agent_id].set_total(resources[agent_id])

resource_mgr = ResourceManager()
