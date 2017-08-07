"""Defines the base monitor class"""
from __future__ import unicode_literals

import logging
from abc import ABCMeta

from django.db import transaction

from ingest.models import Ingest, Strike
from storage.models import Workspace
from util.file_size import file_size_to_string

logger = logging.getLogger(__name__)


class Monitor(object):
    """Abstract class for a monitor that processes incoming files to ingest. Sub-classes must have a no-argument
    constructor that passes in the correct monitor type and supported broker types and should override the
    load_configuration(), run(), stop(), and validate_configuration() methods.
    """

    __metaclass__ = ABCMeta

    def __init__(self, monitor_type, supported_broker_types):
        """Constructor

        :param monitor_type: The type of this monitor
        :type monitor_type: string
        :param supported_broker_types: The broker types supported by this monitor
        :type supported_broker_types: [string]
        """

        self._monitor_type = monitor_type
        self._supported_broker_types = supported_broker_types
        self._file_handler = None  # The file handler configured for this monitor
        self._monitored_workspace = None  # The workspace model that is being monitored
        self._workspaces = {}  # The workspaces needed by this monitor, stored by workspace name {string: workspace}
        self.strike_id = None

    @property
    def monitor_type(self):
        """The type of this monitor

        :returns: The monitor type
        :rtype: string
        """

        return self._monitor_type

    @property
    def supported_broker_types(self):
        """The broker types supported by this monitor

        :returns: The broker types supported by this monitor
        :rtype: [string]
        """

        return self._supported_broker_types

    def load_configuration(self, configuration):
        """Loads the given configuration

        :param configuration: The configuration as a dictionary
        :type configuration: dict
        """

        pass

    def reload_configuration(self):
        """Reloads the configuration for this monitor from the database
        """

        if self.strike_id:
            logger.info('Reloading Strike configuration from database')
        else:
            logger.warning('Cannot reload Strike configuration from database: missing Strike ID')

        strike = Strike.objects.get(id=self.strike_id)
        strike.get_strike_configuration().load_monitor_configuration(self)

    def run(self):
        """Runs the monitor until signaled to stop by the stop() method. Sub-classes that override this method should
        make it block until the stop() method is called and should call reload_configuration() on a regular basis to get
        updated configuration from the database.

        Sub-classes should call Ingest.objects.create_ingest() when they detect a new file in the monitored workspace.
        If the sub-class is tracking transfer time (the amount of time it takes for the file to be copied into the
        monitored workspace), it should call _start_transfer(), _update_transfer() as updates occur, and finally
        _complete_transfer() and _process_ingest() when the transfer is complete. If the sub-class is not tracking
        transfer time, it should just call _process_ingest().
        """

        pass

    def setup_workspaces(self, monitored_workspace, file_handler):
        """Sets up the workspaces that will be used by this monitor

        :param monitored_workspace: The name of the workspace that is being monitored
        :type monitored_workspace: string
        :param file_handler: The file handler configured for this monitor
        :type file_handler: :class:`ingest.strike.handlers.file_handler.FileHandler`
        """

        workspace_names = {monitored_workspace}
        for rule in file_handler.rules:
            if rule.new_workspace:
                workspace_names.add(rule.new_workspace)

        workspaces = {}
        for workspace in Workspace.objects.filter(name__in=workspace_names):
            workspaces[workspace.name] = workspace

        self._file_handler = file_handler
        self._workspaces = workspaces
        self._monitored_workspace = workspaces[monitored_workspace]

    def stop(self):
        """Signals the monitor to stop running. Sub-classes that override this method should make it stop the run() call
        as gracefully and quickly as possible.
        """

        pass

    def validate_configuration(self, configuration):
        """Validates the given configuration

        :param configuration: The configuration as a dictionary
        :type configuration: dict
        :returns: A list of warnings discovered during validation
        :rtype: [:class:`ingest.strike.configuration.strike_configuration.ValidationWarning`]

        :raises :class:`ingest.strike.monitors.exceptions.InvalidMonitorConfiguration`: If the given configuration is
            invalid
        """

        return []

    def _complete_transfer(self, ingest, when, bytes_transferred):
        """Completes the transfer of the given ingest into a workspace. The database save is the caller's
        responsibility. This method should only be used if _start_transfer() was called first.

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        :param when: When the transfer of the file completed
        :type when: :class:`datetime.datetime`
        :param bytes_transferred: How many total bytes were transferred
        :type bytes_transferred: long
        """

        if ingest.status != 'TRANSFERRING':
            raise Exception('Invalid ingest status: %s' % ingest.status)
        ingest.status = 'TRANSFERRED'
        ingest.bytes_transferred = bytes_transferred
        ingest.transfer_ended = when
        ingest.file_size = bytes_transferred

        logger.info('%s has finished transferring to %s, total of %s copied', ingest.file_name, ingest.workspace.name,
                    file_size_to_string(bytes_transferred))

    @transaction.atomic
    def _process_ingest(self, ingest, file_path, file_size):
        """Processes the ingest file by applying the Strike configuration rules. This method will update the ingest
        model in the database and create an ingest task (if applicable) in an atomic transaction. This method should
        either be called immediately after Ingest.objects.create_ingest() or after _complete_transfer().

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        :param file_path: The relative location of the ingest file within the workspace
        :type file_path: string
        :param file_size: The size of the file in bytes
        :type file_size: long
        """

        if ingest.status not in ['TRANSFERRING', 'TRANSFERRED']:
            raise Exception('Invalid ingest status: %s' % ingest.status)

        ingest.file_path = file_path
        ingest.file_size = file_size

        # Rule match case
        if ingest.is_there_rule_match(self._file_handler, self._workspaces):
            if not ingest.id:
                ingest.save()
            Ingest.objects.start_ingest_tasks([ingest], strike_id=self.strike_id)
        # No rule match
        else:
            ingest.status = 'DEFERRED'
            ingest.save()

    def _start_transfer(self, ingest, when):
        """Starts recording the transfer of the given ingest into a workspace. The database save is the caller's
        responsibility. This method should only be used immediately after Ingest.objects.create_ingest().

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        :param when: When the transfer of the file started
        :type when: :class:`datetime.datetime`
        :param bytes_transferred: How many bytes have currently been transferred
        :type bytes_transferred: long
        """

        if ingest.status != 'TRANSFERRING':
            raise Exception('Invalid ingest status: %s' % ingest.status)
        ingest.transfer_started = when

        logger.info('%s is transferring to %s', ingest.file_name, ingest.workspace.name)

    def _update_transfer(self, ingest, bytes_transferred):
        """Updates how many bytes have currently been transferred for the given ingest. The database save is the
        caller's responsibility. This method should only be used between calls to _start_transfer() and
        _complete_transfer().

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        :param bytes_transferred: How many bytes have currently been transferred
        :type bytes_transferred: long
        """

        if ingest.status != 'TRANSFERRING':
            raise Exception('Invalid ingest status: %s' % ingest.status)
        ingest.bytes_transferred = bytes_transferred

        logger.info('%s of %s copied', file_size_to_string(bytes_transferred), ingest.file_name)
