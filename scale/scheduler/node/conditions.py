"""Defines the class that holds a node's current conditions"""
from __future__ import unicode_literals

import datetime
import logging
from collections import namedtuple

from django.utils.timezone import now

from job.tasks.health_task import HealthTask
from scheduler.cleanup.node import JOB_EXES_WARNING_THRESHOLD
from util.active_warnings import ActiveError, ActiveWarning
from util.parse import datetime_to_string

CLEANUP_WARN_THRESHOLD = datetime.timedelta(hours=3)


logger = logging.getLogger(__name__)
NodeError = namedtuple('NodeError', ['name', 'title', 'description', 'daemon_bad', 'pull_bad'])
NodeWarning = namedtuple('NodeWarning', ['name', 'title', 'description'])

WARNING_NAME_COUNTER = 1


class NodeConditions(object):
    """This class represents the set of current conditions that apply to a node."""

    # Errors
    BAD_DAEMON_ERR = NodeError(name='BAD_DAEMON', title='Docker Not Responding',
                               description='The Docker daemon on this node is not responding.', daemon_bad=True,
                               pull_bad=True)
    BAD_LOGSTASH_ERR = NodeError(name='BAD_LOGSTASH', title='Fluentd Not Responding',
                                 description='The Scale fluentd is not responding to this node.', daemon_bad=False,
                                 pull_bad=False)
    CLEANUP_ERR = NodeError(name='CLEANUP', title='Cleanup Failure',
                            description='The node failed to clean up some Scale Docker containers and volumes.',
                            daemon_bad=False, pull_bad=False)
    HEALTH_FAIL_ERR = NodeError(name='HEALTH_FAIL', title='Health Check Failure',
                                description='The last node health check failed with an unknown exit code.',
                                daemon_bad=False, pull_bad=False)
    HEALTH_TIMEOUT_ERR = NodeError(name='HEALTH_TIMEOUT', title='Health Check Timeout',
                                   description='The last node health check timed out.', daemon_bad=False,
                                   pull_bad=False)
    IMAGE_PULL_ERR = NodeError(name='IMAGE_PULL', title='Image Pull Failure',
                               description='The node failed to pull the Scale Docker image from the registry.',
                               daemon_bad=False, pull_bad=False)
    LOW_DOCKER_SPACE_ERR = NodeError(name='LOW_DOCKER_SPACE', title='Low Docker Disk Space',
                                     description='The free disk space available to Docker is low.', daemon_bad=False,
                                     pull_bad=True)
    # Errors that can occur due to health checks
    HEALTH_ERRORS = [BAD_DAEMON_ERR, BAD_LOGSTASH_ERR, HEALTH_FAIL_ERR, HEALTH_TIMEOUT_ERR, LOW_DOCKER_SPACE_ERR]

    # Warnings
    SLOW_CLEANUP = NodeWarning(name='SLOW_CLEANUP', title='Slow Cleanup',
                                  description='There are %s job executions waiting to be cleaned up on this node.')
                                  
    CLEANUP_FAILURE = NodeWarning(name='CLEANUP_FAILURE', title='Cleanup Failure',
                                  description='There was a failure cleaning up some of the following jobs: %s')
                                  
    CLEANUP_TIMEOUT = NodeWarning(name='CLEANUP_TIMEOUT', title='Cleanup Timeout',
                                  description='There was a timeout cleaning up some of the following jobs: %s')

    def __init__(self, hostname):
        """Constructor

        :param hostname: The node's hostname
        :type hostname: string
        """

        self._active_errors = {}  # {Error name: ActiveError}
        self._active_warnings = {}  # {Warning name: ActiveWarning}
        self._hostname = hostname

        self.is_daemon_bad = False  # Whether the node's Docker daemon is bad, preventing Docker tasks from running
        self.is_health_check_normal = True  # Whether the last node health check was normal
        self.is_pull_bad = False  # Whether the node should attempt to perform Docker image pulls

    def generate_status_json(self, node_dict):
        """Generates the portion of the status JSON that describes these node conditions

        :param node_dict: The dict for this node within the status JSON
        :type node_dict: dict
        """

        error_list = []
        for active_error in self._active_errors.values():
            error = {'name': active_error.error.name, 'title': active_error.error.title,
                     'description': active_error.error.description, 'started': datetime_to_string(active_error.started),
                     'last_updated': datetime_to_string(active_error.last_updated)}
            error_list.append(error)
        warning_list = []
        for active_warning in self._active_warnings.values():
            warning = {'name': active_warning.warning.name, 'title': active_warning.warning.title,
                       'description': active_warning.description, 'started': datetime_to_string(active_warning.started),
                       'last_updated': datetime_to_string(active_warning.last_updated)}
            warning_list.append(warning)
        node_dict['errors'] = error_list
        node_dict['warnings'] = warning_list

    def handle_cleanup_task_completed(self):
        """Handles the successful completion of a node cleanup task
        """

        self._error_inactive(NodeConditions.CLEANUP_ERR)
        self._warning_inactive_old()
        self._update_state()

    def handle_cleanup_task_failed(self, job_exes):
        """Handles the failure of a node cleanup task
        """

        self._error_active(NodeConditions.CLEANUP_ERR)
        
        if job_exes:
            # add a warning that a cleanup failure has occurred; this will remain after the error has been cleared due with a successful cleanup
            # this will aid in debugging if a node or specific jobs continually have failures cleaning up
            global WARNING_NAME_COUNTER
            ids = [exe.job_id for exe in job_exes]
            name = NodeConditions.CLEANUP_FAILURE.name + ' %d' % WARNING_NAME_COUNTER
            WARNING_NAME_COUNTER += 1
            title = NodeConditions.CLEANUP_FAILURE.title
            description = NodeConditions.CLEANUP_FAILURE.description % ids
            self._warning_active(NodeWarning(name=name, title=title, description=None), description)
        else:
            logger.warning('Cleanup task failed with no job exes')
        
        self._update_state()

    def handle_cleanup_task_timeout(self, job_exes):
        """Indicates that a node cleanup task has timed out
        """

        self._error_active(NodeConditions.CLEANUP_ERR)
        
        if job_exes:
            # add a warning that a timeout has occurred; this will remain after the error has been cleared due with a successful cleanup
            global WARNING_NAME_COUNTER
            ids = [exe.job_id for exe in job_exes]
            name = NodeConditions.CLEANUP_TIMEOUT.name + ' %d' % WARNING_NAME_COUNTER
            WARNING_NAME_COUNTER += 1
            title = NodeConditions.CLEANUP_TIMEOUT.title
            description = NodeConditions.CLEANUP_TIMEOUT.description % ids
            self._warning_active(NodeWarning(name=name, title=title, description=None), description)
        else:
            logger.warning('Cleanup task timed out with no job exes')
        
        self._update_state()

    def handle_health_task_completed(self):
        """Handles the successful completion of a node health check task
        """

        self.is_health_check_normal = True
        self._error_inactive_all_health()
        self._update_state()

    def handle_health_task_failed(self, task_update):
        """Handles the given failed task update for a node health check task

        :param task_update: The health check task update
        :type task_update: :class:`job.tasks.update.TaskStatusUpdate`
        """

        self.is_health_check_normal = False
        self._error_inactive_all_health()
        if task_update.exit_code == HealthTask.BAD_DAEMON_CODE:
            logger.warning('Docker daemon not responding on host %s', self._hostname)
            self._error_active(NodeConditions.BAD_DAEMON_ERR)
        elif task_update.exit_code == HealthTask.LOW_DOCKER_SPACE_CODE:
            logger.warning('Low Docker disk space on host %s', self._hostname)
            self._error_active(NodeConditions.LOW_DOCKER_SPACE_ERR)
        elif task_update.exit_code == HealthTask.BAD_LOGSTASH_CODE:
            logger.warning('Fluentd not responding on host %s', self._hostname)
            self._error_active(NodeConditions.BAD_LOGSTASH_ERR)
        else:
            logger.error('Unknown health check exit code %s on host %s', str(task_update.exit_code), self._hostname)
            self._error_active(NodeConditions.HEALTH_FAIL_ERR)
        self._update_state()

    def handle_health_task_timeout(self):
        """Indicates that a node health check task has timed out
        """

        self.is_health_check_normal = False
        self._error_inactive_all_health()
        self._error_active(NodeConditions.HEALTH_TIMEOUT_ERR)
        self._update_state()

    def handle_pull_task_completed(self):
        """Handles the successful completion of a node image pull task
        """

        self._error_inactive(NodeConditions.IMAGE_PULL_ERR)
        self._update_state()

    def handle_pull_task_failed(self):
        """Handles the failure of a node image pull task
        """

        self._error_active(NodeConditions.IMAGE_PULL_ERR)
        self._update_state()

    def handle_pull_task_timeout(self):
        """Indicates that a node image pull task has timed out
        """

        self._error_active(NodeConditions.IMAGE_PULL_ERR)
        self._update_state()

    def has_active_errors(self):
        """Indicates if any errors are currently active

        :returns: True if at least one error is active, False otherwise
        :rtype: bool
        """

        return len(self._active_errors) > 0

    def last_cleanup_task_error(self):
        """Returns the last time that the cleanup task failed, None if the last cleanup task succeeded

        :returns: The time of the last cleanup task failure, possibly None
        :rtype: :class:`datetime.datetime`
        """

        if NodeConditions.CLEANUP_ERR.name in self._active_errors:
            return self._active_errors[NodeConditions.CLEANUP_ERR.name].last_updated
        return None

    def last_image_pull_task_error(self):
        """Returns the last time that the image pull task failed, None if the last image pull task succeeded

        :returns: The time of the last image pull task failure, possibly None
        :rtype: :class:`datetime.datetime`
        """

        if NodeConditions.IMAGE_PULL_ERR.name in self._active_errors:
            return self._active_errors[NodeConditions.IMAGE_PULL_ERR.name].last_updated
        return None

    def update_cleanup_count(self, num_job_exes):
        """Updates the number of job executions that need to be cleaned up

        :param num_job_exes: The number of job executions that need to be cleaned up
        :type num_job_exes: int`
        """

        if num_job_exes < JOB_EXES_WARNING_THRESHOLD:
            self._warning_inactive(NodeConditions.SLOW_CLEANUP)
        else:
            description = NodeConditions.SLOW_CLEANUP.description % str(num_job_exes)
            self._warning_active(NodeConditions.SLOW_CLEANUP, description)
        self._update_state()

    def _error_active(self, error):
        """Indicates that the given error is now active

        :param error: The node error
        :type error: :class:`scheduler.node.conditions.NodeError`
        """

        when = now()
        if error.name in self._active_errors:
            active_error = self._active_errors[error.name]
        else:
            active_error = ActiveError(error)
            active_error.started = when
            self._active_errors[error.name] = active_error
        active_error.last_updated = when

    def _error_inactive(self, error):
        """Indicates that the given error is now inactive

        :param error: The node error
        :type error: :class:`scheduler.node.conditions.NodeError`
        """

        if error.name in self._active_errors:
            del self._active_errors[error.name]

    def _error_inactive_all_health(self):
        """Inactivates all node errors related to health checks
        """

        for error in NodeConditions.HEALTH_ERRORS:
            self._error_inactive(error)

    def _update_state(self):
        """Updates some internal state
        """

        self.is_daemon_bad = False
        self.is_pull_bad = False
        for active_error in self._active_errors.values():
            self.is_daemon_bad = self.is_daemon_bad or active_error.error.daemon_bad
            self.is_pull_bad = self.is_pull_bad or active_error.error.pull_bad

    def _warning_active(self, warning, description=None):
        """Indicates that the given warning is now active

        :param warning: The node warning
        :type warning: :class:`scheduler.node.conditions.NodeWarning`
        :param description: An optional specific description for the warning
        :type description: string
        """

        when = now()
        if warning.name in self._active_warnings:
            active_warning = self._active_warnings[warning.name]
        else:
            active_warning = ActiveWarning(warning, description)
            active_warning.started = when
            self._active_warnings[warning.name] = active_warning
        active_warning.description = description
        active_warning.last_updated = when

    def _warning_inactive(self, warning):
        """Indicates that the given warning is now inactive

        :param warning: The node warning
        :type warning: :class:`scheduler.node.conditions.NodeWarning`
        """

        if warning.name in self._active_warnings:
            del self._active_warnings[warning.name]
            
    def _warning_inactive_old(self):
        """Inactivates all old warnings
        """

        warnings_to_delete = []
        for name in self._active_warnings:
            if now() - self._active_warnings[name].last_updated >= CLEANUP_WARN_THRESHOLD:
                warnings_to_delete.append(name)
        for name in warnings_to_delete:
            del self._active_warnings[name]
