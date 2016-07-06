"""Defines the base monitor class"""
from abc import ABCMeta
import logging

from ingest.models import Strike
from storage.models import Workspace


logger = logging.getLogger(__name__)


# TODO: mention methods that sub-classes should override (load_configuration, validate_configuration)
class Monitor(object):
    """Abstract class for a monitor that processes incoming files to ingest. Sub-classes must have a no-argument
    constructor that passes in the correct monitor type.
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
