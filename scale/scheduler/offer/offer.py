"""Defines the class that represents resource offers"""


class ResourceOffer(object):
    """This class represents an offer of resources from a node. This class is thread-safe."""

    def __init__(self, offer_id, agent_id, node_resources):
        """Constructor

        :param offer_id: The ID of the offer
        :type offer_id: str
        :param agent_id: The agent ID of the node
        :type agent_id: str
        :param node_resources: The resources offered by the node
        :type node_resources: :class:`job.resources.NodeResources`
        """

        self._id = offer_id
        self._agent_id = agent_id
        self._node_resources = node_resources

    @property
    def id(self):
        """Returns the ID of this resource offer

        :returns: The ID of the offer
        :rtype: str
        """

        return self._id

    @property
    def agent_id(self):
        """Returns the agent ID of this resource offer

        :returns: The agent ID of the offer
        :rtype: str
        """

        return self._agent_id

    @property
    def node_resources(self):
        """Returns the resources of this offer

        :returns: The resources of the offer
        :rtype: :class:`job.resources.NodeResources`
        """

        return self._node_resources
