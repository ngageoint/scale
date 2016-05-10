"""Defines the factory for creating brokers"""
from storage.brokers.host_broker import HostBroker


BROKERS = {HostBroker().broker_type: HostBroker}


def get_broker(broker_type):
    """Returns a broker of the given type

    :param broker_type: The broker type
    :type broker_type: string
    :returns: a broker for storing and retrieving files
    :rtype: :class:`storage.brokers.broker.Broker`
    """

    if broker_type in BROKERS:
        return BROKERS[broker_type]()
    raise KeyError('\'%s\' is an invalid broker type' % broker_type)
