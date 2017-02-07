"""Defines the class for a node health check task"""
from __future__ import unicode_literals

import datetime

from job.resources import NodeResources
from job.tasks.base_task import AtomicCounter, Task


HEALTH_TASK_ID_PREFIX = 'scale_health'
COUNTER = AtomicCounter()


class HealthTask(Task):
    """Represents a task that performs a health check on a node. This class is thread-safe.
    """

    def __init__(self, framework_id, agent_id):
        """Constructor

        :param framework_id: The framework ID
        :type framework_id: string
        :param agent_id: The agent ID
        :type agent_id: string
        """

        task_id = '%s_%s_%d' % (HEALTH_TASK_ID_PREFIX, framework_id, COUNTER.get_next())
        super(HealthTask, self).__init__(task_id, 'Scale Health Check', agent_id)

        self._uses_docker = False
        self._docker_image = None
        self._force_docker_pull = False
        self._docker_params = []
        self._is_docker_privileged = False
        self._running_timeout_threshold = datetime.timedelta(minutes=15)
        self._staging_timeout_threshold = datetime.timedelta(minutes=2)

        # Create command that performs health check
        self._command = 'echo Healthy!'

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        return NodeResources(cpus=0.1, mem=32)
