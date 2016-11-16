"""Defines the class that represents nodes in the scheduler"""
from __future__ import unicode_literals

import logging
import threading
from collections import namedtuple


logger = logging.getLogger(__name__)
NodeState = namedtuple('NodeState', ['state', 'description'])


class Node(object):
    """This class represents a node in the scheduler. It combines information retrieved from the database node models as
    well as run-time information retrieved from Mesos. This class is thread-safe."""

    INACTIVE = NodeState(state='INACTIVE', description='Inactive, ignored by Scale')
    OFFLINE = NodeState(state='OFFLINE', description='Offline/unavailable')
    PAUSED = NodeState(state='PAUSED', description='Paused, no new jobs will be scheduled')
    INITIAL_CLEANUP = NodeState(state='INITIAL_CLEANUP', description='Performing initial cleanup')
    READY = NodeState(state='READY', description='Ready for new jobs')

    def __init__(self, agent_id, node):
        """Constructor

        :param agent_id: The Mesos agent ID for the node
        :type agent_id: string
        :param node: The node model
        :type node: :class:`node.models.Node`
        """

        self._agent_id = agent_id
        self._hostname = node.hostname  # Never changes
        self._id = node.id  # Never changes
        self._is_active = node.is_active
        self._is_initial_cleanup_completed = False
        self._is_online = True
        self._is_paused = node.is_paused
        self._lock = threading.Lock()
        self._port = node.port
        self._state = self.INACTIVE
        self._update_state()

    @property
    def agent_id(self):
        """Returns the agent ID of the node

        :returns: The agent ID
        :rtype: string
        """

        return self._agent_id

    @property
    def hostname(self):
        """Returns the hostname of the node

        :returns: The hostname
        :rtype: string
        """

        return self._hostname

    @property
    def id(self):
        """Returns the ID of the node

        :returns: The node ID
        :rtype: int
        """

        return self._id

    @property
    def is_active(self):
        """Indicates whether this node is active (True) or not (False)

        :returns: Whether this node is active
        :rtype: bool
        """

        return self._is_active

    @property
    def is_initial_cleanup_completed(self):
        """Indicates whether this node has its initial cleanup completed (True) or not (False)

        :returns: Whether this node has its initial cleanup completed
        :rtype: bool
        """

        return self._is_initial_cleanup_completed

    @property
    def is_online(self):
        """Indicates whether this node is online (True) or not (False)

        :returns: Whether this node is online
        :rtype: bool
        """

        return self._is_online

    @property
    def is_paused(self):
        """Indicates whether this node is paused (True) or not (False)

        :returns: Whether this node is paused
        :rtype: bool
        """

        return self._is_paused

    @property
    def state(self):
        """Returns the state of the node

        :returns: The state
        :rtype: :class:`scheduler.node.node_class.NodeState`
        """

        return self._state

    def initial_cleanup_completed(self):
        """Tells this node that its initial cleanup task has succeeded
        """

        logger.info('Node %s has completed initial clean up', self._hostname)
        with self._lock:
            self._is_initial_cleanup_completed = True
            self._update_state()

    def update_from_mesos(self, agent_id=None, port=None, is_online=None):
        """Updates this node's data from Mesos

        :param agent_id: The Mesos agent ID for the node
        :type agent_id: string
        :param port: The Mesos port of the node
        :type port: int
        :param is_online: Whether the Mesos agent is online
        :type is_online: bool
        """

        with self._lock:
            if agent_id:
                self._agent_id = agent_id
            if port:
                self._port = port
            if is_online is not None:
                self._is_online = is_online
            self._update_state()

    def update_from_model(self, node):
        """Updates this node's data from the database model

        :param node: The node model
        :type node: :class:`node.models.Node`
        """

        if self.id != node.id:
            raise Exception('Trying to update node from incorrect database model')

        with self._lock:
            self._is_active = node.is_active
            self._is_paused = node.is_paused
            self._update_state()

    def _update_state(self):
        """Updates the node's state. Caller must have obtained the node's thread lock.
        """

        if not self._is_active:
            self._state = self.INACTIVE
        elif not self._is_online:
            self._state = self.OFFLINE
        elif self._is_paused:
            self._state = self.PAUSED
        elif not self._is_initial_cleanup_completed:
            self._state = self.INITIAL_CLEANUP
        else:
            self._state = self.READY
