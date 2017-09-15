"""Defines the class that represents queued job executions being considered for scheduling"""
from __future__ import unicode_literals

from job.models import JobExecution
from node.resources.node_resources import NodeResources


class QueuedJobExecution(object):
    """This class represents a queued job execution that is being considered for scheduling"""

    def __init__(self, queue):
        """Constructor

        :param queue: The queue model
        :type queue: :class:`queue.models.Queue`
        """

        self.id = queue.id
        self.is_canceled = queue.is_canceled
        self.configuration = queue.get_execution_configuration()
        self.interface = queue.get_job_interface()
        self.priority = queue.priority
        self.required_resources = queue.get_resources()
        self.scheduled_agent_id = None

        self._queue = queue
        self._scheduled_node_id = None
        self._scheduled_resources = None

    def create_job_exe_model(self, framework_id, when):
        """Creates and returns a scheduled job execution model

        :param framework_id: The scheduling framework ID
        :type framework_id: string
        :param when: The start time
        :type when: :class:`datetime.datetime`
        :returns: The job execution model
        :rtype: :class:`job.models.JobExecution`
        """

        job_exe = JobExecution()
        job_exe.job_id = self._queue.job_id
        job_exe.job_type_id = self._queue.job_type_id
        job_exe.exe_num = self._queue.exe_num
        job_exe.timeout = self._queue.timeout
        job_exe.input_file_size = self._queue.input_file_size
        job_exe.configuration = self.configuration.get_dict()
        job_exe.queued = self._queue.queued

        if self.is_canceled:
            job_exe.node_id = None
            job_exe.resources = NodeResources().get_json().get_dict()
            job_exe.started = None
        else:
            job_exe.node_id = self._scheduled_node_id
            job_exe.resources = self._scheduled_resources.get_json().get_dict()
            job_exe.started = when

        job_exe.set_cluster_id(framework_id, self._queue.job_id, self._queue.exe_num)

        return job_exe

    def scheduled(self, agent_id, node_id, resources):
        """Indicates that this job execution has been scheduled on a node and passes the agent, node, and resource
        information

        :param agent_id: The agent ID
        :type agent_id: string
        :param node_id: The node ID
        :type node_id: int
        :param resources: The scheduled resources
        :type resources: :class:`node.resources.node_resources.NodeResources`
        """

        self.scheduled_agent_id = agent_id
        self._scheduled_node_id = node_id
        self._scheduled_resources = resources
