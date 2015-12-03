'''Defines errors relevant to the scheduler'''
from error.models import Error

ERROR_MESOS_LOST = None
ERROR_NODE_LOST = None
ERROR_SCHEDULER_LOST = None
ERROR_TIMEOUT = None


def get_timeout_error():
    '''Returns the error for a job timeout

    :returns: The timeout error
    :rtype: :class:`error.models.Error`
    '''

    global ERROR_TIMEOUT
    if not ERROR_TIMEOUT:
        ERROR_TIMEOUT = Error.objects.get(name=u'timeout')
    return ERROR_TIMEOUT


def get_mesos_error():
    '''Returns the error for Mesos losing the job

    :returns: The Mesos error
    :rtype: :class:`error.models.Error`
    '''

    global ERROR_MESOS_LOST
    if not ERROR_MESOS_LOST:
        ERROR_MESOS_LOST = Error.objects.get(name=u'mesos-lost')
    return ERROR_MESOS_LOST


def get_node_lost_error():
    '''Returns the error for a lost node

    :returns: The node lost error
    :rtype: :class:`error.models.Error`
    '''

    global ERROR_NODE_LOST
    if not ERROR_NODE_LOST:
        ERROR_NODE_LOST = Error.objects.get(name=u'node-lost')
    return ERROR_NODE_LOST


def get_scheduler_error():
    '''Returns the error for the scheduler losing the job

    :returns: The scheduler error
    :rtype: :class:`error.models.Error`
    '''

    global ERROR_SCHEDULER_LOST
    if not ERROR_SCHEDULER_LOST:
        ERROR_SCHEDULER_LOST = Error.objects.get(name=u'scheduler-lost')
    return ERROR_SCHEDULER_LOST
