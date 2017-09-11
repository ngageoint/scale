"""Defines the class for a message handler task"""
from __future__ import unicode_literals

from job.tasks.base_task import AtomicCounter
from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Mem
from scheduler.tasks.system_task import SystemTask


MSG_HANDLER_TASK_ID_PREFIX = 'scale_message_handler'
COUNTER = AtomicCounter()


class MessageHandlerTask(SystemTask):
    """Represents a task that runs a message handler for processing the backend messaging system. This class is
    thread-safe.
    """

    def __init__(self, framework_id):
        """Constructor

        :param framework_id: The framework ID
        :type framework_id: string
        """

        task_id = '%s_%s_%d' % (MSG_HANDLER_TASK_ID_PREFIX, framework_id, COUNTER.get_next())
        super(MessageHandlerTask, self).__init__(task_id, 'Scale Message Handler')

        self._add_database_docker_params()
        self._add_messaging_docker_params()
        self._command_arguments = 'scale_message_handler'

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        return NodeResources([Cpus(0.5), Mem(512.0)])
