"""Defines the class for a node health check task"""
from __future__ import unicode_literals

import datetime

from django.conf import settings

from job.tasks.base_task import AtomicCounter
from job.tasks.node_task import NodeTask
from node.resources.node_resources import NodeResources
from node.resources.resource import Cpus, Mem


HEALTH_TASK_ID_PREFIX = 'scale_health'
COUNTER = AtomicCounter()


class HealthTask(NodeTask):
    """Represents a task that performs a health check on a node. This class is thread-safe.
    """

    BAD_DAEMON_CODE = 2
    LOW_DOCKER_SPACE_CODE = 3
    BAD_LOGSTASH_CODE = 4

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
        self._docker_params = []
        self._is_docker_privileged = False
        self._running_timeout_threshold = datetime.timedelta(minutes=15)

        health_check_commands = []

        # Check if docker version works (indicates if daemon is working)
        bad_daemon_check = 'docker version'
        bad_daemon_check = 'timeout -s SIGKILL 10s %s' % bad_daemon_check  # docker version has 10 seconds to succeed
        bad_daemon_check = '%s; if [[ $? != 0 ]]; then exit %d; fi' % (bad_daemon_check, HealthTask.BAD_DAEMON_CODE)
        health_check_commands.append(bad_daemon_check)

        # Check if docker ps works (also indicates if daemon is working)
        docker_ps_check = 'docker ps'
        docker_ps_check = 'timeout -s SIGKILL 10s %s' % docker_ps_check  # docker ps has 10 seconds to succeed
        docker_ps_check = '%s; if [[ $? != 0 ]]; then exit %d; fi' % (docker_ps_check, HealthTask.BAD_DAEMON_CODE)
        health_check_commands.append(docker_ps_check)

        # Check if Docker disk space is below 1 GiB (assumes /var/lib/docker, ignores check otherwise)
        get_disk_space = 'df --output=avail /var/lib/docker | tail -1'
        test_disk_space = 'test `%s` -lt 1048576; if [[ $? == 0 ]]; then exit %d; fi'
        test_disk_space = test_disk_space % (get_disk_space, HealthTask.LOW_DOCKER_SPACE_CODE)
        low_docker_space_check = 'if [[ -d /var/lib/docker ]]; then %s; fi' % test_disk_space
        health_check_commands.append(low_docker_space_check)

        # Check to ensure that logstash is reachable
        if settings.LOGGING_HEALTH_ADDRESS:
            logstash_check = 'timeout -s SIGKILL 5s curl %s; if [[ $? != 0 ]]; then exit %d; fi'
            logstash_check = logstash_check % (settings.LOGGING_HEALTH_ADDRESS, HealthTask.BAD_LOGSTASH_CODE)
            health_check_commands.append(logstash_check)

        self._command = ' && '.join(health_check_commands)

        # Node task properties
        self.task_type = 'health-check'
        self.title = 'Node Health Check'
        self.description = 'Checks the health status of the node'

    def get_resources(self):
        """See :meth:`job.tasks.base_task.Task.get_resources`
        """

        return NodeResources([Cpus(0.1), Mem(32.0)])
