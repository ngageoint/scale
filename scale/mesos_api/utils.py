"""Provides utility functions for handling Mesos"""
import logging
from datetime import datetime, timedelta

from django.utils.timezone import utc
from google.protobuf.internal import enum_type_wrapper
from mesos.interface import mesos_pb2

from job.execution.running.tasks.exe_task import JOB_TASK_ID_PREFIX
from job.models import JobExecution, TaskUpdate


EPOCH = datetime.utcfromtimestamp(0).replace(tzinfo=utc)
REASON_ENUM_WRAPPER = enum_type_wrapper.EnumTypeWrapper(mesos_pb2._TASKSTATUS_REASON)
SOURCE_ENUM_WRAPPER = enum_type_wrapper.EnumTypeWrapper(mesos_pb2._TASKSTATUS_SOURCE)


logger = logging.getLogger(__name__)


def create_task_update_model(status):
    """Creates and returns a task update model for the given Mesos task status

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task update model
    :rtype: :class:`job.models.TaskUpdate`
    """

    task_update = TaskUpdate()
    task_update.task_id = get_status_task_id(status)
    if task_update.task_id.startswith(JOB_TASK_ID_PREFIX):
        task_update.job_exe_id = JobExecution.get_job_exe_id(task_update.task_id)
    task_update.status = get_status_state(status)
    task_update.timestamp = get_status_timestamp(status)
    task_update.source = get_status_source(status)
    task_update.reason = get_status_reason(status)
    task_update.message = get_status_message(status)

    return task_update


def get_status_agent_id(status):
    """Returns the agent ID of the given Mesos task status

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The agent ID
    :rtype: string
    """

    return status.slave_id.value


def get_status_data(status):
    """Returns the data dict in the given Mesos task status, possibly None

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task status data dict
    :rtype: dict
    """

    if hasattr(status, 'data') and status.data:
        logger.info('data field has type %s', type(status.data))
        return status.data

    return None


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

    # A reason of 0 is invalid (dummy default value according to Mesos code comment) and should be ignored (return None)
    if hasattr(status, 'reason') and status.reason:
        try:
            return REASON_ENUM_WRAPPER.Name(status.reason)
        except ValueError:
            logger.error('Unknown reason value: %d', status.reason)

    return None


def get_status_source(status):
    """Returns the source of the given Mesos task status, possibly None

    :param status: The task status
    :type status: :class:`mesos_pb2.TaskStatus`
    :returns: The task status source
    :rtype: string
    """

    if hasattr(status, 'source') and status.source is not None:
        try:
            return SOURCE_ENUM_WRAPPER.Name(status.source)
        except ValueError:
            logger.error('Unknown source value: %d', status.source)

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


def string_to_TaskStatusCode(status):
    """Converts the given Mesos status string to an integer

    :param status: The status as a string
    :type status: string
    :returns: The status as an integer
    :rtype: int
    """

    return mesos_pb2.TaskState.Value(status)
