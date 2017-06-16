"""Defines the factory for creating messaging backends"""
from __future__ import unicode_literals

import json
import logging

logger = logging.getLogger(__name__)

_MESSAGE_BACKENDS = {}


def add_message_backend(backend_class):
    """Registers a backend so it can be used for Scale messaging

    :param backend_class: The class definition for a backend
    :type backend_class: class:`messaging.backends.Backend`
    """

    backend_clazz = backend_class()
    if backend_clazz.type in _MESSAGE_BACKENDS:
        logger.warning('Duplicate message type registration: %s', backend_clazz.type)
    _MESSAGE_BACKENDS[backend_clazz.type] = backend_clazz


def get_message_backend(backend_type):
    """Returns a backend class of the given type

    :param backend_type: The unique identifier of a registered message backend
    :type backend_type: string
    """

    if backend_type in _MESSAGE_BACKENDS:
        return _MESSAGE_BACKENDS[backend_type]
    raise KeyError("'{}' is an invalid backend type".format(backend_type))
    

def get_message_backed():
    """Returns a list of type identifiers for all registered message backends

    :returns: A list of messages backends
    :rtype: [string]
    """

    return _MESSAGE_BACKENDS.keys()