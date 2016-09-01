"""Provides utility functions for handling Mesos"""
import re
from datetime import datetime, timedelta

from django.utils.timezone import utc
from google.protobuf.internal import enum_type_wrapper
from mesos.interface import mesos_pb2

from job.execution.running.job_exe import RunningJobExecution
from job.models import TaskUpdate


EPOCH = datetime.utcfromtimestamp(0).replace(tzinfo=utc)
EXIT_CODE_PATTERN = re.compile(r'exited with status ([\-0-9]+)')
REASON_ENUM_WRAPPER = enum_type_wrapper.EnumTypeWrapper(mesos_pb2._TASKSTATUS_REASON)
SOURCE_ENUM_WRAPPER = enum_type_wrapper.EnumTypeWrapper(mesos_pb2._TASKSTATUS_SOURCE)


def create_task_update_model(status):
    """Creates and returns a task update model for the given Mesos task status

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task update model
    :rtype: :class:`job.models.TaskUpdate`
    """

    task_update = TaskUpdate()
    task_update.task_id = get_status_task_id(status)
    task_update.job_exe_id = RunningJobExecution.get_job_exe_id(task_update.task_id)
    task_update.status = get_status_state(status)
    task_update.timestamp = get_status_timestamp(status)
    task_update.source = get_status_source(status)
    task_update.reason = get_status_reason(status)
    task_update.message = get_status_message(status)

    return task_update


def get_status_message(status):
    """Returns the message of the given Mesos task status, possibly None

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task status message
    :rtype: string
    """

    if hasattr(status, 'message'):
        return status.message

    return None


def get_status_reason(status):
    """Returns the reason of the given Mesos task status, possibly None

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task status reason
    :rtype: string
    """

    if hasattr(status, 'reason') and status.reason is not None:
        return REASON_ENUM_WRAPPER.Name(status.reason)

    return None


def get_status_source(status):
    """Returns the source of the given Mesos task status, possibly None

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task status source
    :rtype: string
    """

    if hasattr(status, 'source') and status.source is not None:
        return SOURCE_ENUM_WRAPPER.Name(status.source)

    return None


def get_status_state(status):
    """Returns the state of the given Mesos task status, possibly None

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task status state
    :rtype: string
    """

    return mesos_pb2.TaskState.Name(status.state)


def get_status_task_id(status):
    """Returns the task ID of the given Mesos task status

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task ID
    :rtype: string
    """

    return status.task_id.value


def get_status_timestamp(status):
    """Returns the timestamp of the given Mesos task status, possibly None

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task status timestamp
    :rtype: :class:`datetime.datetime`
    """

    if hasattr(status, 'timestamp') and status.timestamp:
        return EPOCH + timedelta(seconds=status.timestamp)

    return None


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


def string_to_TaskStatusCode(status):
    """Converts the given Mesos status string to an integer

    :param status: The status as a string
    :type status: string
    :returns: The status as an integer
    :rtype: int
    """

    return mesos_pb2.TaskState.Value(status)
