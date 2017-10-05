from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from django.conf import settings
from six import raise_from

from messaging.messages.factory import get_message_type
from util.broker import BrokerDetails
from .backends.factory import get_message_backend
from .exceptions import CommandMessageExecuteFailure, InvalidCommandMessage

logger = logging.getLogger(__name__)


class CommandMessageManager(object):
    def __new__(cls):
        """Singleton support for manager"""
        if not hasattr(cls, 'instance'):
            cls.instance = super(CommandMessageManager, cls).__new__(cls)

        return cls.instance

    def __init__(self):
        """Instantiate CommandMessageManager based on setting values"""

        # Set up the backend message passing... right now its just RabbitMQ or SQS
        broker_type = BrokerDetails.from_broker_url(settings.BROKER_URL).get_type()

        self._backend = get_message_backend(broker_type)

    def send_messages(self, commands):
        """Serialize CommandMessages and send via configured message broker

        The command.to_json() and command.message_type will be used to generate
        serialized form of CommandMessage for transmission across the wire.

        :param command: CommandMessages to be sent via configured broker
        :type command: [`messaging.messages.message.CommandMessage`]
        """

        messages = [{"type": x.type, "body": x.to_json()} for x in commands]
        self._backend.send_messages(messages)

    def receive_messages(self):
        """Main entry point to message processing.

        This will process up to a batch of 10 messages at a time. Behavior may
        differ slightly based on message backend. RabbitMQ will immediately
        iterate over up to 10 messages, process and return. SQS will long-poll
        up to 20 seconds or until 10 messages have been processed, process and
        then return.

        New messages will potentially be sent within this method, if CommandMessage populates
        the new_messages list.
        """

        message_generator = self._backend.receive_messages(10)

        # Manually control iteration, so we can pass back success/failure to co-routine
        try:
            # Seed message to start processing
            message = message_generator.next()
            while True:
                success = False
                try:
                    self._process_message(message)
                    success = True
                except InvalidCommandMessage:
                    logger.exception('Exception encountered processing message payload. Message remains on queue.')
                except CommandMessageExecuteFailure:
                    logger.exception('CommandMessage failure during execute call. Message remains on queue.')

                # Feed boolean to backend generator and grab next message
                message = message_generator.send(success)
        except StopIteration:
            pass

    @staticmethod
    def _extract_command(message):
        """Reconstitute a CommandMessage from incoming raw message payload

        :param message: Incoming message payload
        :type message: dict
        :return: Instantiated CommendMessage
        :rtype: `messaging.messages.message.CommandMessage`
        """
        if 'type' not in message:
            raise InvalidCommandMessage('Invalid message missing type: %s', message)

        if 'body' not in message:
            raise InvalidCommandMessage('Missing body in message.')

        try:
            message_class = get_message_type(message['type'])
            message_body = message['body']

            return message_class.from_json(message_body)
        except KeyError as ex:
            raise_from(InvalidCommandMessage('No message type handler available.'), ex)

    def _process_message(self, message):
        """Inspects message for type and then attempts to launch execution

        This function will potentially fire off new messages as required by
        execution logic within CommandMessage extending class. These messages
        will only be sent if command execution is successful.

        :param message: message payload
        :type message: dict
        :raises InvalidCommandMessage:
        :raises CommandMessageExecuteFailure: Failure during CommandMessage.execute
        """

        command = self._extract_command(message)
        logger.info('Processing message of type %s', command.type)
        success = command.execute()

        if not success:
            raise CommandMessageExecuteFailure

        # If execute is successful, we need to fire off any downstream messages
        self._send_downstream(command.new_messages)

        logger.info('Successfully completed message of type %s', command.type)

    def _send_downstream(self, messages):
        """Send any required downstream messages following a CommandMessage.execute
        :param messages: List of CommandMessage instances to send downstream
        :type messages: [`messaging.message.CommandMessage`]
        """
        if len(messages):
            logger.info('Sending %i downstream CommandMessage(s).', len(messages))
            self.send_messages(messages)
