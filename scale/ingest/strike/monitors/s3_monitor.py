"""Defines a monitor that watches an AWS SQS queue for S3 file notifications"""
from __future__ import unicode_literals

import json
import logging
import os

import boto3

from ingest.strike.monitors.exceptions import (InvalidMonitorConfiguration, S3NoDataNotificationError,
                                               SQSNotificationError)
from ingest.strike.monitors.monitor import Monitor


logger = logging.getLogger(__name__)


class S3Monitor(Monitor):
    """A monitor that watches an AWS SQS queue for S3 file notifications
    """

    def __init__(self):
        """Constructor
        """

        super(S3Monitor, self).__init__('s3', ['s3'])
        self._running = True
        self._sqs_name = None

    def load_configuration(self, configuration):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.load_configuration`
        """

        self._sqs_name = configuration['sqs_name']

    def run(self):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.run`
        """

        # Get the service resource
        sqs = boto3.resource('sqs')

        # Get the queue
        self.queue = sqs.get_queue_by_name(QueueName=self._sqs_name)

        # Set the event version supported in message
        self.event_version_supported = '2.0'

        # TODO: move these values into Strike configuration
        ###################################################
        # Tuning values for performance
        # Messages per request set to 1 to minimize visibility timeout expiration causing multiple watching
        # instances to repeatedly retrieve the same object. Can be bumped up to max (10) if this
        # proves to not be a problem.
        self.messages_per_request = 1
        # Wait time set to the SQS max to reduce chattiness during downtime without notifications.
        # This will perform a long-poll operation over the duration, but end immediately on message receipt
        self.wait_time = 20
        # Duration in seconds for a message to be hidden after retrieved from the queue. If not deleted,
        # it will reappear on the queue after this time.
        self.visibility_timeout = 120
        # If set to True this will discard any message that cannot be processed to avoid queue blocking.
        # This may be set to False if message visibility timeout hides them for long enough to process
        # other messages in the queue without backing up behind bad messages.
        self.sqs_discard_unrecognized = False
        ###################################################

        logger.info('Running experimental S3 Strike processor')

        # Loop endlessly polling SQS queue
        while self._running:
            # For each new file we receive a notification about:
            logger.info('Beginning long-poll against queue with wait time of %s seconds.' % self.wait_time)
            messages = self.queue.receive_messages(MaxNumberOfMessages=self.messages_per_request,
                                                   WaitTimeSeconds=self.wait_time,
                                                   VisibilityTimeout=self.visibility_timeout)

            for message in messages:
                try:
                    # Perform message extraction and then callback to ingest
                    self._process_s3_notification(message)

                    # Remove message from queue now that the message is processed
                    message.delete()
                except SQSNotificationError:
                    logger.exception('Unable to process message. Invalid SQS S3 notification.')

                    if self.sqs_discard_unrecognized:
                        # Remove message from queue when unrecognized
                        message.delete()
                except S3NoDataNotificationError:
                    logger.exception('Unable to process message. File size of 0')
                    message.delete()

    def stop(self):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.stop`
        """

        self._running = False

    def validate_configuration(self, configuration):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.validate_configuration`
        """

        if 'sqs_name' not in configuration:
            raise InvalidMonitorConfiguration('sqs_name is required for s3 monitor')
        if not isinstance(configuration['sqs_name'], basestring):
            raise InvalidMonitorConfiguration('sqs_name must be a string')
        if not configuration['sqs_name']:
            raise InvalidMonitorConfiguration('sqs_name must be a non-empty string')

    def _process_s3_notification(self, message):
        """Extracts an S3 notification object from SQS message body and calls on to ingest.
        We want to ensure we have the following minimal values before passing S3 object on:
        - body.Subject == 'Amazon S3 Notification'
        - body.Type == 'Notification
        - body.Records[x].eventName starts with 'ObjectCreated'
        - body.Records[x].eventVersion == '2.0'
        Once the above have been validated we will pass the S3 record on to ingest, otherwise
        exception will be raised
        :param message: SQS message containing S3 notification object
        :type message: object
        """

        try:
            body = json.loads(message.body)

            if body['Subject'] == 'Amazon S3 Notification' and body['Type'] == 'Notification':
                message = json.loads(body['Message'])

                for record in message['Records']:
                    if 'eventName' in record and record['eventName'].startswith('ObjectCreated') and \
                                    'eventVersion' in record and record['eventVersion'] == self.event_version_supported:
                        self._ingest_s3_notification_object(record['s3'])
                    else:
                        # Log message that didn't match with valid EventName and EventVersion
                        raise SQSNotificationError('Unable to process message as it does not match '
                                                   'EventName and EventVersion: '
                                                   '%s' % json.dumps(message))
            else:
                raise SQSNotificationError('Unable to process message as it does not appear to be an S3 notification: '
                                           '%s' % json.dumps(message))
        except (TypeError, ValueError) as ex:
            raise SQSNotificationError('Exception: %s\nUnable to process message not recognized as valid JSON: %s.' %
                                       (ex.message, message))

    def _ingest_s3_notification_object(self, s3_notification):
        """Extracts S3 specific object metadata and call the final ingest
        We are going to additionally ignore any object of size 0 as these are generally
        folder create operations.
        :param s3_notification: S3 bucket and object metadata associated with notification
        :type s3_notification: dict
        """

        try:
            bucket_name = s3_notification['bucket']['name']
            object_key = s3_notification['object']['key']
            object_size = s3_notification['object']['size']
        except KeyError as ex:
            raise SQSNotificationError(ex)

        if not object_size:
            raise S3NoDataNotificationError('Skipping folder or 0 byte file: %s' % object_key)

        object_name = os.path.basename(object_key)
        ingest = self._create_ingest(object_name)
        self._process_ingest(ingest, object_key, object_size)
        logger.info("Strike ingested '%s' from bucket '%s'..." % (object_key, bucket_name))
