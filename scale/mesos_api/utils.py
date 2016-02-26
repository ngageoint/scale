"""Provides utility functions for handling Mesos"""
import re
from datetime import datetime, timedelta

from django.utils.timezone import utc


try:
    from mesos.interface import mesos_pb2
except ImportError:
    import mesos_api.mesos_pb2 as mesos_pb2


EPOCH = datetime.utcfromtimestamp(0).replace(tzinfo=utc)
EXIT_CODE_PATTERN = re.compile(r'Command exited with status ([\-0-9]+)')


def get_status_timestamp(status):
    """Returns the timestamp of the given Mesos task status, possibly None

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task status timestamp
    :rtype: :class:`datetime.datetime`
    """

    if not status.timestamp:
        return None

    return EPOCH + timedelta(seconds=status.timestamp)


def parse_exit_code(status):
    """Parses and returns an exit code from the task status, returns None if no exit code can be parsed

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The exit code, possibly None
    :rtype: int
    """

    exit_code = None

    match = EXIT_CODE_PATTERN.search(status.message)
    if match:
        exit_code = int(match.group(1))

    return exit_code


def status_to_string(status):
    """Converts the given Mesos status to a string

    :param status: The status
    :type status: int
    :returns: The status as a string
    :rtype: str
    """

    return mesos_pb2.TaskState.Name(status)


def string_to_TaskStatusCode(status):
    """Converts the given Mesos status string to an integer

    :param status: The status as a string
    :type status: str
    :returns: The status as an integer
    :rtype: int
    """

    return mesos_pb2.TaskState.Value(status)
