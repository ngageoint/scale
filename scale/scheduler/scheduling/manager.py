"""Defines the class that manages all scheduling"""
from __future__ import unicode_literals


class SchedulingManager(object):
    """This class manages all scheduling. This class is NOT thread-safe and should only be used within the scheduling
    thread.
    """

    def __init__(self):
        """Constructor
        """

        self._waiting_tasks = {}  # {Task ID: int}

    def perform_scheduling(self):
        """Organizes and analyzes the cluster resources, schedules new job executions, and launches tasks
        """

        # TODO: implement
        pass

    # TODO: create scheduling/node.py for a class to hold the resources/tasks for a node during a round of scheduling
    # TODO: for first step of scheduling, create private method that grabs current tasks and nodes,
    # uses the resource_mgr, and ultimately creates and returns the node classes with resources and tasks