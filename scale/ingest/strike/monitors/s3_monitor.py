"""Defines a monitor that watches an AWS SQS queue for S3 file notifications"""
from __future__ import unicode_literals

import json
import logging
import os

from botocore.exceptions import ClientError

from ingest.models import Ingest
from ingest.strike.configuration.strike_configuration import ValidationWarning
from ingest.strike.monitors.exceptions import (InvalidMonitorConfiguration, S3NoDataNotificationError,
                                               SQSNotificationError)
from ingest.strike.monitors.monitor import Monitor
from util.aws import AWSClient, SQSClient

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
        self._credentials = None
        self._region_name = None

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

    def load_configuration(self, configuration):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.load_configuration`
        """

        self._sqs_name = configuration['sqs_name']
        self._region_name = configuration.get('region_name')
        # TODO Change credentials to use an encrypted store key reference
        self._credentials = AWSClient.instantiate_credentials_from_config(configuration)

    def run(self):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.run`
        """

        logger.info('Running experimental S3 Strike processor')

        # Loop endlessly polling SQS queue
        while self._running:
            # Between each pass over the SQS, refresh configuration from database in case of credential changes.
            # This eliminates the need to stop and restart a Strike job to pick up configuration updates.
            self.reload_configuration()

            with SQSClient(self._credentials, self._region_name) as client:
                # For each new file we receive a notification about:
                logger.debug('Beginning long-poll against queue with wait time of %s seconds.' % self.wait_time)
                messages = client.receive_messages(self._sqs_name,
                                                   batch_size=10,
                                                   wait_time_seconds=self.wait_time,
                                                   visibility_timeout=self.visibility_timeout)

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
                            logger.warning('Removing message that cannot be processed.')
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

        warnings = []
        if 'sqs_name' not in configuration:
            raise InvalidMonitorConfiguration('sqs_name is required for s3 monitor')
        if not isinstance(configuration['sqs_name'], basestring):
            raise InvalidMonitorConfiguration('sqs_name must be a string')
        if not configuration['sqs_name']:
            raise InvalidMonitorConfiguration('sqs_name must be a non-empty string')

        # If credentials exist, validate them.
        credentials = AWSClient.instantiate_credentials_from_config(configuration)

        region_name = configuration.get('region_name')

        # Check whether the queue can actually be accessed
        with SQSClient(credentials, region_name) as client:
            try:
                client.get_queue_by_name(configuration['sqs_name'])
            except ClientError:
                warnings.append(ValidationWarning('sqs_access',
                                                  'Unable to access SQS. Check the name, region and credentials.'))

        return warnings

    def _process_s3_notification(self, message):
        """Extracts an S3 notification object from SQS message body and calls on to ingest.
        We want to ensure we have the following minimal values before passing S3 object on:
        - body.Records[x].eventName starts with 'ObjectCreated'
        - body.Records[x].eventVersion == '2.0'
        Once the above have been validated we will pass the S3 record on to ingest, otherwise
        exception will be raised
        :param message: SQS message containing S3 notification object
        :type message: object
        """

        try:
            body = json.loads(message.body)

            # Previously we checked for body.Subject and body.Type, but this unnecessarily forced us to deliver
            # messages via SNS. When writing tools to mirror the S3 Event Notifications delivered via S3 -> SNS -> SQS
            # this arbitrarily required use of SNS to apply the Subject and Type keys. Lifting these checks allows 
            # us to immitate the format with direct programmtic SQS enqueue.
            try:
                message = json.loads(body['Message'])

                for record in message['Records']:
                    if 'eventName' in record and record['eventName'].startswith('ObjectCreated') and \
                                    'eventVersion' in record and record['eventVersion'] == self.event_version_supported:
                        self._ingest_s3_notification_object(record['s3'])
                    else:
                        # Log message that didn't match with valid EventName and EventVersion
                        raise SQSNotificationError('Unable to process message as it does not match '
                                                   'EventName and EventVersion: {}'.format(json.dumps(message)))
            except KeyError as ex:
                raise SQSNotificationError(
                    'Exception: {}'
                    'Unable to process message as it does not appear to be an S3 notification: {}'.format(
                        ex.message, json.dumps(message)))
        except (TypeError, ValueError) as ex:
            raise SQSNotificationError(
                'Exception: {}\nUnable to process message not recognized as valid JSON: {}.'.format(ex.message,
                                                                                                    message))

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
        ingest = Ingest.objects.create_ingest(object_name, self._monitored_workspace, strike_id=self.strike_id)
        logger.info('New ingest in %s: %s', ingest.workspace.name, ingest.file_name)
        self._process_ingest(ingest, object_key, object_size)
        logger.info("Strike ingested '%s' from bucket '%s'..." % (object_key, bucket_name))
