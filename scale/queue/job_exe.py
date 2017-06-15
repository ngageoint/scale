"""Defines the class that represents queued job executions being considered to be scheduled"""
from __future__ import unicode_literals

from job.resources import JobResources


class QueuedJobExecution(object):
    """This class represents a queued job execution that is being considered to be scheduled."""

    def __init__(self, queue):
        """Constructor

        :param queue: The queue model
        :type queue: :class:`queue.models.Queue`
        """

        self._queue = queue

        self._input_file_size = queue.input_file_size
        self._required_resources = queue.get_resources()

        self._provided_node_id = None
        self._provided_resources = None

    @property
    def id(self):
        """Returns the ID of this job execution

        :returns: The ID of this job execution
        :rtype: int
        """

        return self._queue.job_exe_id

    @property
    def provided_node_id(self):
        """Returns the ID of the node that has been provided to run this job execution

        :returns: The ID of the node that has been provided to run this job execution
        :rtype: int
        """

        return self._provided_node_id

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
        :rtype: :class:`node.resources.node_resources.NodeResources`
        """

        return self._required_resources

    def accepted(self, node_id, resources):
        """Indicates that this job execution has been accepted to be scheduled and passes the node and resources being
        provided

        :param node_id: The node ID
        :type node_id: int
        :param resources: The provided resources
        :type resources: :class:`node.resources.node_resources.NodeResources`
        """

        cpus = resources.cpus
        mem = resources.mem
        disk_total = resources.disk
        disk_out = disk_total - self._input_file_size
        self._provided_node_id = node_id
        self._provided_resources = JobResources(cpus=cpus, mem=mem, disk_in=self._input_file_size, disk_out=disk_out,
                                                disk_total=disk_total)
