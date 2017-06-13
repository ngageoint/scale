"""Defines the class that represents an agent's set of resource offers"""
from __future__ import unicode_literals

import datetime
import logging
from collections import namedtuple

from node.resources.node_resources import NodeResources

# Maximum time that each offer should be held
MAX_OFFER_HOLD_DURATION = datetime.timedelta(seconds=10)

ResourceSet = namedtuple('ResourceSet', ['offered_resources', 'task_resources', 'watermark_resources'])

logger = logging.getLogger(__name__)


class AgentResources(object):
    """This class represents an agent's set of resource offers."""

    def __init__(self, agent_id):
        """Constructor

        :param agent_id: The agent ID
        :type agent_id: string
        """

        self.agent_id = agent_id
        self._offers = {}  # {Offer ID: ResourceOffer}
        self._offer_resources = NodeResources()  # Total resources from offers
        self._shortage_resources = NodeResources()  # Resources that agent needs to fulfill current obligations
        self._task_resources = NodeResources()  # Total resources for current tasks
        self._watermark_resources = NodeResources()  # Highest level of offer + task resources
        self._recent_watermark_resources = NodeResources()  # Recent watermark, used to provide a rolling watermark

    def allocate_offers(self, resources, when):
        """Directs the agent to allocate offers sufficient to match the given resources. Any offers that have been held
        too long will automatically be included. It's possible that the offer resources returned are less than
        requested.

        :param resources: The requested resources
        :type resources: :class:`node.resources.node_resources.NodeResources`
        :param when: The current time
        :type when: :class:`datetime.datetime`
        :returns: The list of allocated offers
        :rtype: [:class:`scheduler.resources.offer.ResourceOffer`]
        """

        allocated_offers = {}
        allocated_resources = NodeResources()
        available_offer_ids = set(self._offers.keys())
        # Automatically include all offers that have been held too long
        for offer in self._offers.values():
            if when - offer.received >= MAX_OFFER_HOLD_DURATION:
                allocated_offers[offer.id] = offer
                allocated_resources.add(offer.resources)
                available_offer_ids.discard(offer.id)

        if self._offer_resources.is_sufficient_to_meet(resources):
            # We have enough resources to meet the request, so keep allocating offers until we get enough
            while not allocated_resources.is_sufficient_to_meet(resources):
                offer_id = available_offer_ids.pop()
                offer = self._offers[offer_id]
                allocated_offers[offer_id] = offer
                allocated_resources.add(offer.resources)

        # Remove allocated offers and return them
        for offer in allocated_offers.values():
            del self._offers[offer.id]
        self._offer_resources.subtract(allocated_resources)
        return allocated_offers.values()

    def generate_status_json(self, node_dict, total_running, total_offered, total_watermark):
        """Generates the portion of the status JSON that describes the resources for this agent

        :param node_dict: The dict for this agent's node within the status JSON
        :type node_dict: dict
        :param total_running: The total running resources to add up
        :type total_running: :class:`node.resources.node_resources.NodeResources`
        :param total_offered: The total offered resources to add up
        :type total_offered: :class:`node.resources.node_resources.NodeResources`
        :param total_watermark: The total watermark resources to add up
        :type total_watermark: :class:`node.resources.node_resources.NodeResources`
        """

        running_dict = {}
        self._task_resources.generate_status_json(running_dict)
        total_running.add(self._task_resources)
        offered_dict = {}
        self._offer_resources.generate_status_json(offered_dict)
        total_offered.add(self._offer_resources)
        watermark_dict = {}
        self._watermark_resources.generate_status_json(watermark_dict)
        total_watermark.add(self._watermark_resources)

        node_dict['resources'] = {'num_offers': len(self._offers), 'running': running_dict, 'offered': offered_dict,
                                  'watermark': watermark_dict}

        if self._shortage_resources:
            shortage_dict = {}
            self._shortage_resources.generate_status_json(shortage_dict)
            node_dict['resources']['shortage'] = shortage_dict

    def refresh_resources(self, offers, tasks):
        """Refreshes the agent's resources by setting the current running tasks and adding new resource offers. Returns
        a copy of the set of resources for the agent.

        :param offers: The new resource offers to add
        :type offers: [:class:`scheduler.resources.offer.ResourceOffer`]
        :param tasks: The current tasks running on the agent
        :type tasks: [:class:`job.tasks.base_task.Task`]
        :returns: A copy of the set of agent resources
        :rtype: :class:`scheduler.resources.agent.ResourceSet`
        """

        # Add new offers
        for offer in offers:
            if offer.id not in self._offers:
                self._offers[offer.id] = offer
                self._offer_resources.add(offer.resources)

        # Recalculate task resources
        self._task_resources = NodeResources()
        for task in tasks:
            self._task_resources.add(task.get_resources())

        # Increase watermark if needed
        total_resources = NodeResources()
        total_resources.add(self._offer_resources)
        total_resources.add(self._task_resources)
        self._watermark_resources.increase_up_to(total_resources)
        self._recent_watermark_resources.increase_up_to(total_resources)

        offered_resources = NodeResources()
        task_resources = NodeResources()
        watermark_resources = NodeResources()
        offered_resources.add(self._offer_resources)
        task_resources.add(self._task_resources)
        watermark_resources.add(self._watermark_resources)
        return ResourceSet(offered_resources, task_resources, watermark_resources)

    def rescind_offers(self, offer_ids):
        """Rescinds the offers with the given IDs

        :param offer_ids: The list of IDs of the offers to remove
        :type offer_ids: [str]
        """

        for offer_id in offer_ids:
            if offer_id in self._offers:
                offer = self._offers[offer_id]
                self._offer_resources.subtract(offer.resources)
                del self._offers[offer_id]

    def reset_watermark(self):
        """Resets the agent's watermark to the highest recent value
        """

        self._watermark_resources = self._recent_watermark_resources
        self._recent_watermark_resources = NodeResources()

    def set_shortage(self, shortage_resources=None):
        """Sets the resource shortage for the agent, if any

        :param shortage_resources: The resource shortage
        :type shortage_resources: :class:`node.resources.node_resources.NodeResources`
        """

        if shortage_resources:
            logger.warning('Agent %s has a shortage of %s', self.agent_id, shortage_resources.to_logging_string())
        self._shortage_resources = shortage_resources
