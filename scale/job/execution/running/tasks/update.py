"""Defines the class that represents a task status update"""
from __future__ import unicode_literals


class TaskStatusUpdate(object):
    """This class represents a task status update. This class is thread-safe."""

    STAGING = 'STAGING'
    RUNNING = 'RUNNING'
    FINISHED = 'FINISHED'
    LOST = 'LOST'
    FAILED = 'FAILED'
    KILLED = 'KILLED'
    VALID_STATUSES = [STAGING, RUNNING, FINISHED, LOST, FAILED, KILLED]
    TERMINAL_STATUSES = [FINISHED, FAILED, KILLED]

    def __init__(self, task_id, agent_id, status, when, exit_code=None):
        """Constructor

        :param task_id: The unique ID of the task
        :type task_id: string
        :param agent_id: The agent ID for the task
        :type agent_id: string
        :param status: The status of the task
        :type status: string
        :param when: The timestamp of the update
        :type when: :class:`datetime.datetime`
        :param exit_code: The task's exit code
        :type exit_code: int
        """

        if not task_id:
            raise Exception('task_id must be provided')
        if not agent_id:
            raise Exception('agent_id must be provided')
        if status not in self.VALID_STATUSES:
            raise Exception('invalid status')
        if not when:
            raise Exception('when must be provided')

        self._task_id = task_id
        self._agent_id = agent_id
        self._status = status
        self._when = when
        self._exit_code = exit_code

    @property
    def agent_id(self):
        """Returns the agent ID for the task

        :returns: The agent ID
        :rtype: string
        """

        return self._agent_id

    @property
    def exit_code(self):
        """Returns the task's exit code, possibly None

        :returns: The task's exit code
        :rtype: int
        """

        return self._exit_code

    @property
    def status(self):
        """Returns the task's status

        :returns: The task's status
        :rtype: string
        """

        return self._status

    @property
    def task_id(self):
        """Returns the task's ID

        :returns: The task's ID
        :rtype: string
        """

        return self._task_id

    @property
    def when(self):
        """Returns the timestamp of the update

        :returns: The timestamp of the update
        :rtype: :class:`datetime.datetime`
        """

        return self._when
