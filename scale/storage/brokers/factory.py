'''Defines the factory for creating brokers'''
from storage.brokers.nfs_broker import NfsBroker


BROKERS = {NfsBroker.broker_type: NfsBroker}


def get_broker(broker_type):
    '''Returns a broker of the given type

    :param broker_type: The broker type
    :type broker_type: str
    :returns: a broker for storing and retrieving files
    :rtype: :class:`storage.brokers.broker.Broker`
    '''
    if broker_type in BROKERS:
        return BROKERS[broker_type]()
    error_msg = u'\'{0}\' is an invalid broker type'.format(broker_type)
    raise KeyError(error_msg)
