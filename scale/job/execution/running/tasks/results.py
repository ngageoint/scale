"""Defines the class representing the results of a task"""


class TaskResults(object):
    """Represents the results of a job execution task
    """

    def __init__(self, task_id):
        """Constructor

        :param task_id: The unique ID of the task
        :type task_id: str
        """

        self._task_id = task_id
        self._exit_code = None
        self._when = None
        self._stdout = None
        self._stderr = None

    @property
    def exit_code(self):
        """Returns the task's exit code, possibly None

        :returns: The task's exit code
        :rtype: int
        """

        return self._exit_code

    @exit_code.setter
    def exit_code(self, value):
        """Sets the task's exit code

        :param value: The task's exit code
        :type value: int
        """

        self._exit_code = value

    @property
    def task_id(self):
        """Returns the task's ID

        :returns: The task's ID
        :rtype: str
        """

        return self._task_id

    @property
    def stderr(self):
        """Returns the task's stderr log contents, possibly None

        :returns: The task's stderr log contents
        :rtype: str
        """

        return self._stderr

    @stderr.setter
    def stderr(self, value):
        """Sets the task's stderr log contents

        :param value: The task's stderr log contents
        :type value: str
        """

        self._stderr = value

    @property
    def stdout(self):
        """Returns the task's stdout log contents, possibly None

        :returns: The task's stdout log contents
        :rtype: str
        """

        return self._stdout

    @stdout.setter
    def stdout(self, value):
        """Sets the task's stdout log contents

        :param value: The task's stdout log contents
        :type value: str
        """

        self._stdout = value

    @property
    def when(self):
        """Returns the timestamp when the task reached its final state, possibly None

        :returns: The timestamp of the task's final state
        :rtype: :class:`datetime.datetime`
        """

        return self._when

    @when.setter
    def when(self, value):
        """Sets the timestamp of the task's final state

        :param value: The timestamp of the task's final state
        :type value: :class:`datetime.datetime`
        """

        self._when = value
