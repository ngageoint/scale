'''Defines utility methods for testing nodes'''
from node.models import Node

HOSTNAME_COUNTER = 1
SLAVEID_COUNTER = 1


def create_node(hostname=None, port=5051, slave_id=None):
    '''Creates a node model for unit testing

    :returns: The node model
    :rtype: :class:`node.models.Node`
    '''

    if not hostname:
        global HOSTNAME_COUNTER
        hostname = u'host%i.com' % HOSTNAME_COUNTER
        HOSTNAME_COUNTER = HOSTNAME_COUNTER + 1

    if not slave_id:
        global SLAVEID_COUNTER
        slave_id = u'123-456-789-%i' % SLAVEID_COUNTER
        SLAVEID_COUNTER = SLAVEID_COUNTER + 1

    return Node.objects.register_node(hostname, port, slave_id)
