"""Defines a command message that purges a source file"""
from __future__ import unicode_literals

import logging

from messaging.messages.message import CommandMessage


logger = logging.getLogger(__name__)


def create_purge_source_file_message(source_file_id, trigger_id):
    """Creates messages to removes a source file form Scale

    :param source_file_id: The source file ID
    :type source_file_id: int
    :param trigger_id: The trigger event ID for the purge operation
    :type trigger_id: int
    :return: The purge source file message
    :rtype: :class:`storage.messages.purge_source_file.PurgeSourceFile`
    """

    message = PurgeSourceFile()
    message.source_file_id = source_file_id
    message.trigger_id = trigger_id

    return message


class PurgeSourceFile(CommandMessage):
    """Command message that removes source file models
    """

    def __init__(self):
        """Constructor
        """

        super(PurgeSourceFile, self).__init__('purge_source_file')

        self.source_file_id = None
        self.trigger_id = None


    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'source_file_id': self.source_file_id, 'trigger_id': self.trigger_id}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = PurgeSourceFile()
        message.source_file_id = json_dict['source_file_id']
        message.trigger_id = json_dict['trigger_id']

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        return True
