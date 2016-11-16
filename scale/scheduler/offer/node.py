"""Defines the class that represents the set of all resource offers for a node"""
from __future__ import unicode_literals

import threading

from scheduler.node.node_class import Node


class NodeOffers(object):
    """This class represents the set of all resource offers for a node. This class is thread-safe."""

    ACCEPTED = 0
    TASK_INVALID = 1
    NOT_ENOUGH_CPUS = 2
    NOT_ENOUGH_MEM = 3
    NOT_ENOUGH_DISK = 4
    NO_OFFERS = 5
    NODE_PAUSED = 6
    NODE_OFFLINE = 7
    NODE_NOT_READY = 8

    def __init__(self, node):
        """Constructor

        :param node: The node model
        :type node: :class:`scheduler.node.node_class.Node`
        """

        self._node = node
        self._lock = threading.Lock()
        # TODO: remove
        from util.lock import DebugLock
        self._lock = DebugLock()

        self._available_cpus = 0.0
        self._available_mem = 0.0
        self._available_disk = 0.0
        self._offers = {}  # {Offer ID: Offer}
        self._accepted_new_job_exes = {}  # {Job Exe ID: Job Exe}
        self._accepted_running_job_exes = {}  # {Job Exe ID: Job Exe}
        self._accepted_tasks = []

    @property
    def node(self):
        """Returns the node

        :returns: The node
        :rtype: :class:`scheduler.node.node_class.Node`
        """

        return self._node

    @node.setter
    def node(self, value):
        """Sets the node

        :param value: The node
        :type value: :class:`scheduler.node.node_class.Node`
        """

        with self._lock:
            self._node = value

    @property
    def offer_ids(self):
        """Returns the list of offer IDs

        :returns: The offer IDs
        :rtype: [str]
        """

        with self._lock:
            return list(self._offers.keys())

    def add_offer(self, offer):
        """Adds the given offer to this node set

        :param offer: The offer to add
        :type offer: :class:`scheduler.offer.offer.ResourceOffer`
        """

        if offer.agent_id != self._node.agent_id:
            raise Exception('Offer has invalid agent ID')

        with self._lock:
            if offer.id in self._offers:
                return

            resources = offer.node_resources
            self._available_cpus += resources.cpus
            self._available_mem += resources.mem
            self._available_disk += resources.disk
            self._offers[offer.id] = offer

    def consider_new_job_exe(self, job_exe):
        """Considers the queued job execution to see if it can be run on this node with the current resources

        :param job_exe: The queued job execution
        :type job_exe: :class:`queue.job_exe.QueuedJobExecution`
        :returns: One of the NodeOffers constants indicating if the new job execution was accepted or why it was not
            accepted
        :rtype: int
        """

        with self._lock:
            if job_exe.id in self._accepted_new_job_exes:
                return NodeOffers.ACCEPTED
            if not self._node.is_online:
                return NodeOffers.NODE_OFFLINE
            if self._node.is_paused:
                return NodeOffers.NODE_PAUSED
            if self._node.state != Node.READY:
                return NodeOffers.NODE_NOT_READY
            if len(self._offers) == 0:
                return NodeOffers.NO_OFFERS

            required_resources = job_exe.required_resources
            if self._available_cpus < required_resources.cpus:
                return NodeOffers.NOT_ENOUGH_CPUS
            if self._available_mem < required_resources.mem:
                return NodeOffers.NOT_ENOUGH_MEM
            if self._available_disk < required_resources.disk_total:
                return NodeOffers.NOT_ENOUGH_DISK
            provided_resources = required_resources

            self._available_cpus -= provided_resources.cpus
            self._available_mem -= provided_resources.mem
            self._available_disk -= provided_resources.disk_total
            job_exe.accepted(self._node.id, provided_resources)
            self._accepted_new_job_exes[job_exe.id] = job_exe
            return NodeOffers.ACCEPTED

    def consider_next_task(self, job_exe):
        """Considers the currently running job execution to see if its next task can be run on this node with the
        current resources

        :param job_exe: The running job execution
        :type job_exe: :class:`job.execution.running.job_exe.RunningJobExecution`
        :returns: One of the NodeOffers constants indicating if the next task was accepted or why it was not accepted
        :rtype: int
        """

        with self._lock:
            if job_exe.id in self._accepted_running_job_exes:
                return NodeOffers.ACCEPTED
            if not self._node.is_online:
                return NodeOffers.NODE_OFFLINE
            if len(self._offers) == 0:
                return NodeOffers.NO_OFFERS

            required_resources = job_exe.next_task_resources()
            if not required_resources:
                return NodeOffers.TASK_INVALID
            if self._available_cpus < required_resources.cpus:
                return NodeOffers.NOT_ENOUGH_CPUS
            if self._available_mem < required_resources.mem:
                return NodeOffers.NOT_ENOUGH_MEM
            if self._available_disk < required_resources.disk:
                return NodeOffers.NOT_ENOUGH_DISK

            self._available_cpus -= required_resources.cpus
            self._available_mem -= required_resources.mem
            self._available_disk -= required_resources.disk
            self._accepted_running_job_exes[job_exe.id] = job_exe
            return NodeOffers.ACCEPTED

    def consider_task(self, task):
        """Considers if the given task can be run on this node with the current resources

        :param task: The task to consider
        :type task: :class:`job.execution.running.tasks.base_task.Task`
        :returns: One of the NodeOffers constants indicating if the task was accepted or why it was not accepted
        :rtype: int
        """

        with self._lock:
            if self._node.agent_id != task.agent_id:
                return NodeOffers.TASK_INVALID
            if not self._node.is_online:
                return NodeOffers.NODE_OFFLINE
            if len(self._offers) == 0:
                return NodeOffers.NO_OFFERS

            required_resources = task.get_resources()
            if not required_resources:
                return NodeOffers.TASK_INVALID
            if self._available_cpus < required_resources.cpus:
                return NodeOffers.NOT_ENOUGH_CPUS
            if self._available_mem < required_resources.mem:
                return NodeOffers.NOT_ENOUGH_MEM
            if self._available_disk < required_resources.disk:
                return NodeOffers.NOT_ENOUGH_DISK

            self._available_cpus -= required_resources.cpus
            self._available_mem -= required_resources.mem
            self._available_disk -= required_resources.disk
            self._accepted_tasks.append(task)
            return NodeOffers.ACCEPTED

    def get_accepted_new_job_exes(self):
        """Returns all of the new job executions that have been accepted to run on this node

        :returns: The list of all accepted new job executions
        :rtype: [:class:`queue.job_exe.QueuedJobExecution`]
        """

        job_exes = []
        with self._lock:
            for job_exe_id in self._accepted_new_job_exes:
                job_exes.append(self._accepted_new_job_exes[job_exe_id])
        return job_exes

    def get_accepted_running_job_exes(self):
        """Returns all of the running job executions that have been accepted to run their next tasks on this node

        :returns: The list of all accepted running job executions
        :rtype: [:class:`job.execution.running.job_exe.RunningJobExecution`]
        """

        job_exes = []
        with self._lock:
            for job_exe_id in self._accepted_running_job_exes:
                job_exes.append(self._accepted_running_job_exes[job_exe_id])
        return job_exes

    def get_accepted_tasks(self):
        """Returns all of the tasks that have been accepted to run on this node

        :returns: The list of all accepted tasks
        :rtype: [:class:`job.execution.running.tasks.base_task.Task`]
        """

        tasks = []
        with self._lock:
            for task in self._accepted_tasks:
                tasks.append(task)
        return tasks

    def has_accepted_job_exes(self):
        """Indicates whether any job executions have been accepted

        :returns: True if any job executions have been accepted, False otherwise
        :rtype: bool
        """

        with self._lock:
            return len(self._accepted_new_job_exes) or len(self._accepted_running_job_exes) or len(self._accepted_tasks)

    def lost_node(self):
        """Informs the set of offers that the node was lost and has gone offline
        """

        with self._lock:
            # All offers and accepted job executions are lost
            self._available_cpus = 0.0
            self._available_mem = 0.0
            self._available_disk = 0.0
            self._offers = {}
            self._accepted_new_job_exes = {}
            self._accepted_running_job_exes = {}
            self._accepted_tasks = []

    def remove_offer(self, offer_id):
        """Removes the offer with the given ID from this node set, resetting any accepted job executions if there are no
        longer the resources to support them

        :param offer_id: The ID of the offer to remove
        :type offer_id: str
        """

        with self._lock:
            if offer_id not in self._offers:
                return

            offer = self._offers[offer_id]
            resources_lost = offer.node_resources
            self._available_cpus -= resources_lost.cpus
            self._available_mem -= resources_lost.mem
            self._available_disk -= resources_lost.disk
            del self._offers[offer.id]

            if self._available_cpus < 0 or self._available_mem < 0 or self._available_disk < 0:
                # Lost too many resources, dump previously accepted job executions
                self._accepted_running_job_exes = {}
                self._accepted_new_job_exes = {}
                self._accepted_tasks = []
                self._available_cpus = 0
                self._available_mem = 0
                self._available_disk = 0
                for offer_id in self._offers:
                    resources = self._offers[offer_id].node_resources
                    self._available_cpus += resources.cpus
                    self._available_mem += resources.mem
                    self._available_disk += resources.disk
