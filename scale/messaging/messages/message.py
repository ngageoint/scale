from abc import ABCMeta, abstractmethod


class CommandMessage(object):
    """This ABC defines the interface all CommandMessage classes should implement.

    If a CommandMessage needs to chain processing together, it should define this via
    the new_messages array.
    """
    __metaclass__ = ABCMeta

    def __init__(self, message_type):
        # List to contain messages that must be passed on downstream by calling CommandMessageManager
        # Must contain elements of type CommandMessage
        self.new_messages = []

        # Unique type of CommandMessage, each type must be registered in apps.py
        self.type = message_type

    @abstractmethod
    def to_json(self):
        """JSON Serializer for CommandMessage subclasses. Must be implemented in all subclasses.

        :return: JSON representation of CommandMessage class.
        :rtype: dict
        """

    @staticmethod
    @abstractmethod
    def from_json(json_dict):
        """JSON deserializer for CommandMessage subclasses. Must be implemented in all subclasses.

        :param json_dict: CommandMessage JSON representation to reconstitute into class instance.
        :type json_dict: dict
        :return: Instantiated class from input JSON
        :rtype: `messaging.messages.CommandMessage`
        """

    @abstractmethod
    def execute(self):
        """Processing logic for all command messages should be implemented within this method.

        It is critical that execution of messages is idempotent - no side effects as result of repeated executions.
        Without idempotency we cannot support messaging backends such as SQS which guarantee 'at least once' delivery.
        No assurances are provided for message ordering, due to the asynchronous nature of messaging system with many
        potential message producers.

        :return: Success or failure of execute operation
        :rtype: bool
        """