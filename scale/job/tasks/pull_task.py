"""Defines the class for a Docker pull task"""
from __future__ import unicode_literals

import datetime

from django.conf import settings

from job.tasks.base_task import AtomicCounter, Task
from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Mem


PULL_TASK_ID_PREFIX = 'scale_pull'
COUNTER = AtomicCounter()


def create_pull_command(image_name, check_exists=False):
    """Creates the Docker pull command to pull the given image name

    :param image_name: The name of the Docker image to pull
    :type image_name: string
    :param check_exists: If True, skips pull if image already exists, False pulls image regardless
    :type check_exists: bool
    :returns: The Docker pull command
    :rtype: string
    """

    # Create command that pulls image and deletes any dangling images
    pull_echo_cmd = 'echo \'Pulling image...\''
    pull_cmd = 'docker pull %s' % image_name
    delete_echo_cmd = 'echo \'Cleaning up dangling images...\''
    delete_cmd = 'for img in `docker images -q -f dangling=true`; do docker rmi $img; done'
    command = '%s && %s && %s && %s' % (pull_echo_cmd, pull_cmd, delete_echo_cmd, delete_cmd)

    # Setting DOCKER_CONFIG env var is needed if CONFIG_URI is set for custom Docker configuration
    if settings.CONFIG_URI:
        export_echo_cmd = 'echo \'Setting Docker configuration\''
        export_cmd = 'export DOCKER_CONFIG=`pwd`/.docker'
        command = '%s && %s && %s' % (export_echo_cmd, export_cmd, command)

    # If check_exists and the image does not have a "latest" tag, check for image locally before pulling
    if check_exists and not image_name.endswith(':latest'):
        exists_echo_cmd = 'echo \'Checking if image is already pulled...\''
        image_search_cmd = 'docker images --format \'{{.Repository}}:{{.Tag}}\' | grep %s' % image_name
        exists_cmd = '(%s; if [[ $? = 0 ]]; then echo \'Image already pulled\'; exit 0; fi;)' % image_search_cmd
        command = '%s && %s && %s' % (exists_echo_cmd, exists_cmd, command)

    return command


class PullTask(Task):
    """Represents a task that pulls Docker images from the registry. This class is thread-safe.
    """

    def __init__(self, framework_id, agent_id):
        """Constructor

        :param framework_id: The framework ID
        :type framework_id: string
        :param agent_id: The agent ID
        :type agent_id: string
        """

        task_id = '%s_%s_%d' % (PULL_TASK_ID_PREFIX, framework_id, COUNTER.get_next())
        super(PullTask, self).__init__(task_id, 'Scale Docker Pull', agent_id)

        self._uses_docker = False
        self._docker_image = None
        self._docker_params = []
        self._is_docker_privileged = False
        self._running_timeout_threshold = datetime.timedelta(minutes=15)

        self._command = create_pull_command(self._create_scale_image_name(), check_exists=True)

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        return NodeResources([Cpus(0.1), Mem(32.0)])
