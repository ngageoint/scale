"""Defines the base monitor class"""
from abc import ABCMeta
import logging
import os

from django.db import transaction
from django.utils.timezone import now

from ingest.models import Ingest, Strike
from job.configuration.configuration.job_configuration import JobConfiguration, MODE_RW
from queue.models import Queue
from storage.media_type import get_media_type
from storage.models import Workspace
from trigger.models import TriggerEvent
from util.file_size import file_size_to_string


logger = logging.getLogger(__name__)


class Monitor(object):
    """Abstract class for a monitor that processes incoming files to ingest. Sub-classes must have a no-argument
    constructor that passes in the correct monitor type and should override the load_configuration(), run(), stop(), and
    validate_configuration() methods.
    """

    __metaclass__ = ABCMeta

    def __init__(self, monitor_type):
        """Constructor

        :param monitor_type: The type of this monitor
        :type monitor_type: string
        """

        self._monitor_type = monitor_type
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

    def load_configuration(self, configuration, monitored_workspace, file_handler):
        """Loads the given configuration. Sub-classes that override this method should make sure that they call
        self._setup_workspaces().

        :param configuration: The configuration as a dictionary
        :type configuration: dict
        :param monitored_workspace: The name of the workspace that is being monitored
        :type monitored_workspace: string
        :param file_handler: The file handler configured for this monitor
        :type file_handler: :class:`ingest.strike.handlers.file_handler.FileHandler`
        """

        self._setup_workspaces(monitored_workspace, file_handler)

    def reload_configuration(self):
        """Reloads the configuration for this monitor from the database
        """

        if not self.strike_id:
            logger.warning('Cannot reload Strike configuration from database: missing Strike ID')

        strike = Strike.objects.get(id=self.strike_id)
        strike.get_strike_configuration().load_monitor_configuration(self)

    def run(self):
        """Runs the monitor until signaled to stop by the stop() method. Sub-classes that override this method should
        make it block until the stop() method is called and should call reload_configuration() on a regular basis to get
        updated configuration from the database.

        Sub-classes should call _create_ingest() when they detect a new file in the monitored workspace. If the
        sub-class is tracking transfer time (the amount of time it takes for the file to be copied into the monitored
        workspace), it should call _start_transfer(), _update_transfer() as updates occur, and finally
        _complete_transfer() and _process_ingest() when the transfer is complete. If the sub-class is not tracking
        transfer time, it should just call _process_ingest().
        """

        pass

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
        ingest.transfer_started = when

        logger.info('%s has finished transferring to %s, total of %s copied', ingest.file_name, ingest.workspace.name,
                    file_size_to_string(bytes_transferred))

    def _create_ingest(self, file_name):
        """Creates a new ingest for the given file name. The database save is the caller's responsibility.

        :param file_name: The name of the file being ingested
        :type file_name: string
        :returns: The new ingest model
        :rtype: :class:`ingest.models.Ingest`
        """

        ingest = Ingest()
        ingest.file_name = file_name
        ingest.strike_id = self.strike_id
        ingest.media_type = get_media_type(file_name)
        ingest.workspace = self._monitored_workspace

        logger.info('New file on %s: %s', ingest.workspace.name, file_name)
        return ingest

    @transaction.atomic
    def _process_ingest(self, ingest, file_path, file_size):
        """Processes the ingest file by applying the Strike configuration rules. This method will update the ingest
        model in the database and create an ingest task (if applicable) in an atomic transaction. This method should
        either be called immediately after _create_ingest() or after _complete_transfer().

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        :param file_path: The relative location of the ingest file within the workspace
        :type file_path: string
        :param file_size: The size of the file in bytes
        :type file_size: long
        """

        if ingest.status not in ['TRANSFERRING', 'TRANSFERRED']:
            raise Exception('Invalid ingest status: %s' % ingest.status)

        file_name = ingest.file_name
        logger.info('Applying rules to %s (%s, %s)', file_name, ingest.media_type, file_size_to_string(file_size))
        ingest.file_path = file_path
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
            self._start_ingest_task(ingest)
        else:
            logger.info('No rule match for %s, file is being deferred', file_name)
            ingest.save()

    def _setup_workspaces(self, monitored_workspace, file_handler):
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

    @transaction.atomic
    def _start_ingest_task(self, ingest):
        """Starts a task for the given ingest in an atomic transaction

        :param ingest: The ingest model
        :type ingest: :class:`ingest.models.Ingest`
        """

        logger.info('Creating ingest task for %s', ingest.file_name)

        # TODO: change this when updating ingest job
        # Atomically create new ingest job and mark ingest as QUEUED
        ingest_job_type = Ingest.objects.get_ingest_job_type()
        data = {
            'version': '1.0',
            'input_data': [
                {'name': 'Ingest ID', 'value': str(ingest.id)}
            ]
        }
        desc = {'strike_id': self.strike_id, 'file_name': ingest.file_name}
        when = ingest.transfer_ended if ingest.transfer_ended else now()
        event = TriggerEvent.objects.create_trigger_event('STRIKE_TRANSFER', None, desc, when)
        job_configuration = JobConfiguration()
        if ingest.workspace:
            job_configuration.add_job_task_workspace(ingest.workspace.name, MODE_RW)
        if ingest.new_workspace:
            job_configuration.add_job_task_workspace(ingest.new_workspace.name, MODE_RW)
        ingest_job = Queue.objects.queue_new_job(ingest_job_type, data, event, job_configuration)

        ingest.job = ingest_job
        ingest.status = 'QUEUED'
        ingest.save()

        logger.info('Successfully created ingest task for %s', ingest.file_name)

    def _start_transfer(self, ingest, when, bytes_transferred):
        """Starts recording the transfer of the given ingest into a workspace. The database save is the caller's
        responsibility. This method should only be used immediately after _create_ingest().

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
        ingest.bytes_transferred = bytes_transferred

        logger.info('%s is transferring to %s, %s copied so far', ingest.file_name, ingest.workspace.name,
                    file_size_to_string(bytes_transferred))

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

        logger.info('%s is still transferring to %s, %s copied so far', ingest.file_name, ingest.workspace.name,
                    file_size_to_string(bytes_transferred))
