"""Defines the class that represents queued job executions being considered to be scheduled"""
from job.resources import JobResources


class QueuedJobExecution(object):
    """This class represents a queued job execution that is being considered to be scheduled."""

    def __init__(self, queue):
        """Constructor

        :param queue: The queue model
        :type queue: :class:`queue.models.Queue`
        """

        self.queue = queue

        cpus = self.queue.cpus_required
        mem = self.queue.mem_required
        disk_in = self.queue.disk_in_required
        disk_out = self.queue.disk_out_required
        disk_total = self.queue.disk_total_required
        self.required_resources = JobResources(cpus=cpus, mem=mem, disk_in=disk_in, disk_out=disk_out,
                                               disk_total=disk_total)
        # TODO: populate this from queue model
        self.required_node_ids = []

        self.provided_node = None
        self.provided_resources = None

    def accepted(self, node, resources):
        """Indicates that this job execution has been accepted to be scheduled and passes the node and resources being
        provided

        :param node: The node model
        :type node: :class:`node.models.Node`
        :param resources: The provided resources
        :type resources: :class:`job.resources.JobResources`
        """

        self.provided_node = node
        self.provided_resources = resources
