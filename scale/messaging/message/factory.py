"""Defines the factory for creating messages"""
from __future__ import unicode_literals

import json
import logging

logger = logging.getLogger(__name__)

_MESSAGE_TYPES = {}


def add_message_type(message_class):
    """Registers a message class so it can be used for Scale messaging

    :param message_class: The class definition for a message
    :type message_class: class:`messaging.messages.CommandMessage`
    """

    message_clazz = message_class()
    if message_clazz.type in _MESSAGE_TYPES:
        logger.warning('Duplicate message type registration: %s', message_clazz.type)
    _MESSAGE_TYPES[message_clazz.scanner_type] = message_clazz


def get_message_type(message_type):
    """Returns a message class of the given type

    :param message_type: The unique identifier of a registered scanner
    :type message_type: string
    :param message_class: The class definition for a message
    :type message_class: class:`messaging.messages.CommandMessage`
    """

    if message_type in _MESSAGE_TYPES:
        return _MESSAGE_TYPES[message_type]()
    raise KeyError("'{}' is an invalid message type".format(message_type))

def process_message(message):
    """Inspects message for type and then attempts to launch execution

    :param message: raw message payload (expects stringified JSON)
    :type message:string
    :return: success or failure of message process
    """

    message_dict = json.loads(message)

    if 'type' in message_dict:
        if 'body' in message_dict:
            try:
                message_class= get_message_type(message_dict['type'])
                message_body = message_dict['body']

                processor = message_class.from_json(message_body)
                return processor.execute(message_body)
            except KeyError as ex:
                logger.exception('No message type handler available.')
        else:
            logger.error('Missing body in message.')
    else:
        logger.error('Invalid message missing type: %s', message)

    return False

def get_message_types():
    """Returns a list of type identifiers for all registered message types

    :returns: A list of messages types
    :rtype: [string]
    """

    return _MESSAGE_TYPES.keys()