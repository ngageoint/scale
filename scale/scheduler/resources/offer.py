"""Defines the class that represents resource offers"""
from __future__ import unicode_literals


class ResourceOffer(object):
    """This class represents an offer of resources from a node."""

    def __init__(self, offer_id, agent_id, node_resources):
        """Constructor

        :param offer_id: The ID of the offer
        :type offer_id: string
        :param agent_id: The agent ID of the node
        :type agent_id: string
        :param node_resources: The resources offered by the node
        :type node_resources: :class:`job.resources.NodeResources`
        """

        self.id = offer_id
        self.agent_id = agent_id
        self.resources = node_resources
        self.generation = 1  # Number of generations (loops) this offer has been through the scheduling thread
