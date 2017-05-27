"""Defines the base scanner class"""
from __future__ import unicode_literals

import logging
import os
from abc import ABCMeta, abstractmethod

from django.db import transaction

from ingest.models import Ingest, Scan
from ingest.scan.scanners.exceptions import ScannerInterruptRequested
from storage.models import Workspace

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
        self._batch_size = 1000  # Use a batch size of 1000 for scan
        self._count = 0
        self._dry_run = False  # Used to only scan and skip ingest process
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

        :param dry_run: Flag to enable file scanning only, no file ingestion will occur
        :type dry_run: bool
        """

        logger.info('Running %s scanner %s...' % (self.scanner_type, 'in dry run mode ' if dry_run else ''))
        self._dry_run = dry_run

        # Initialize workspace scan via storage broker. Configuration determines if recursive workspace walk.
        files = self._scanned_workspace.list_files(recursive=self._recursive)

        batched_files = []
        for file in files:
            batched_files.append(file)

            # Process files every time a batch size is reached
            if len(batched_files) >= self._batch_size:
                self._process_scanned(batched_files)
                batched_files = []

        # If any remaining files, process
        if len(batched_files):
            self._process_scanned(batched_files)

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

    def _process_scanned(self, file_list):
        """Method for handling files identified by list_files Generator
        
        :param file_list: List of files found within workspace
        :type file_list: storage.brokers.broker.FileDetails
        """

        ingests = []

        for file_details in file_list:
            if not self._stop_received:
                ingest = self._ingest_file(file_details.file, file_details.size)
                # Only bother appending ingests that are instantiated, they won't be for dry run
                if ingest:
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

        # bulk insert remaining as queued and note detected files in Scan mode
        with transaction.atomic():
            Ingest.objects.bulk_create(ingests)
            Scan.objects.filter(pk=self.scan_id).update(file_count=self._count)

        Ingest.objects.start_ingest_tasks(ingests, scan_id=self.scan_id)

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

        deduplicate_file_names = set()
        list_count = len(new_ingests)
        ingest_file_names = [ingest.file_name for ingest in new_ingests]

        existing_ingests = Ingest.objects.get_ingests_by_scan(scan_id, ingest_file_names)
        existing_ingest_file_names = [ingest.file_name for ingest in existing_ingests]

        deduplicated_ingests = []
        for ingest in new_ingests:
            if ingest.file_name not in deduplicate_file_names:
                deduplicate_file_names.add(ingest.file_name)
                deduplicated_ingests.append(ingest)
            else:
                logging.info('Removed duplicate file_name %s from ingests at file_path %s',
                             ingest.file_name, ingest.file_path)

        final_ingests = [x for x in deduplicated_ingests if x.file_name not in existing_ingest_file_names]

        logger.info('Removed %i duplicates of pre-existing ingests.', list_count - len(final_ingests))

        return final_ingests

    def _process_ingest(self, file_path, file_size):
        """Processes the ingest file by applying the Scan configuration rules.
        
        This method will populate the ingest model and insert ingest object into
        appropriate list for later batch inserts.

        :param file_path: The relative location of the ingest file within the workspace
        :type file_path: string
        :param file_size: The size of the file in bytes
        :type file_size: long
        :returns: The ingest model prepped for bulk create
        :rtype: :class:`ingest.models.Ingest`
        """

        file_name = os.path.basename(file_path)

        ingest = Ingest.objects.create_ingest(file_name, self._scanned_workspace, scan_id=self.scan_id)
        ingest.file_path = file_path
        ingest.file_size = file_size
        logger.info('New ingest in %s: %s', ingest.workspace.name, ingest.file_name)

        if ingest.is_there_rule_match(self._file_handler, self._workspaces):
            return ingest

            # If is_there_rule_match matches a rule ingest will be returned above, otherwise None is default
