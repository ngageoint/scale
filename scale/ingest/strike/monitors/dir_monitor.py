"""Defines a monitor that watches a file system directory for incoming files"""
from __future__ import unicode_literals

import logging
import math
import os
import time
from datetime import datetime

from django.utils.timezone import now

from ingest.models import Ingest
from ingest.strike.monitors.exceptions import InvalidMonitorConfiguration
from ingest.strike.monitors.monitor import Monitor

logger = logging.getLogger(__name__)


class DirWatcherMonitor(Monitor):
    """A monitor that watches a file system directory for incoming files
    """

    def __init__(self):
        """Constructor
        """

        super(DirWatcherMonitor, self).__init__('dir-watcher', ['host'])
        self._running = True
        self._strike_dir = None
        self._deferred_dir = None
        self._ingest_dir = None
        self._transfer_suffix = None

    def load_configuration(self, configuration):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.load_configuration`
        """

        self._strike_dir = self._monitored_workspace.workspace_volume_path
        self._deferred_dir = os.path.join(self._strike_dir, 'deferred')
        self._ingest_dir = os.path.join(self._strike_dir, 'ingesting')
        self._transfer_suffix = configuration['transfer_suffix']

    def run(self):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.run`
        """

        throttle = 60

        while self._running:
            secs_passed = 0
            try:
                self.reload_configuration()

                # Process the directory and record number of seconds used
                started = now()
                self._mount_and_process_dir()
                ended = now()

                secs_passed = (ended - started).total_seconds()
            except:
                logger.exception('Strike encountered error')
            finally:
                if self._running:
                    # If process time takes less than throttle, delay
                    if secs_passed < throttle:
                        # Delay until full throttle time reached
                        delay = math.ceil(throttle - secs_passed)
                        logger.debug('Pausing for %i seconds', delay)
                        time.sleep(delay)

    def stop(self):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.stop`
        """

        self._running = False

    def validate_configuration(self, configuration):
        """See :meth:`ingest.strike.monitors.monitor.Monitor.validate_configuration`
        """

        if 'transfer_suffix' not in configuration:
            raise InvalidMonitorConfiguration('transfer_suffix is required for dir-watcher monitor')
        if not isinstance(configuration['transfer_suffix'], basestring):
            raise InvalidMonitorConfiguration('transfer_suffix must be a string')
        if not configuration['transfer_suffix']:
            raise InvalidMonitorConfiguration('transfer_suffix must be a non-empty string')

    def _final_filename(self, file_name):
        """Returns the final name (after transferring is done) for the given file. If the file is already done
        transferring the name given is simply returned.

        :param file_name: The name of the file
        :type file_name: string
        :returns: The final name of the file after transferring
        :rtype: string
        """

        if file_name.endswith(self._transfer_suffix):
            return file_name.rstrip(self._transfer_suffix)
        return file_name

    def _init_dirs(self):
        """ Creates the directories necessary for processing files
        """

        if not os.path.exists(self._deferred_dir):
            logger.info('Creating %s', self._deferred_dir)
            os.makedirs(self._deferred_dir, mode=0755)
        if not os.path.exists(self._ingest_dir):
            logger.info('Creating %s', self._ingest_dir)
            os.makedirs(self._ingest_dir, mode=0755)

    def _is_still_transferring(self, file_name):
        """ Indicates whether the given file in the Strike directory is still transferring

        :param file_name: The name of the file
        :type file_name: string
        :returns: True if the file is still transferring, False otherwise
        :rtype: bool
        """

        if file_name.endswith(self._transfer_suffix):
            return True
        return False

    def _mount_and_process_dir(self):
        """Mounts NFS and processes the current files in the directory
        """

        try:
            self._init_dirs()
            self._process_dir()
        except Exception:
            logger.exception('Strike encountered error')

    def _move_deferred_file(self, ingest):
        """Moves the deferred ingest file

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        """

        file_name = ingest.file_name
        file_path = os.path.join(self._ingest_dir, file_name)
        deferred_path = os.path.join(self._deferred_dir, file_name)

        if os.path.exists(file_path):
            # File is in ingest dir (expected) so move it
            logger.info('Moving %s to %s', file_path, deferred_path)
            os.rename(file_path, deferred_path)
        else:
            # File not found in ingest dir (unexpected)
            if os.path.exists(deferred_path):
                logger.warning('Unexpectedly %s has already moved to %s', file_path, deferred_path)
            else:
                logger.error('Tried to move %s to %s, but the file is now lost', file_path, deferred_path)

    def _process_dir(self):
        """Processes the current files in the Strike directory
        """

        logger.debug('Processing %s', self._strike_dir)

        # Get current files ordered ascending by modification time
        file_list = []
        for entry in os.listdir(self._strike_dir):
            if os.path.isfile(os.path.join(self._strike_dir, entry)):
                file_list.append(entry)
        file_list.sort(key=lambda x: os.path.getmtime(os.path.join(self._strike_dir, x)))
        logger.debug('%i file(s) in %s', len(file_list), self._strike_dir)

        # Compile a dict of current ingests that need to be processed
        # Ingests that are still TRANSFERRING or have TRANSFERRED but failed to update to DEFERRED, ERRORED, or QUEUED
        # still need to be processed
        ingests = {}
        statuses = ['TRANSFERRING', 'TRANSFERRED']
        ingests_qry = Ingest.objects.filter(status__in=statuses, strike_id=self.strike_id)
        ingests_qry = ingests_qry.order_by('last_modified')
        for ingest in ingests_qry.iterator():
            ingests[ingest.file_name] = ingest

        # Process files in Strike dir
        for file_name in file_list:
            final_file_name = self._final_filename(file_name)
            file_path = os.path.join(self._strike_dir, file_name)
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
        """Processes the given file in the Strike directory. The file_name argument represents a file in the Strike
        directory to process. If file_name is None, then the ingest argument represents an ongoing transfer where the
        file is unexpectedly not in the Strike directory. If file_name is not None and ingest is None, then this is a
        new transfer without an ingest record yet. If both arguments are None an exception is thrown.

        :param file_name: The name of the file to process (possibly None)
        :type file_name: string
        :param ingest: The ingest model for the file (possibly None)
        :type ingest: :class:`ingest.models.Ingest`
        """

        if file_name is None and ingest is None:
            raise Exception('Nothing for Strike to process')
        if file_name is None:
            file_name = ingest.file_name
        file_path = os.path.join(self._strike_dir, file_name)
        final_name = self._final_filename(file_name)

        # Create ingest model for new transfer
        if ingest is None:
            msg = 'New file %s has arrived, creating ingest for %s'
            logger.info(msg, file_path, final_name)
            ingest = Ingest.objects.create_ingest(final_name, self._monitored_workspace, strike_id=self.strike_id)
            # TODO: investigate better way to get start time of transfer
            last_access = os.path.getatime(file_path)
            self._start_transfer(ingest, datetime.utcfromtimestamp(last_access))

        if ingest.status == 'TRANSFERRING':
            # Update bytes transferred
            size = os.path.getsize(file_path)
            self._update_transfer(ingest, size)

            # Ensure that file is still in Strike dir as expected
            if not os.path.exists(file_path):
                logger.error('%s was being transferred, but the file is now lost', file_path)
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
                last_modified = os.path.getmtime(file_path)
                self._complete_transfer(ingest, datetime.utcfromtimestamp(last_modified), size)
                ingest.save()
                logger.info('Transfer complete: %s', file_path)

        if ingest.status == 'TRANSFERRED':
            ingest_path = os.path.join(self._ingest_dir, file_name)
            rel_ingest_path = os.path.relpath(ingest_path, self._strike_dir)
            logger.info('%s is being prepared for ingest', file_path)
            if not ingest.status == 'TRANSFERRED':
                raise Exception('Cannot ingest %s unless it has TRANSFERRED status' % file_path)

            if os.path.exists(file_path):
                # File is in Strike dir (expected) so move it
                logger.info('Moving %s to %s', file_path, ingest_path)
                os.rename(file_path, ingest_path)
            else:
                # File not found in Strike dir (unexpected)
                if os.path.exists(ingest_path):
                    msg = '%s already moved to %s but not marked as QUEUED, likely due to previous error'
                    logger.warning(msg, file_path, ingest_path)
                else:
                    logger.error('Tried to prepare %s for ingest, but the file is now lost', file_name)
                    ingest.status = 'ERRORED'
                    ingest.save()
                    logger.info('Ingest for %s marked as ERRORED', file_name)
                    return

            self._process_ingest(ingest, rel_ingest_path, ingest.file_size)

        if ingest.status == 'DEFERRED':
            self._move_deferred_file(ingest)
