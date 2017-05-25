"""Defines the class that represents an agent's set of resource offers"""
from __future__ import unicode_literals

from job.resources import NodeResources


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

    def generate_status_json(self, node_dict, total_running, total_offered, total_watermark):
        """Generates the portion of the status JSON that describes the resources for this agent

        :param node_dict: The dict for this agent's node within the status JSON
        :type node_dict: dict
        :param total_running: The total running resources to add up
        :type total_running: :class:`job.resources.NodeResources`
        :param total_offered: The total offered resources to add up
        :type total_offered: :class:`job.resources.NodeResources`
        :param total_watermark: The total watermark resources to add up
        :type total_watermark: :class:`job.resources.NodeResources`
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

        node_dict['resources'] = {'running': running_dict, 'offered': offered_dict, 'watermark': watermark_dict}

        if self._shortage_resources:
            shortage_dict = {}
            self._shortage_resources.generate_status_json(shortage_dict)
            node_dict['resources']['shortage'] = shortage_dict

    def refresh_resources(self, offers, tasks):
        """Refreshes the agent's resources by setting the current running tasks and adding new resource offers

        :param offers: The new resource offers to add
        :type offers: [:class:`scheduler.resources.offer.ResourceOffer`]
        :param tasks: The current tasks running on the agent
        :type tasks: [:class:`job.tasks.base_task.Task`]
        """

        # Add new offers
        for offer in offers:
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

    def remove_offers(self, offer_ids):
        """Removes the offers with the given IDs

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
        :type shortage_resources: [:class:`job.resources.NodeResources`]
        """

        self._shortage_resources = shortage_resources
