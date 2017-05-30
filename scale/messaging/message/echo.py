from . import CommandMessage


class EchoCommandMessage(CommandMessage):
    def to_json(self):
        return self._payload

    def execute(self):
        print(self._payload.__dict__)

    def __init__(self):
        super(EchoCommandMessage, self).__init__('echo')

    def _set_payload(self, payload):
        self._payload = payload

    @staticmethod
    def from_json(json_dict):
        this = EchoCommandMessage()
        this._set_payload(json_dict)
        return this