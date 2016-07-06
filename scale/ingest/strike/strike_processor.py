"""Defines the Strike Processor which watches a directory for incoming files and prepares them to be ingested after they
are fully transferred"""
from __future__ import unicode_literals

import json
import logging
import os
from datetime import datetime

import boto3
from django.db import transaction
from django.utils.timezone import now

from ingest.container import SCALE_INGEST_MOUNT_PATH
from ingest.models import Ingest
from ingest.strike.exceptions import SQSNotificationError, S3NoDataNotificationError
from queue.models import Queue
from storage.media_type import get_media_type
from storage.nfs import nfs_mount, nfs_umount
from trigger.models import TriggerEvent

logger = logging.getLogger(__name__)


class StrikeProcessor(object):
    """This class processes files in a given directory (the Strike directory)
    by waiting until a file has been completely transferred to the Strike
    directory (tracking progress along the way) and then determining if the
    file should be ingested (by creating an ingest task) or deferred for later
    evaluation.
    """

    def __init__(self, strike_id, job_exe_id, configuration):
        """Constructor

        :param strike_id: The ID of the Strike process
        :type strike_id: int
        :param job_exe_id: The ID of the job execution
        :type job_exe_id: int
        :param configuration: The Strike configuration
        :type configuration: :class:`ingest.strike.configuration.strike_configuration.StrikeConfiguration`
        """

        self.strike_id = strike_id
        self.job_exe_id = job_exe_id
        self.configuration = configuration
        self.mount = None
        self.sqs_name = None

        self.strike_dir = SCALE_INGEST_MOUNT_PATH
        self.rel_deferred_dir = 'deferred'
        self.rel_duplicate_dir = 'duplicate'
        self.rel_ingest_dir = 'ingesting'
        self.deferred_dir = os.path.join(self.strike_dir, self.rel_deferred_dir)
        self.duplicate_dir = os.path.join(self.strike_dir, self.rel_duplicate_dir)
        self.ingest_dir = os.path.join(self.strike_dir, self.rel_ingest_dir)

        self.load_configuration(configuration)

    def load_configuration(self, configuration):
        """Loads the given configuration

        :param configuration: The Strike configuration
        :type configuration: :class:`ingest.strike.configuration.strike_configuration.StrikeConfiguration`
        """

        self.configuration = configuration

        self.mount = self.configuration.get_mount()
        self.sqs_name = None
        if 'sqs_name' in self.configuration.get_dict():
            self.sqs_name = self.configuration.get_dict()['sqs_name']

    def mount_and_process_dir(self):
        """Mounts NFS and processes the current files in the Strike directory
        """

        if self.sqs_name:
            self._run_s3_notification_sqs_processor()
            return

        try:
            if not os.path.exists(self.strike_dir):
                logger.info('Creating %s', self.strike_dir)
                os.makedirs(self.strike_dir, mode=0755)
            nfs_mount(self.mount, self.strike_dir, read_only=False)
            self._init_dirs()
            self._process_dir()
        except Exception:
            logger.exception('Strike processor encountered error.')
        finally:
            nfs_umount(self.strike_dir)

    def _complete_transfer(self, ingest, size):
        """Completes the transfer for the given ingest and updates the database

        :param transfer: The ingest model
        :type transfer: :class:`ingest.models.Ingest`
        :param size: Total size of the file in bytes
        :type size: long
        """

        file_name = ingest.file_name
        file_path = os.path.join(self.strike_dir, file_name)
        if not ingest.status == 'TRANSFERRING':
            msg = 'Completing transfer for %s requires TRANSFERRING status'
            raise Exception(msg % file_path)
        logger.info('Transfer complete: %s', file_path)
        last_modified = os.path.getmtime(file_path)
        ingest.transfer_ended = datetime.utcfromtimestamp(last_modified)
        ingest.media_type = get_media_type(file_name)
        ingest.file_size = size

        # Check configuration for what to do with this file
        file_config = self.configuration.match_file_name(file_name)
        if file_config:
            for data_type in file_config[0]:
                ingest.add_data_type_tag(data_type)
            today = now()
            # Store file within workspace at /configuration_path/current_year/current_month/current_day/file_name
            year_dir = str(today.year)
            month_dir = '%02d' % today.month
            day_dir = '%02d' % today.day
            ingest.file_path = os.path.join(file_config[1], year_dir, month_dir, day_dir, file_name)
            ingest.workspace = file_config[2]
            ingest.ingest_path = os.path.join(self.rel_ingest_dir, file_name)
        ingest.status = 'TRANSFERRED'
        ingest.save()
        logger.info('Ingest marked as TRANSFERRED: %s', file_name)

    def _defer_file(self, ingest):
        """Defers the file for the given ingest by moving the file and updating
        the database

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        """

        file_name = ingest.file_name
        file_path = os.path.join(self.strike_dir, file_name)
        deferred_path = os.path.join(self.deferred_dir, file_name)
        logger.info('%s is being deferred', file_path)
        if not ingest.status == 'TRANSFERRED':
            msg = 'Cannot defer %s unless it has TRANSFERRED status'
            raise Exception(msg % file_path)

        if os.path.exists(file_path):
            # File is in Strike dir (expected) so move it
            logger.info('Moving %s to %s', file_path, deferred_path)
            os.rename(file_path, deferred_path)
            ingest.status = 'DEFERRED'
        else:
            # File not found in Strike dir (unexpected)
            if os.path.exists(deferred_path):
                msg = ('%s already moved to deferred location %s but not '
                       'marked as DEFERRED, likely due to previous error')
                logger.warning(msg, file_path, deferred_path)
                ingest.status = 'DEFERRED'
            else:
                msg = 'Tried to defer %s, but the file is now lost'
                logger.error(msg, file_name)
                ingest.status = 'ERRORED'

        ingest.save()
        if ingest.status == 'DEFERRED':
            logger.info('Ingest for %s marked as DEFERRED', file_name)
        else:
            logger.info('Ingest for %s marked as ERRORED', file_name)

    def _final_filename(self, file_name):
        """Returns the final name (after transferring is done) for the given
        file. If the file is already done transferring the name given is simply
        returned.

        :param file_name: The name of the file
        :type file_name: str
        :returns: The final name of the file after transferring
        :rtype: str
        """

        suffix = self.configuration.get_transfer_suffix()
        if file_name.endswith(suffix):
            return file_name.rstrip(suffix)
        return file_name

    def _init_dirs(self):
        """ Creates the directories necessary for processing files
        """

        if not os.path.exists(self.deferred_dir):
            logger.info('Creating %s', self.deferred_dir)
            os.makedirs(self.deferred_dir, mode=0755)
        if not os.path.exists(self.duplicate_dir):
            logger.info('Creating %s', self.duplicate_dir)
            os.makedirs(self.duplicate_dir, mode=0755)
        if not os.path.exists(self.ingest_dir):
            logger.info('Creating %s', self.ingest_dir)
            os.makedirs(self.ingest_dir, mode=0755)

    def _is_still_transferring(self, file_name):
        """ Indicates whether the given file in the Strike directory is still
        transferring

        :param file_name: The name of the file
        :type file_name: str
        :returns: True if the file is still transferring, False otherwise
        :rtype: bool
        """

        suffix = self.configuration.get_transfer_suffix()
        if file_name.endswith(suffix):
            return True
        return False

    def _prepare_file_for_ingest(self, ingest):
        """Prepares the file for ingest by moving the file and starting an
        ingest task

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        """

        file_name = ingest.file_name
        file_path = os.path.join(self.strike_dir, file_name)
        ingest_path = os.path.join(self.ingest_dir, file_name)
        logger.info('%s is being prepared for ingest', file_path)
        if not ingest.status == 'TRANSFERRED':
            msg = 'Cannot ingest %s unless it has TRANSFERRED status'
            raise Exception(msg % file_path)

        if os.path.exists(file_path):
            # File is in Strike dir (expected) so move it
            logger.info('Moving %s to %s', file_path, ingest_path)
            os.rename(file_path, ingest_path)
        else:
            # File not found in Strike dir (unexpected)
            if os.path.exists(ingest_path):
                msg = '%s already moved to ingest location %s but not marked as QUEUED, likely due to previous error'
                logger.warning(msg, file_path, ingest_path)
            else:
                msg = 'Tried to prepare %s for ingest, but the file is now lost'
                logger.error(msg, file_name)
                ingest.status = 'ERRORED'
                ingest.save()
                logger.info('Ingest for %s marked as ERRORED', file_name)
                return

        # Start ingest task which will mark ingest as QUEUED
        self._start_ingest_task(ingest)

    def _process_dir(self):
        """Processes the current files in the Strike directory
        """
        logger.debug('Processing %s', self.strike_dir)

        # Get current files ordered ascending by modification time
        file_list = []
        for entry in os.listdir(self.strike_dir):
            if os.path.isfile(os.path.join(self.strike_dir, entry)):
                file_list.append(entry)
        file_list.sort(key=lambda x:
                       os.path.getmtime(os.path.join(self.strike_dir, x)))
        logger.debug('%i file(s) in %s', len(file_list), self.strike_dir)

        # Compile a dict of current ingests that need to be processed
        # Ingests that are still TRANSFERRING or have TRANSFERRED but failed to
        # update to DEFERRED, ERRORED, or QUEUED still need to be processed
        ingests = {}
        statuses = ['TRANSFERRING', 'TRANSFERRED']
        ingests_qry = Ingest.objects.filter(status__in=statuses, strike_id=self.strike_id)
        ingests_qry = ingests_qry.order_by('last_modified')
        for ingest in ingests_qry.iterator():
            ingests[ingest.file_name] = ingest

        # Process files in Strike dir
        for file_name in file_list:
            final_file_name = self._final_filename(file_name)
            file_path = os.path.join(self.strike_dir, file_name)
            logger.info('Processing %s', file_path)
            ingest = None
            if final_file_name in ingests:
                ingest = ingests[final_file_name]
                # Clear the ingest to see what's left after files are done
                del ingests[final_file_name]
            try:
                self._process_file(file_name, ingest)
            except Exception:
                logger.exception('Error processing %s', file_path)

        # Process ingests where the file is missing from the Strike dir
        for file_name in ingests.iterkeys():
            ingest = ingests[file_name]
            logger.warning('Processing ingest for missing file %s', file_name)
            try:
                self._process_file(None, ingest)
            except Exception:
                msg = 'Error processing ingest for missing file %s'
                logger.exception(msg, file_name)

    def _process_file(self, file_name, ingest):
        """Processes the given file in the Strike directory. The file_name
        argument represents a file in the Strike directory to process. If
        file_name is None, then the ingest argument represents an ongoing
        transfer where the file is unexpectedly not in the Strike directory.
        If file_name is not None and ingest is None, then this is a
        new transfer without an ingest record yet. If both arguments are None
        an exception is thrown.

        :param file_name: The name of the file to process (possibly None)
        :type file_name: str
        :param ingest: The ingest model for the file (possibly None)
        :type ingest: :class:`ingest.models.Ingest`
        """
        if file_name is None and ingest is None:
            raise Exception('Nothing for Strike to process')
        if file_name is None:
            file_name = ingest.file_name
        file_path = os.path.join(self.strike_dir, file_name)
        final_name = self._final_filename(file_name)

        # Create ingest model for new transfer
        if ingest is None:
            msg = 'New file %s has arrived, creating ingest for %s'
            logger.info(msg, file_path, final_name)
            ingest = Ingest()
            # Ingest model should record the actual name of the file (no
            # temporary suffix)
            ingest.file_name = final_name
            ingest.strike_id = self.strike_id
            # TODO: investigate better way to get start time of transfer
            last_access = os.path.getatime(file_path)
            ingest.transfer_path = os.path.join(self.strike_dir, final_name)
            ingest.transfer_started = datetime.utcfromtimestamp(last_access)

        if ingest.status == 'TRANSFERRING':
            # Update bytes transferred
            size = os.path.getsize(file_path)
            ingest.bytes_transferred = size

            # Ensure that file is still in Strike dir as expected
            if not os.path.exists(file_path):
                msg = '%s was being transferred, but the file is now lost'
                logger.error(msg, file_path)
                ingest.status = 'ERRORED'
                ingest.save()
                logger.info('Ingest for %s marked as ERRORED', final_name)
                return

            if self._is_still_transferring(file_name):
                # Update with current progress of the transfer
                ingest.save()
                logger.info('%s is still transferring, progress updated', file_path)
            else:
                # Transfer is complete, will move on to next section
                self._complete_transfer(ingest, size)

        if ingest.status == 'TRANSFERRED':
            if ingest.ingest_path:
                self._prepare_file_for_ingest(ingest)
            else:
                self._defer_file(ingest)
        elif not ingest.status == 'TRANSFERRING':
            msg = 'Strike not expecting to process file with status %s'
            raise Exception(msg, ingest.status)

    def _start_ingest_task(self, ingest):
        """Starts a task for the given ingest

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        """
        logger.info('Creating ingest task for %s', ingest.file_name)

        # TODO: change this when updating ingest job
        # Atomically create new ingest job and mark ingest as QUEUED
        with transaction.atomic():
            ingest_job_type = Ingest.objects.get_ingest_job_type()
            data = {
                'version': '1.0',
                'input_data': [
                    {'name': 'Ingest ID', 'value': str(ingest.id)},
                    {'name': 'Mount', 'value': self.mount}
                ]
            }
            desc = {'strike_id': self.strike_id, 'file_name': ingest.file_name}
            event = TriggerEvent.objects.create_trigger_event('STRIKE_TRANSFER', None, desc, ingest.transfer_ended)
            ingest_job = Queue.objects.queue_new_job(ingest_job_type, data, event)

            ingest.job = ingest_job
            ingest.status = 'QUEUED'
            ingest.save()

        logger.info('Successfully created ingest task')

    def _run_s3_notification_sqs_processor(self):
        """Subscribe to SQS and process S3 file notifications
        """
        # Get the service resource
        sqs = boto3.resource('sqs')

        # Get the queue
        self.queue = sqs.get_queue_by_name(QueueName=self.sqs_name)

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
        while True:
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
                    logger.exception()
                    message.delete()

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

        self._ingest_s3_file(object_name, object_key, object_size)
        logger.info("Strike ingested '%s' from bucket '%s'..." % (object_key, bucket_name))

    def _ingest_s3_file(self, file_name, file_path, file_size):
        """Subscribe to SQS and process S3 file notifications

        :param file_name: The name of the file
        :type file_name: string
        :param file_path: Relative path (key) in the bucket
        :type file_path: string
        :param file_size: The size of the file in bytes
        :type file_size: long
        """

        right_now = now()

        ingest = Ingest()
        ingest.file_name = file_name
        ingest.strike_id = self.strike_id
        ingest.transfer_path = 'sqs'
        ingest.transfer_started = right_now
        ingest.bytes_transferred = file_size
        ingest.transfer_ended = right_now
        ingest.media_type = get_media_type(file_name)
        ingest.file_size = file_size

        # Check configuration for what to do with this file
        file_config = self.configuration.match_file_name(file_name)
        if not file_config:
            logger.info('Ignoring unmatched file name %s', file_name)
            return

        for data_type in file_config[0]:
            ingest.add_data_type_tag(data_type)
        ingest.file_path = file_path
        ingest.workspace = file_config[2]
        ingest.ingest_path = file_path
        ingest.status = 'TRANSFERRED'
        with transaction.atomic():
            ingest.save()
            self._start_ingest_task(ingest)
