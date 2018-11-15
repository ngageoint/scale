"""Defines the named tuple for host locations"""
from __future__ import unicode_literals

from collections import namedtuple

# Named tuple represents a host location
HostAddress = namedtuple('HostAddress', ['hostname', 'port', 'protocol'])


def host_address_from_mesos_url(url):
    """Extract URL components from a Mesos Master URL

    Must include the protocol prefix. Ports may be omitted.

    :param url: The URL to parse
    :type url: basestring
    :return: Parsed URL components
    :rtype: :class:`util.host.HostAddress`
    """

    from urlparse import urlparse
    elements = urlparse(url)

    # infer port from scheme if not set:
    port = elements.port
    if not port:
        if elements.scheme == 'https':
            port = 443
        elif elements.scheme == 'http':
            port = 80

    return HostAddress(elements.hostname, port, elements.scheme)

