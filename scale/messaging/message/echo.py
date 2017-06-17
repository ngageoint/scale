from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import random

from . import CommandMessage

logger = logging.getLogger(__name__)


class EchoCommandMessage(CommandMessage):
    def __init__(self):
        super(EchoCommandMessage, self).__init__('echo')
        

    def _set_payload(self, payload):
        self._payload = payload

    def execute(self):
        logger.info(self._payload)
        random.seed()
        if random.choice([True, False]):
            self.new_messages = [EchoCommandMessage.from_json({'message':"This is a chained EchoCommandMessage via new_messages."})]
        return True
        
    @staticmethod
    def from_json(json_dict):
        this = EchoCommandMessage()
        this._set_payload(json_dict)
        return this
        
    def to_json(self):
        return self._payload
