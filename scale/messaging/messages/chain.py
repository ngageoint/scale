from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from messaging.messages.message import CommandMessage
from messaging.messages.echo import EchoCommandMessage

logger = logging.getLogger(__name__)


class ChainCommandMessage(CommandMessage):
    def __init__(self):
        super(ChainCommandMessage, self).__init__('chain')

        self._payload = None

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`"""
        logger.info(self._payload)
        self.new_messages = [
            EchoCommandMessage.from_json({'message': "This is a chained EchoCommandMessage via new_messages."})]
        return True

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`"""
        this = ChainCommandMessage()
        this._payload = json_dict
        return this

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`"""
        return self._payload
