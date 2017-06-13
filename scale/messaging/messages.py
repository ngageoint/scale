from .backends.amqp import AMQPMessagingBackend
from .backends.sqs import SQSMessagingBackend
from .message.factory import process_message


class CommandMessageManager(object):
    def __new__(cls):
        """Singleton support for manager"""
        if not hasattr(cls, 'instance'):
            cls.instance = super(CommandMessageManager, cls).__new__(cls)

        return cls.instance

    def __init__(self):
        """Instantiate CommandMessageManager based on setting values

        :return:
        """

        # Retrieve the broker URL for message passing... right now its just RabbitMQ or SQS
        # TODO: make this discover the backend 
        #self._backend = AMQPMessagingBackend()
        self._backend = SQSMessagingBackend()

    def send_message(self, command):
        """Use command.to_json() to generate payload and then publish

        :param command:
        :return:
        """

        self._backend.send_message({"type":command.message_type, "body":command.to_json()})

    def process_messages(self):
        """Main entry point to message processing.
        
        This will process up to a batch of 10 messages at a time. Behavior may
        differ slightly based on message backend. RabbitMQ will immediately
        iterate over up to 10 messages, process and return. SQS will long-poll
        up to 20 seconds or until 10 messages have been processed, process and
        then return.

        :return:
        """

        self._backend.receive_messages(10, process_message)