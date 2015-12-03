'''Provides utility functions for handling Mesos'''


try:
    from mesos.interface import mesos_pb2
except ImportError:
    import mesos_api.mesos_pb2 as mesos_pb2


def status_to_string(status):
    '''Converts the given Mesos status to a string

    :param status: The status
    :type status: int
    :returns: The status as a string
    :rtype: str
    '''

    return mesos_pb2.TaskState.Name(status)


def string_to_TaskStatusCode(status):
    '''Converts the given Mesos status string to an integer

    :param status: The status as a string
    :type status: str
    :returns: The status as an integer
    :rtype: int
    '''

    return mesos_pb2.TaskState.Value(status)
