from abc import ABCMeta

from .backends.amqp import AMQPMessagingBackend

class CommandMessage(object):

    __metaclass__ = ABCMeta

    def __init__(self, message_type):

        # Result of CommandMessage # TODO: Why do we need this over just returning success from execute?
        self.succeeded = False

        # List to contain messages that must be passed on downstream by calling CommandMessageManager
        # Must contain elements of type CommandMessage
        self.new_messages = []

        # Unique type of CommandMessage, each type must be registered in apps.py
        self.type = message_type

        pass

    def to_json(self):
        """JSON Serializer for CommandMessage subclasses. Must be implemented in all subclasses.

        :return: JSON serialized representation of CommandMessage class.
        :rtype: dict
        """
        raise NotImplementedError

    @staticmethod
    def from_json(json_dict):
        """JSON deserializer for CommandMessage subclasses. Must be implemented in all subclasses.

        :param json_dict: CommandMessage JSON representation to reconstitute into class instance.
        :type json_dict: dict
        :return: Instantiated class from input JSON
        :rtype: `messaging.messages.CommandMessage`
        """
        raise NotImplementedError

    def execute(self):
        """Processing logic for all command messages should be implemented within this method.

        It is critical that execution of messages is idempotent - no side effects as result of repeated executions.
        Without idempotency we cannot support messaging backends such as SQS which guarantee 'at least once' delivery.
        No assurances are provided for message ordering, due to the asynchronous nature of messaging system with many
        potential message producers.

        :return: Success or failure of execute operation
        :rtype: bool
        """
        raise NotImplementedError


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
        self._backend = AMQPMessagingBackend()

        # Retrieve
        pass

    def send_message(self, command):
        """Use command.to_json() to generate payload and then

        :param command:
        :return:
        """
        pass

    def process_messages(self):
        """Main entry point to message processing.

        :return:
        """



        self._backend.receive_messages()

        pass