"""Defines the named tuple for host locations"""
from __future__ import unicode_literals

from collections import namedtuple


# Named tuple represents a host location
HostAddress = namedtuple('HostAddress', ['hostname', 'port'])
