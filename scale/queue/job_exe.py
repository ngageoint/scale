"""Defines the class that represents queued job executions being considered to be scheduled"""
from job.resources import JobResources


class QueuedJobExecution(object):
    """This class represents a queued job execution that is being considered to be scheduled."""

    def __init__(self, queue):
        """Constructor

        :param queue: The queue model
        :type queue: :class:`queue.models.Queue`
        """

        self._queue = queue

        cpus = self._queue.cpus_required
        mem = self._queue.mem_required
        disk_in = self._queue.disk_in_required
        disk_out = self._queue.disk_out_required
        disk_total = self._queue.disk_total_required
        self._required_resources = JobResources(cpus=cpus, mem=mem, disk_in=disk_in, disk_out=disk_out,
                                                disk_total=disk_total)

        self._required_node_ids = None
        if self._queue.node_required_id:
            self._required_node_ids = {self._queue.node_required_id}

        self._provided_node = None
        self._provided_resources = None

    @property
    def id(self):
        """Returns the ID of this job execution

        :returns: The ID of this job execution
        :rtype: int
        """

        return self._queue.job_exe_id

    @property
    def provided_node(self):
        """Returns the node that has been provided to run this job execution

        :returns: The node that has been provided to run this job execution
        :rtype: :class:`node.models.Node`
        """

        return self._provided_node

    @property
    def provided_resources(self):
        """Returns the resources that have been provided to run this job execution

        :returns: The resources that have been provided to run this job execution
        :rtype: :class:`job.resources.JobResources`
        """

        return self._provided_resources

    @property
    def queue(self):
        """Returns the queue model for this job execution

        :returns: The queue model for this job execution
        :rtype: :class:`queue.models.Queue`
        """

        return self._queue

    @property
    def required_resources(self):
        """Returns the resources required by this job execution

        :returns: The resources required by this job execution
        :rtype: :class:`job.resources.JobResources`
        """

        return self._required_resources

    def accepted(self, node, resources):
        """Indicates that this job execution has been accepted to be scheduled and passes the node and resources being
        provided

        :param node: The node model
        :type node: :class:`node.models.Node`
        :param resources: The provided resources
        :type resources: :class:`job.resources.JobResources`
        """

        self._provided_node = node
        self._provided_resources = resources

    def is_node_acceptable(self, node_id):
        """Indicates whether the node with the given ID is acceptable to this job execution

        :param node_id: The node ID
        :type node_id: int
        :returns: True if the node is acceptable, False otherwise
        :rtype: bool
        """

        return self._required_node_ids is None or node_id in self._required_node_ids
