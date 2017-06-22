from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from messaging.messages.message import CommandMessage

logger = logging.getLogger(__name__)


class FailCommandMessage(CommandMessage):
    def __init__(self):
        super(FailCommandMessage, self).__init__('failing')

        self._payload = None

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`"""
        logger.info("I'm going to fail now...")
        return False

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`"""
        this = FailCommandMessage()
        this._payload = json_dict
        return this

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`"""
        return self._payload
