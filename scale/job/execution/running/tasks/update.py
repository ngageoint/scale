"""Defines the class that represents a task status update"""
from __future__ import unicode_literals

import logging
import re


logger = logging.getLogger(__name__)


class TaskStatusUpdate(object):
    """This class represents a task status update. This class is thread-safe."""

    # Task statuses
    STAGING = 'STAGING'
    RUNNING = 'RUNNING'
    FINISHED = 'FINISHED'
    LOST = 'LOST'
    FAILED = 'FAILED'
    KILLED = 'KILLED'
    UNKNOWN = 'UNKNOWN'
    TERMINAL_STATUSES = [FINISHED, FAILED, KILLED]

    # Regex for parsing exit code
    EXIT_CODE_PATTERN = re.compile(r'exited with status ([\-0-9]+)')

    # This dict is used to convert the model status (from Mesos) to the set of statuses we use
    TASK_STATUS_CONVERSION = {'TASK_STAGING': STAGING, 'TASK_STARTING': STAGING, 'TASK_RUNNING': RUNNING,
                              'TASK_FINISHED': FINISHED, 'TASK_FAILED': FAILED, 'TASK_KILLED': KILLED,
                              'TASK_LOST': LOST, 'TASK_ERROR': FAILED}

    def __init__(self, task_update_model, agent_id, data):
        """Constructor

        :param task_update_model: The task update model
        :type task_update_model: :class:`job.models.TaskUpdate`
        :param agent_id: The agent ID for the task
        :type agent_id: string
        :param data: The data dict in the task update
        :type data: dict
        """

        self.task_id = task_update_model.task_id
        self.agent_id = agent_id
        self.timestamp = task_update_model.timestamp

        if task_update_model.status in self.TASK_STATUS_CONVERSION:
            self.status = self.TASK_STATUS_CONVERSION[task_update_model.status]
        else:
            logger.error('Unknown task status: %s', task_update_model.status)
            self.status = self.UNKNOWN

        self.message = task_update_model.message
        self.source = task_update_model.source
        self.reason = task_update_model.reason
        self.exit_code = None

        self._parse_exit_code()

    def _parse_exit_code(self):
        """Parses the exit code
        """

        if self.message:
            match = self.EXIT_CODE_PATTERN.search(self.message)
            if match:
                self.exit_code = int(match.group(1))

        # If we don't receive an exit code for a finished task, we assume exit code 0
        if self.exit_code is None and self.status == TaskStatusUpdate.FINISHED:
            self.exit_code = 0
