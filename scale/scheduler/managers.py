"""Defines the class that holds all of the various data managers in the scheduler"""
from __future__ import unicode_literals

from scheduler.cleanup.manager import CleanupManager
from scheduler.node.manager import NodeManager


# TODO: add the remaining managers to this class, can move the initial database sync into this class
class SchedulerManagers(object):
    """This class holds all of the various data managers in the scheduler."""

    def __init__(self):
        """Constructor
        """

        self.cleanup = CleanupManager()
        self.node = NodeManager()
