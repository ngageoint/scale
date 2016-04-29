"""Defines the Strike Processor which watches a directory for incoming files and prepares them to be ingested after they
are fully transferred"""
from __future__ import unicode_literals

import logging
import os
from datetime import datetime

from django.db import transaction
from django.utils.timezone import now

from ingest.container import SCALE_INGEST_MOUNT_PATH
from ingest.models import Ingest
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

    def mount_and_process_dir(self):
        """Mounts NFS and processes the current files in the Strike directory
        """

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
