"""Provides utility functions for handling Mesos"""
from __future__ import unicode_literals

import json
import logging
from base64 import b64decode
from datetime import datetime, timedelta

from django.utils.timezone import utc

from job.models import TaskUpdate

try:
    from types import SimpleNamespace as Namespace
except ImportError:
    # Python 2.x fallback
    from argparse import Namespace

EPOCH = datetime.utcfromtimestamp(0).replace(tzinfo=utc)


logger = logging.getLogger(__name__)

sample = {u'type': u'UPDATE', u'update': {u'status':
                                              {u'task_id': {
                                                  u'value': u'scale_health_73e84cd0-c07b-44bc-a76b-475f608aa132-0005_10'},
                                               u'timestamp': 1541085060.901,
                                               u'state': u'TASK_LOST',
                                               u'source': u'SOURCE_MASTER',
                                               u'reason': u'REASON_RECONCILIATION',
                                               u'agent_id': {u'value': u'ef554235-4600-4202-aac9-53d79dc8e923-S3'},
                                               u'message': u'Reconciliation: Task is unknown to the agent'}
                                          }}

sample2 = {u'status': {u'task_id': {u'value': u'scale_cleanup_73e84cd0-c07b-44bc-a76b-475f608aa132-0007_7'}}}


def obj_from_json(input_json):
    """Converts an JSON dict into a dot accessible object

    :param input_json: The task status in TaskStatus JSON format
    :type input_json: dict
    :returns: The Task Status in dot accessible form
    :rtype: :class:`Namespace`
    """
    return json.loads(json.dumps(input_json), object_hook=lambda d: Namespace(**d))


def create_task_update_model(status):
    """Creates and returns a task update model for the given Mesos task status

    :param status: The task status in TaskStatus JSON format
    :type status: dict
    :returns: The task update model
    :rtype: :class:`job.models.TaskUpdate`
    """

    task_update = TaskUpdate()
    task_update.task_id = get_status_task_id(status)
    task_update.status = get_status_state(status)
    task_update.timestamp = get_status_timestamp(status)
    task_update.source = get_status_source(status)
    task_update.reason = get_status_reason(status)
    task_update.message = get_status_message(status)

    return task_update


def get_status_agent_id(status):
    """Returns the agent ID of the given Mesos task status

    :param status: The task status in TaskStatus JSON format
    :type status: dict
    :returns: The agent ID
    :rtype: string
    """

    return obj_from_json(status).status.agent_id.value


def get_status_data(status):
    """Returns the data dict in the given Mesos task status. If there is no data dict or it is invalid, an empty dict
    will be returned.

    :param status: The task status in TaskStatus JSON format
    :type status: dict
    :returns: The task status data dict
    :rtype: dict
    """

    data = {}

    try:
        data = b64decode(obj_from_json(status).status.data)
    except AttributeError:
        pass
    except:
        logger.exception('Invalid data dict')

    return data


def get_status_message(status):
    """Returns the message of the given Mesos task status, possibly None

    :param status: The task status in TaskStatus JSON format
    :type status: dict
    :returns: The task status message
    :rtype: string
    """

    message = None
    try:
        message = obj_from_json(status).status.message
    except AttributeError:
        pass

    return message


def get_status_reason(status):
    """Returns the reason of the given Mesos task status, possibly None

    :param status: The task status in TaskInfo JSON format
    :type status: dict
    :returns: The task status reason
    :rtype: string
    """

    reason = None
    try:
        reason = obj_from_json(status).status.reason
    except AttributeError:
        pass

    return reason


def get_status_source(status):
    """Returns the source of the given Mesos task status, possibly None

    :param status: The task status in TaskStatus JSON format
    :type status: dict
    :returns: The task status source
    :rtype: string
    """

    return obj_from_json(status).status.source


def get_status_state(status):
    """Returns the state of the given Mesos task status, possibly None

    :param status: The task status in TaskStatus JSON format
    :type status: dict
    :returns: The task status state
    :rtype: string
    """

    return obj_from_json(status).status.state


def get_status_task_id(status):
    """Returns the task ID of the given Mesos task status

    :param status: The task status in TaskStatus JSON format
    :type status: dict
    :returns: The task ID
    :rtype: string
    """

    return obj_from_json(status).status.task_id.value


def get_status_timestamp(status):
    """Returns the timestamp of the given Mesos task status, possibly None

    :param status: The task status in TaskStatus JSON format
    :type status: dict
    :returns: The task status timestamp
    :rtype: :class:`datetime.datetime`
    """

    timestamp = obj_from_json(status).status.timestamp
    if timestamp:
        return EPOCH + timedelta(seconds=timestamp)

    return None
