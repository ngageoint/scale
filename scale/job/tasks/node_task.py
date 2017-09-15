"""Defines the abstract base class for all node tasks"""
from __future__ import unicode_literals

from abc import ABCMeta

from job.tasks.base_task import Task


class NodeTask(Task):
    """Abstract base class for a node task
    """

    __metaclass__ = ABCMeta

    def __init__(self, task_id, task_name, agent_id):
        """Constructor

        :param task_id: The unique ID of the task
        :type task_id: string
        :param task_name: The name of the task
        :type task_name: string
        :param agent_id: The ID of the agent on which the task is launched
        :type agent_id: string
        """

        super(NodeTask, self).__init__(task_id, task_name, agent_id)

        # Node task properties that sub-classes should override
        self.task_type = None
        self.title = task_name
        self.description = None
