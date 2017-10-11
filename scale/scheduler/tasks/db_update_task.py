"""Defines the class for a database update task"""
from __future__ import unicode_literals

from job.tasks.base_task import AtomicCounter
from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Mem
from scheduler.tasks.system_task import SystemTask


DB_UPDATE_TASK_ID_PREFIX = 'scale_db_update'
COUNTER = AtomicCounter()


class DatabaseUpdateTask(SystemTask):
    """Represents a task that updates the Scale database. This class is thread-safe.
    """

    def __init__(self, framework_id):
        """Constructor

        :param framework_id: The framework ID
        :type framework_id: string
        """

        task_id = '%s_%s_%d' % (DB_UPDATE_TASK_ID_PREFIX, framework_id, COUNTER.get_next())
        super(DatabaseUpdateTask, self).__init__(task_id, 'Scale Database Update')

        self._add_database_docker_params()
        self._command_arguments = 'scale_db_update'

        # System task properties
        self.task_type = 'db-update'
        self.title = 'Database Update'
        self.description = 'Updates the Scale database to the current version'

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        return NodeResources([Cpus(0.5), Mem(512.0)])
