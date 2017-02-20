"""Defines a monitor that watches a minio fed NATS queue for S3 compatible file notifications"""
from __future__ import unicode_literals

import json
import logging
import os

from ingest.strike.configuration.strike_configuration import ValidationWarning
from ingest.strike.monitors.exceptions import (InvalidMonitorConfiguration, S3NoDataNotificationError,
                                               SQSNotificationError)
from ingest.strike.monitors.monitor import Monitor
from util.nats import NATSClient

logger = logging.getLogger(__name__)


class NatsMonitor(Monitor):
    """A monitor that watches a NATS queue for S3 compatible file notifications
    """

    def __init__(self):
        """Constructor
        """

        super(NatsMonitor, self).__init__('nats', ['s3'])
        self._running = True
        self._topic_name = None

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
        # If set to True this will discard any message that cannot be processed to avoid queue blocking.
        # This may be set to False if message visibility timeout hides them for long enough to process
        # other messages in the queue without backing up behind bad messages.
        self.sqs_discard_unrecognized = False
        ###################################################

    def load_configuration(self, configuration):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.load_configuration`
        """

        self._topic_name = configuration['nats_topic_name']

    def run(self):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.run`
        """

        logger.info('Running experimental NATS Strike processor')

        # Loop endlessly polling NATS queue
        while self._running:
            # Between each pass over the NATS, refresh configuration from database in case of credential changes.
            # This eliminates the need to stop and restart a Strike job to pick up configuration updates.
            self.reload_configuration()

            with NATSClient() as client:
                topic = client.get_topic_by_name(self._topic_name, self._process_s3_notification)

                # For each new file we receive a notification about:
                logger.debug('Beginning long-poll against queue with wait time of %s seconds.' % self.wait_time)
                client.connection.wait(duration=self.wait_time, count=self.messages_per_request)

    def stop(self):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.stop`
        """

        self._running = False

    def validate_configuration(self, configuration):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.validate_configuration`
        """

        warnings = []
        if 'nats_topic_name' not in configuration:
            raise InvalidMonitorConfiguration('nats_topic_name is required for NATS monitor')
        if not isinstance(configuration['nats_topic_name'], basestring):
            raise InvalidMonitorConfiguration('nats_topic_name must be a string')
        if not configuration['sqs_name']:
            raise InvalidMonitorConfiguration('nats_topic_name must be a non-empty string')

        # Check whether the bucket can actually be accessed
        with NATSClient() as client:
            if client.get_topic_by_name(configuration['nats_topic_name'], None) is None:
                warnings.append(ValidationWarning('nats_topic_access',
                                                  'Unable to access NATS. Check the name and server.'))

        return warnings

    def _process_s3_notification(self, message):
        """Extracts an S3 notification object from SQS message body and calls on to ingest.
        We want to ensure we have the following minimal values before passing S3 object on:
        - body.Records[x].eventName starts with 's3:ObjectCreated'
        - body.Records[x].eventVersion == '2.0'
        Once the above have been validated we will pass the S3 record on to ingest, otherwise
        exception will be raised
        :param message: NATS message containing S3 notification object
        :type message: object
        """

        try:
            message = json.loads(message.body)

            for record in message['Records']:
                if 'eventName' in record and record['eventName'].startswith('s3:ObjectCreated') and \
                                'eventVersion' in record and record['eventVersion'] == self.event_version_supported:
                    self._ingest_s3_notification_object(record['s3'])
                else:
                    # Log message that didn't match with valid EventName and EventVersion
                    raise SQSNotificationError('Unable to process message as it does not match '
                                               'EventName and EventVersion: '
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

