import logging

from . import CommandMessage

logger = logging.getLogger(__name__)


class EchoCommandMessage(CommandMessage):
    def __init__(self):
        super(EchoCommandMessage, self).__init__('echo')

    def _set_payload(self, payload):
        self._payload = payload

    def execute(self):
        logger.info(self._payload)
        
    @staticmethod
    def from_json(json_dict):
        this = EchoCommandMessage()
        this._set_payload(json_dict)
        return this
        
    def to_json(self):
        return self._payload
