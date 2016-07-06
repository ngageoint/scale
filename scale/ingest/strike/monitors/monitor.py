"""Defines the base monitor class"""
from abc import ABCMeta


class Monitor(object):
    """Abstract class for a monitor that processes incoming files to ingest
    """

    __metaclass__ = ABCMeta

    def __init__(self, monitor_type, workspace):
        """Constructor

        :param monitor_type: The type of this monitor
        :type monitor_type: string
        :param workspace: The workspace that is being monitored
        :type workspace: :class:`storage.models.Workspace`
        """

        self._monitor_type = monitor_type
        self._workspace = workspace

    @property
    def monitor_type(self):
        """The type of this monitor

        :returns: The monitor type
        :rtype: string
        """

        return self._monitor_type
