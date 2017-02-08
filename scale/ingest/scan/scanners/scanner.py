"""Defines the base scanner class"""
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod
import logging
import os

from django.db import transaction
from django.utils.timezone import now

from ingest.models import Ingest, Scan
from job.configuration.configuration.job_configuration import JobConfiguration, MODE_RW
from job.configuration.data.job_data import JobData
from queue.models import Queue
from storage.media_type import get_media_type
from storage.models import Workspace
from trigger.models import TriggerEvent
from util.file_size import file_size_to_string


logger = logging.getLogger(__name__)


class Scanner(object):
    """Abstract class for a scanner that processes existing files to ingest. Sub-classes must have a no-argument
    constructor that passes in the correct scanner type and supported broker types and should override the
    load_configuration(), run(), stop(), and validate_configuration() methods.
    """

    __metaclass__ = ABCMeta

    def __init__(self, scanner_type, supported_broker_types):
        """Constructor

        :param scanner_type: The type of this scanner
        :type scanner_type: string
        :param supported_broker_types: The broker types supported by this scanner
        :type supported_broker_types: [string]
        """

        self.scan_id = None
        self._count = 0
        self._dry_run = False # Used to only scan and skip ingest process
        self._file_handler = None  # The file handler configured for this scanner
        self._recursive = True
        self._scanned_workspace = None  # The workspace model that is being scanned
        self._scanner_type = scanner_type
        self._stop_received = False
        self._supported_broker_types = supported_broker_types
        self._workspaces = {}  # The workspaces needed by this scanner, stored by workspace name {string: workspace}
        
    def set_recursive(self, recursive):
        """Support configuration of scanner recursive property
        
        :param recursive: The flag indicating whether workspace will be recursively scanned
        :type recursive: bool
        """
        
        self._recursive = recursive

    @property
    def scanner_type(self):
        """The type of this scanner

        :returns: The scanner type
        :rtype: string
        """

        return self._scanner_type

    @property
    def supported_broker_types(self):
        """The broker types supported by this scanner

        :returns: The broker types supported by this scanner
        :rtype: [string]
        """

        return self._supported_broker_types

    @abstractmethod
    def load_configuration(self, configuration):
        """Loads the given configuration

        :param configuration: The configuration as a dictionary
        :type configuration: dict
        """

        raise NotImplementedError

    def run(self, dry_run=False):
        """Runs the scanner until signaled to stop by the stop() method or processing complete.
        Sub-classes that override this method should ensure the stop() method can quickly terminate the scan process.

        Sub-classes should call _create_ingest() when they identify a file within the workspace. 
        Once _process_ingest() when the transfer is complete. If the sub-class is not tracking
        transfer time, it should just call _process_ingest().
        
        :param dry_run: Flag to enable file scanning only, no file ingestion will occur
        :type dry_run: bool
        """

        logger.info('Running %s scanner %s...' % (self.scanner_type, 'in dry run mode ' if dry_run else ''))
        self._dry_run = dry_run

        # Initialize workspace scan via storage broker. Configuration determines if recursive workspace walk.
        self._scanned_workspace.list_files(recursive=self._recursive, callback=self._callback)
        
        logger.info('%s %i files during scan.' % ('Detected' if self._dry_run else 'Processed', self._count))

    def setup_workspaces(self, scanned_workspace, file_handler):
        """Sets up the workspaces that will be used by this scanner

        :param scanned_workspace: The name of the workspace that is being scanned
        :type scanned_workspace: string
        :param file_handler: The file handler configured for this monitor
        :type file_handler: :class:`ingest.handlers.file_handler.FileHandler`
        """

        workspace_names = {scanned_workspace}
        for rule in file_handler.rules:
            if rule.new_workspace:
                workspace_names.add(rule.new_workspace)

        workspaces = {}
        for workspace in Workspace.objects.filter(name__in=workspace_names):
            workspaces[workspace.name] = workspace

        self._file_handler = file_handler
        self._workspaces = workspaces
        self._scanned_workspace = workspaces[scanned_workspace]

    def stop(self):
        """Signals the scanner to stop running.

        It is the responsibility of sub-classes that override the run() call to monitor this instance variable and stop
        as gracefully and quickly as possible.
        """

        self._stop_received = True

    @abstractmethod
    def validate_configuration(self, configuration):
        """Validates the given configuration.

        Sub-classes must validate scanner type specific configuration and return a list of warnings if encountered.

        :param configuration: The configuration as a dictionary
        :type configuration: dict
        :returns: A list of warnings discovered during validation
        :rtype: [:class:`ingest.scan.configuration.scan_configuration.ValidationWarning`]

        :raises :class:`ingest.scan.scanners.exceptions.InvalidScannerConfiguration`: If the given configuration is
            invalid
        """

        raise NotImplementedError
        
    def _callback(self, file_list):
        """Callback for handling files identified by list_files callback
        
        :param file_list: List of files found within workspace
        :type file_list: string
        """
        
        ingests = []
        
        for file_name in file_list:
            if not self._stop_received:
                ingest = self._ingest_file(file_name)
                # Only bother appending ingests 
                if not self._dry_run:
                    ingests.append(ingest)
                self._count += 1
            else:
                raise ScannerInterruptRequested
                
        # If no ingests were added, don't bother moving on
        if not len(ingests):
            logger.debug('No ingests for batch, this will always be the case during a dry-run.')
            return
                
        # Once all ingest rules have been applied, de-duplicate and then bulk insert
        ingests = self._deduplicate_ingest_list(self.scan_id, ingests)
        
        # bulk insert remaining as queued
        with transaction.atomic():
            Ingest.objects.bulk_create(ingests)
            
        self._start_ingest_tasks(ingests)
        
    @staticmethod
    def _deduplicate_ingest_list(scan_id, new_ingests):
        """Check the ingest records to ensure these ingests are not already created by previous scan run
        
        :param scan_id: ID of scan to check against
        :type scan_id: integer
        :param new_ingests: List of ingest models to validate for uniqueness
        :type new_ingests: :class:`ingest.models.Ingest`
        :returns: List of deduplicated ingest models
        :rtype: List[:class:`ingest.models.Ingest`]
        """
        
        list_count = len(new_ingests)
        ingest_file_names = [ingest.file_name for ingest in new_ingests]
        
        existing_ingests = Ingest.objects.get_ingests_by_scan(scan_id, ingest_file_names)
        existing_ingest_file_names = [ingest.file_name for ingest in existing_ingests]
        
        final_ingests = [x for x in new_ingests if x.file_name not in existing_ingest_file_names]

        logger.info('Removed %i duplicates from ingests.' % (list_count - len(final_ingests)))

        return final_ingests

    def _process_ingest(self, file_name, file_size):
        """Processes the ingest file by applying the Scan configuration rules.
        
        This method will populate the ingest model and insert ingest object into
        appropriate list for later batch inserts.

        :param file_name: The relative location of the ingest file within the workspace
        :type file_name: string
        :param file_size: The size of the file in bytes
        :type file_size: long
        :returns: The ingest model prepped for bulk create
        :rtype: :class:`ingest.models.Ingest`
        """

        ingest = Ingest()
        ingest.file_name = file_name
        ingest.scan_id = self.scan_id
        ingest.media_type = get_media_type(file_name)
        ingest.workspace = self._scanned_workspace
        logger.info('New file on %s: %s', ingest.workspace.name, file_name)

        logger.info('Applying rules to %s (%s, %s)', file_name, ingest.media_type, file_size_to_string(file_size) if file_size else 'Unknown')
        ingest.file_name = file_name
        if file_size:
            ingest.file_size = file_size

        matched_rule = self._file_handler.match_file_name(file_name)
        if matched_rule:
            for data_type_tag in matched_rule.data_types:
                ingest.add_data_type_tag(data_type_tag)
            file_path = ingest.file_path
            if matched_rule.new_file_path:
                today = now()
                year_dir = str(today.year)
                month_dir = '%02d' % today.month
                day_dir = '%02d' % today.day
                ingest.new_file_path = os.path.join(matched_rule.new_file_path, year_dir, month_dir, day_dir, file_name)
                file_path = ingest.new_file_path
            workspace_name = ingest.workspace.name
            if matched_rule.new_workspace:
                ingest.new_workspace = self._workspaces[matched_rule.new_workspace]
                workspace_name = ingest.new_workspace.name
            if ingest.new_file_path or ingest.new_workspace:
                logger.info('Rule match, %s will be moved to %s on workspace %s', file_name, file_path, workspace_name)
            else:
                logger.info('Rule match, %s will be registered as %s on workspace %s', file_name, file_path,
                            workspace_name)
        else:
            logger.info('No rule match for %s, file is being skipped', file_name)
            ingest = None
            
        return ingest

    @transaction.atomic
    def _start_ingest_tasks(self, ingests):
        """Starts a batch of tasks for the given scan in an atomic transaction

        :param ingests: The ingest models
        :type ingests: list[:class:`ingest.models.Ingest`]
        """

        # Create new ingest job and mark ingest as QUEUED
        ingest_job_type = Ingest.objects.get_ingest_job_type()
        
        for ingest in ingests:
            # We need to find the id of each ingest that was created. 
            # Using scan_id and file_name together as a unique composite key
            saved_match = Ingest.objects.get(scan_id=ingest.scan_id, file_name=ingest.file_name)

            logger.debug('Creating ingest task for %s', ingest.file_name)
            data = JobData()
            
            # Use result from query to get ingest ID
            data.add_property_input('Ingest ID', str(saved_match.id))
            desc = {'scan_id': self.scan_id, 'file_name': ingest.file_name}
            when = ingest.transfer_ended if ingest.transfer_ended else now()
            event = TriggerEvent.objects.create_trigger_event('SCAN_TRANSFER', None, desc, when)
            job_configuration = JobConfiguration()
            if ingest.workspace:
                job_configuration.add_job_task_workspace(ingest.workspace.name, MODE_RW)
            if ingest.new_workspace:
                job_configuration.add_job_task_workspace(ingest.new_workspace.name, MODE_RW)
            ingest_job = Queue.objects.queue_new_job(ingest_job_type, data, event, job_configuration)

            ingest.job = ingest_job
            ingest.status = 'QUEUED'
            ingest.save()

            logger.debug('Successfully created ingest task for %s', ingest.file_name)
