"""Defines the class for a Docker pull task"""
from __future__ import unicode_literals

import datetime

from job.resources import NodeResources
from job.tasks.base_task import AtomicCounter, Task


PULL_TASK_ID_PREFIX = 'scale_pull'
COUNTER = AtomicCounter()


class PullTask(Task):
    """Represents a task that pulls Docker images from the registry. This class is thread-safe.
    """

    def __init__(self, framework_id, agent_id, image_name=None):
        """Constructor

        :param framework_id: The framework ID
        :type framework_id: string
        :param agent_id: The agent ID
        :type agent_id: string
        :param image_name: The name of the Docker image to pull. If None, pulls the Scale Docker image
        :type image_name: string
        """

        task_id = '%s_%s_%d' % (PULL_TASK_ID_PREFIX, framework_id, COUNTER.get_next())
        super(PullTask, self).__init__(task_id, 'Scale Docker Pull', agent_id)

        if image_name:
            self.image_name = image_name
        else:
            self.image_name = self._create_scale_image_name()

        self._uses_docker = False
        self._docker_image = None
        self._docker_params = []
        self._is_docker_privileged = False
        self._running_timeout_threshold = datetime.timedelta(minutes=15)
        self._staging_timeout_threshold = datetime.timedelta(minutes=2)

        # Create command that pulls image and deletes any dangling images
        pull_cmd = 'docker pull %s' % self.image_name
        delete_cmd = 'for img in `docker images -q -f dangling=true`; do docker rmi $img; done'
        self._command = '%s && %s' % (pull_cmd, delete_cmd)

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        return NodeResources(cpus=0.1, mem=32)
