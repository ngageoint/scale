"""Defines the factory for creating monitors"""
from __future__ import unicode_literals

import logging

logger = logging.getLogger(__name__)

_MONITORS = {}


def add_monitor_type(monitor_class):
    """Registers a monitor class so it can be used for Strike

    :param monitor_class: The class definition for a monitor
    :type monitor_class: class:`ingest.strike.monitors.monitor.Monitor`
    """

    monitor = monitor_class()
    if monitor.monitor_type in _MONITORS:
        logger.warning('Duplicate monitor registration: %s', monitor.monitor_type)
    _MONITORS[monitor.monitor_type] = monitor_class


def get_monitor(monitor_type):
    """Returns a monitor of the given type that is set to monitor the given workspace

    :param monitor_type: The unique identifier of a registered monitor
    :type monitor_type: string
    :returns: A monitor for storing and retrieving files.
    :rtype: :class:`ingest.strike.monitors.monitor.Monitor`
    """

    if monitor_type in _MONITORS:
        return _MONITORS[monitor_type]()
    raise KeyError('\'%s\' is an invalid monitor type' % monitor_type)


def get_monitor_types():
    """Returns a list of type identifiers for all registered monitors

    :returns: A list of monitor types
    :rtype: [string]
    """

    return _MONITORS.keys()
