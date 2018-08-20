"""Defines the configuration for running an instance of Strike"""
from __future__ import unicode_literals

import logging
import os
import re

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from ingest.handlers.file_handler import FileHandler
from ingest.handlers.file_rule import FileRule
from ingest.strike.configuration.exceptions import InvalidStrikeConfiguration
from ingest.strike.monitors import factory
from storage.models import Workspace

logger = logging.getLogger(__name__)


class StrikeConfiguration(object):
    """Represents the configuration for a running Strike instance. The configuration includes details about mounting the
    transfer NFS directory, the suffix for identifying files still being transferred, and regular expressions to
    identify files to ingest and how to store them.
    """

    def __init__(self):
        """Creates a Strike configuration object from the given dictionary. The general format is checked for
        correctness, but the specified workspace(s) are not checked.

        :param configuration: The Strike configuration
        :type configuration: dict
        :raises InvalidStrikeConfiguration: If the given configuration is invalid
        """

        self.configuration = {}
        
        self.file_handler = FileHandler()

    def get_dict(self):
        """Returns the internal dictionary that represents this Strike process configuration.

        :returns: The internal dictionary
        :rtype: dict
        """

        return self.configuration

    def get_monitor(self):
        """Returns the configured monitor for this Strike configuration

        :returns: The configured monitor
        :rtype: :class:`ingest.strike.monitors.monitor.Monitor`
        """

        monitor_type = self.configuration['monitor']['type']
        monitor = factory.get_monitor(monitor_type)
        self.load_monitor_configuration(monitor)
        return monitor

    def get_workspace(self):
        """Returns the monitored workspace name for this Strike configuration

        :returns: The monitored workspace name
        :rtype: string
        """

        return self.configuration['workspace']

    def load_monitor_configuration(self, monitor):
        """Loads the configuration into the given monitor

        :param monitor: The configuration as a dictionary
        :type monitor: :class:`ingest.strike.monitors.monitor.Monitor`
        """

        monitor_dict = self.configuration['monitor']
        monitor_type = monitor_dict['type']
        workspace = self.configuration['workspace']

        # Only load configuration if monitor type is unchanged
        if monitor_type == monitor.monitor_type:
            monitor.setup_workspaces(workspace, self.file_handler)
            monitor.load_configuration(monitor_dict)
        else:
            msg = 'Strike monitor type has been changed from %s to %s. Cannot reload configuration.'
            logger.warning(msg, monitor.monitor_type, monitor_type)

    def validate(self):
        """Validates the Strike configuration

        :returns: A list of warnings discovered during validation
        :rtype: list[:class:`util.validation.ValidationWarning`]

        :raises :class:`ingest.strike.configuration.exceptions.InvalidStrikeConfiguration`: If the configuration is
            invalid.
        """

        warnings = []

        monitor_type = self.configuration['monitor']['type']
        if monitor_type not in factory.get_monitor_types():
            raise InvalidStrikeConfiguration('\'%s\' is an invalid monitor type' % monitor_type)

        monitored_workspace_name = self.configuration['workspace']
        workspace_names = {monitored_workspace_name}
        for rule in self.file_handler.rules:
            if rule.new_workspace:
                workspace_names.add(rule.new_workspace)

        for workspace in Workspace.objects.filter(name__in=workspace_names):
            if workspace.name == monitored_workspace_name:
                broker_type = workspace.get_broker().broker_type
                monitor = factory.get_monitor(monitor_type)
                if broker_type not in monitor.supported_broker_types:
                    msg = 'Monitor type %s does not support broker type %s'
                    raise InvalidStrikeConfiguration(msg % (monitor_type, broker_type))
            if not workspace.is_active:
                raise InvalidStrikeConfiguration('Workspace is not active: %s' % workspace.name)
            workspace_names.remove(workspace.name)

        if workspace_names:
            raise InvalidStrikeConfiguration('Unknown workspace name: %s' % workspace_names.pop())

        return warnings
