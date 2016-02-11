"""Defines the class that manages all resource offers"""
import threading

from scheduler.offer.node import NodeOffers


class OfferManager(object):
    """This class manages all offers of resources from the cluster nodes. This class is thread-safe."""

    ACCEPTED = NodeOffers.ACCEPTED
    NOT_ENOUGH_CPUS = NodeOffers.NOT_ENOUGH_CPUS
    NOT_ENOUGH_MEM = NodeOffers.NOT_ENOUGH_MEM
    NOT_ENOUGH_DISK = NodeOffers.NOT_ENOUGH_DISK
    NO_OFFERS = NodeOffers.NO_OFFERS
    NODE_PAUSED = NodeOffers.NODE_PAUSED
    NODE_OFFLINE = NodeOffers.NODE_OFFLINE
    NO_NODES_AVAILABLE = 7

    def __init__(self):
        """Constructor
        """

        self._lock = threading.Lock()
        self._new_offers = {}  # {Offer ID: ResourceOffer}
        self._nodes_by_agent_id = {}  # {Agent ID: NodeOffers}
        self._nodes_by_node_id = {}  # {Node ID: NodeOffers}
        self._nodes_by_offer_id = {}  # {Offer ID: NodeOffers}

    def add_new_offers(self, offers):
        """Adds new resource offers to the manager

        :param offers: The list of new offers to add
        :type offers: [:class:`scheduler.offer.offer.ResourceOffer`]
        """

        with self._lock:
            for offer in offers:
                self._new_offers[offer.id] = offer

    def consider_new_job_exe(self, job_exe):
        """Considers the queued job execution to see if it can be run with the current offered resources

        :param job_exe: The queued job execution
        :type job_exe: :class:`queue.job_exe.QueuedJobExecution`
        :returns: One of the OfferManager constants indicating if the new job execution was accepted or why it was not
            accepted
        :rtype: int
        """

        with self._lock:
            num_not_enough_cpus = 0
            num_not_enough_mem = 0
            num_not_enough_disk = 0

            for node_offers in self._nodes_by_node_id.values():
                if not job_exe.is_node_acceptable(node_offers.node.id):
                    continue
                result = node_offers.consider_new_job_exe(job_exe)
                if result == OfferManager.ACCEPTED:
                    return result
                elif result == OfferManager.NOT_ENOUGH_CPUS:
                    num_not_enough_cpus += 1
                elif result == OfferManager.NOT_ENOUGH_MEM:
                    num_not_enough_mem += 1
                elif result == OfferManager.NOT_ENOUGH_DISK:
                    num_not_enough_disk += 1

            max_num = max(num_not_enough_cpus, num_not_enough_mem, num_not_enough_disk)
            if max_num == 0:
                return OfferManager.NO_NODES_AVAILABLE
            elif max_num == num_not_enough_cpus:
                return OfferManager.NOT_ENOUGH_CPUS
            elif max_num == num_not_enough_mem:
                return OfferManager.NOT_ENOUGH_MEM
            else:
                return OfferManager.NOT_ENOUGH_DISK

    def consider_next_task(self, job_exe):
        """Considers the currently running job execution to see if its next task can be run with the current offered
        resources

        :param job_exe: The running job execution
        :type job_exe: :class:`job.execution.running.job_exe.RunningJobExecution`
        :returns: One of the OfferManager constants indicating if the next task was accepted or why it was not accepted
        :rtype: int
        """

        with self._lock:
            if job_exe.node_id not in self._nodes_by_node_id:
                return OfferManager.NODE_OFFLINE

            node_offers = self._nodes_by_node_id[job_exe.node_id]
            return node_offers.consider_next_task(job_exe)

    def lost_node(self, agent_id):
        """Informs the manager that the node with the given agent ID was lost and has gone offline

        :param agent_id: The agent ID of the lost node
        :type agent_id: str
        """

        with self._lock:
            if agent_id in self._nodes_by_agent_id:
                node_offers = self._nodes_by_agent_id[agent_id]
                node_offers.lost_node()

    def pop_all_offers(self):
        """Removes and returns all sets of node offers

        :returns: The list of all sets of node offers
        :rtype: [:class:`scheduler.offer.node.NodeOffers`]
        """

        offers_list = []

        with self._lock:
            for node_offers in self._nodes_by_node_id.values():
                self._remove_node_offers(node_offers)
                self._create_node_offers(node_offers.node)
                offers_list.append(node_offers)

        return offers_list

    def pop_offers_with_accepted_job_exes(self):
        """Removes and returns all sets of node offers that have accepted job executions

        :returns: The list of all sets of node offers that have accepted job executions
        :rtype: [:class:`scheduler.offer.node.NodeOffers`]
        """

        offers_list = []

        with self._lock:
            for node_offers in self._nodes_by_node_id.values():
                if node_offers.has_accepted_job_exes():
                    self._remove_node_offers(node_offers)
                    self._create_node_offers(node_offers.node)
                    offers_list.append(node_offers)

        return offers_list

    def ready_new_offers(self):
        """Readies the new resource offers that have been added to the manager since the last time this method was
        called
        """

        with self._lock:
            for offer in self._new_offers.values():
                if offer.agent_id in self._nodes_by_agent_id:
                    node_offers = self._nodes_by_agent_id[offer.agent_id]
                    node_offers.add_offer(offer)
                    self._nodes_by_offer_id[offer.id] = node_offers

    def remove_offers(self, offer_ids):
        """Removes the offers with the given IDs from the manager

        :param offer_ids: The list of IDs of the offers to remove
        :type offer_ids: [str]
        """

        with self._lock:
            for offer_id in offer_ids:
                if offer_id in self._new_offers:
                    del self._new_offers[offer_id]
                if offer_id in self._nodes_by_offer_id:
                    node_offers = self._nodes_by_offer_id[offer_id]
                    node_offers.remove_offer(offer_id)
                    self._remove_node_offers(node_offers)

    def update_nodes(self, nodes):
        """Updates the manager with the latest copies of the node models

        :param nodes: The list of updated node models
        :type nodes: [:class:`node.models.Node`]
        """

        with self._lock:
            for node in nodes:
                if node.id in self._nodes_by_node_id:
                    node_offers = self._nodes_by_node_id[node.id]
                    if node_offers.node.slave_id == node.slave_id and node.is_active:
                        # No change in agent ID, just update node model
                        node_offers.node = node
                    else:
                        # Agent ID changed or node no longer active, so delete old node offers
                        self._remove_node_offers(node_offers)
                if node.id not in self._nodes_by_node_id and node.is_active:
                    # Create new node offers
                    self._create_node_offers(node)

    def _create_node_offers(self, node):
        """Creates a set of node offers for the given node

        :param node: The node model
        :type node: :class:`node.models.Node`
        """

        node_offers = NodeOffers(node)
        self._nodes_by_node_id[node.id] = node_offers
        self._nodes_by_agent_id[node.slave_id] = node_offers

    def _remove_node_offers(self, node_offers):
        """Removes the given set of node offers from the manager

        :param node_offers: The set of node offers to remove
        :type node_offers: :class:`scheduler.offer.node.NodeOffers`
        """

        del self._nodes_by_agent_id[node_offers.node.slave_id]
        del self._nodes_by_node_id[node_offers.node.id]
        for offer_id in node_offers.offer_ids:
            del self._nodes_by_offer_id[offer_id]
