"""Defines the class that represents an agent's set of resource offers"""
from __future__ import unicode_literals

import datetime
import logging

from node.resources.node_resources import NodeResources

# Maximum time that each offer should be held
MAX_OFFER_HOLD_DURATION = datetime.timedelta(seconds=10)


logger = logging.getLogger(__name__)


class ResourceSet(object):
    """This class represents a set of resources on an agent"""

    def __init__(self, offered_resources=None, task_resources=None, watermark_resources=None):
        """Constructor

        :param offered_resources: The offered resources
        :type offered_resources: :class:`node.resources.node_resources.NodeResources`
        :param task_resources: The resources used by currently running tasks
        :type task_resources: :class:`node.resources.node_resources.NodeResources`
        :param watermark_resources: The watermark resources
        :type watermark_resources: :class:`node.resources.node_resources.NodeResources`
        """

        self.offered_resources = offered_resources if offered_resources else NodeResources()
        self.task_resources = task_resources if task_resources else NodeResources()
        self.watermark_resources = watermark_resources if watermark_resources else NodeResources()


class AgentResources(object):
    """This class represents an agent's set of resource offers."""

    def __init__(self, agent_id):
        """Constructor

        :param agent_id: The agent ID
        :type agent_id: string
        """

        self.agent_id = agent_id
        self._offers = {}  # {Offer ID: ResourceOffer}
        self._recent_watermark_resources = NodeResources()  # Recent watermark, used to provide a rolling watermark
        self._task_resources = NodeResources()  # Total resources for current tasks
        self._watermark_resources = NodeResources()  # Highest level of offer + task resources

        self._offer_resources = None  # Resources from offers
        self._shortage_resources = None  # Resources that agent needs to fulfill current obligations
        self._total_resources = None
        self._update_resources()

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
        self._update_resources()
        return allocated_offers.values()

    def generate_status_json(self, node_dict, total_running=None, total_offered=None, total_watermark=None, total=None):
        """Generates the portion of the status JSON that describes the resources for this agent

        :param node_dict: The dict for this agent's node within the status JSON
        :type node_dict: dict
        :param total_running: The total running resources to add up, possibly None
        :type total_running: :class:`node.resources.node_resources.NodeResources`
        :param total_offered: The total offered resources to add up, possibly None
        :type total_offered: :class:`node.resources.node_resources.NodeResources`
        :param total_watermark: The total watermark resources to add up, possibly None
        :type total_watermark: :class:`node.resources.node_resources.NodeResources`
        :param total: The total resources to add up, possibly None
        :type total: :class:`node.resources.node_resources.NodeResources`
        :returns: The total number of offers this agent has
        :rtype: int
        """

        if self._total_resources:
            total_resources = self._total_resources
        else:
            total_resources = self._watermark_resources
        free_resources = self._watermark_resources.copy()
        free_resources.subtract(self._task_resources)
        free_resources.subtract(self._offer_resources)
        unavailable_resources = total_resources.copy()
        unavailable_resources.subtract(self._watermark_resources)
        resources_dict = {}

        if total_running:
            total_running.add(self._task_resources)
        if total_offered:
            total_offered.add(self._offer_resources)
        if total_watermark:
            total_watermark.add(self._watermark_resources)
        if total:
            total.add(total_resources)
        self._task_resources.generate_status_json(resources_dict, 'running', total_resources)
        self._offer_resources.generate_status_json(resources_dict, 'offered', total_resources)
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
        #        resource_dict['unavailable'] = {'value': 0.0, 'percentage': 0.0}

        num_offers = len(self._offers)
        node_dict['num_offers'] = num_offers
        node_dict['resources'] = resources_dict
        return num_offers

    def has_total_resources(self):
        """Indicates whether this agent knows its total resources or not

        :returns: True if agent knows its total resources, False otherwise
        :rtype: bool
        """

        return self._total_resources is not None

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

        self._update_resources(tasks)

        offered_resources = self._offer_resources.copy()
        task_resources = self._task_resources.copy()
        watermark_resources = self._watermark_resources.copy()
        return ResourceSet(offered_resources, task_resources, watermark_resources)

    def rescind_offers(self, offer_ids):
        """Rescinds the offers with the given IDs

        :param offer_ids: The list of IDs of the offers to remove
        :type offer_ids: [str]
        """

        for offer_id in offer_ids:
            if offer_id in self._offers:
                offer = self._offers[offer_id]
                del self._offers[offer_id]
        self._update_resources()

    def reset_watermark(self):
        """Resets the agent's watermark to the highest recent value
        """

        self._watermark_resources = self._recent_watermark_resources
        self._recent_watermark_resources = NodeResources()
        self._update_resources()

    def set_shortage(self, shortage_resources=None):
        """Sets the resource shortage for the agent, if any

        :param shortage_resources: The resource shortage
        :type shortage_resources: :class:`node.resources.node_resources.NodeResources`
        """

        if shortage_resources:
            logger.warning('Agent %s has a shortage of %s', self.agent_id, shortage_resources)
            shortage_resources.round_values()
        self._shortage_resources = shortage_resources

    def set_total(self, total_resources):
        """Sets the total resources for the agent

        :param total_resources: The total resources
        :type total_resources: :class:`node.resources.node_resources.NodeResources`
        """

        self._total_resources = total_resources

    def _update_resources(self, tasks=None):
        """Updates the agent's resources from its current offers and tasks

        :param tasks: The new list of current tasks running on the agent, possibly None
        :type tasks: list
        """

        # Add up offered resources
        self._offer_resources = NodeResources()
        for offer in self._offers.values():
            self._offer_resources.add(offer.resources)

        # Recalculate task resources if needed
        if tasks is not None:
            self._task_resources = NodeResources()
            for task in tasks:
                self._task_resources.add(task.get_resources())

        # Increase watermark if needed
        available_resources = self._offer_resources.copy()
        available_resources.add(self._task_resources)
        self._watermark_resources.increase_up_to(available_resources)
        self._recent_watermark_resources.increase_up_to(available_resources)

        # Make sure watermark does not exceed total (can happen when we get task resources back before task update)
        if self._total_resources and not self._total_resources.is_sufficient_to_meet(self._watermark_resources):
            self._watermark_resources.limit_to(self._total_resources)
            self._recent_watermark_resources.limit_to(self._total_resources)
            # Since watermark was limited to not be higher than total, we're going to limit offered resources so that
            # offered + task = watermark
            max_offered = self._watermark_resources.copy()
            max_offered.subtract(self._task_resources)
            self._offer_resources.limit_to(max_offered)

        # Round values to deal with float precision issues
        self._offer_resources.round_values()
        self._task_resources.round_values()
        self._watermark_resources.round_values()
