from __future__ import unicode_literals

import logging

from django.conf import settings

from .message.factory import get_message_type
from .backends.factory import get_message_backend

from util.broker import BrokerDetails


logger = logging.getLogger(__name__)


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

        # Set up the bakend message passing... right now its just RabbitMQ or SQS
        broker_type = BrokerDetails.from_broker_url(settings.BROKER_URL).get_type()
        
        self._backend = get_message_backend(broker_type)

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
        
        New messages will potentially be sent within this method, if CommandMessage populates
        the new_messages array.
        """

        messages = self._backend.receive_messages(10)
        
        for message in messages:
            self._process_message(message)
    
    def _process_message(self, message):
        """Inspects message for type and then attempts to launch execution
        
        This function will potentially fire off new messages as required by 
        execution logic within CommandMessage extending class. These messages
        will only be sent if command execution is successful.
    
        :param message: message payload
        :type message: dict
        """
    
        if 'type' in message:
            if 'body' in message:
                try:
                    message_class = get_message_type(message['type'])
                    message_body = message['body']
    
                    processor = message_class.from_json(message_body)
                    
                    success = processor.execute()
                    
                    # If execute is successful, we need to fire off all downstream messages
                    if success and processor.new_messages:
                        logger.info('Sending %i downstream CommandMessage(s).', len(processor.new_messages))
                        for new_message in processor.new_messages:
                            self.send_message(new_message)
                            
                    if success:
                        return
                except KeyError as ex:
                    logger.exception('No message type handler available.')
            else:
                logger.error('Missing body in message.')
        else:
            logger.error('Invalid message missing type: %s', message)
    
        logger.error('Failure processing message: %s', message)