"""Defines the factory for creating brokers"""
from __future__ import unicode_literals

import logging

logger = logging.getLogger(__name__)

_BROKERS = {}


def add_broker_type(broker_class):
    """Registers a broker class so it can be used for storage operations.

    :param broker_class: The class definition for a broker.
    :type broker_class: class:`storage.brokers.broker.Broker`
    """

    broker = broker_class()
    if broker.broker_type in _BROKERS:
        logger.warning('Duplicate broker registration: %s', broker.broker_type)
    _BROKERS[broker.broker_type] = broker_class


def get_broker(broker_type):
    """Returns a broker of the given type.

    :param broker_type: The unique identifier of a registered broker.
    :type broker_type: string
    :returns: A broker for storing and retrieving files.
    :rtype: :class:`storage.brokers.broker.Broker`
    """

    if broker_type in _BROKERS:
        return _BROKERS[broker_type]()
    raise KeyError('\'%s\' is an invalid broker type' % broker_type)


def get_broker_types():
    """Returns a list of type identifiers for all registered brokers.

    :returns: A list of broker type identifiers.
    :rtype: [string]
    """

    return _BROKERS.keys()
