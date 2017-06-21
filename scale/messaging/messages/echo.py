from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import random

from messaging.messages.message import CommandMessage

logger = logging.getLogger(__name__)


class EchoCommandMessage(CommandMessage):
    def __init__(self):
        super(EchoCommandMessage, self).__init__('echo')
        
        self._payload = None

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`"""
        logger.info(self._payload)
        random.seed()
        if random.choice([True, False]):
            self.new_messages = [
                EchoCommandMessage.from_json({'message': "This is a chained EchoCommandMessage via new_messages."})]
        return True

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`"""
        this = EchoCommandMessage()
        this._payload = json_dict
        return this

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`"""
        return self._payload
