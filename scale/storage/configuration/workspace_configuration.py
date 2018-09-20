"""Defines the configuration for a storage Workspace"""
from __future__ import unicode_literals

from jsonschema import validate
from jsonschema.exceptions import ValidationError

import storage.brokers.factory as broker_factory
from storage.configuration.exceptions import InvalidWorkspaceConfiguration

class WorkspaceConfiguration(object):
    """Represents the configuration for a storage Workspace.
    The configuration includes details about the storage broker system required to read, write, move, or delete files
    within the workspace.
    """

    def __init__(self):
        """Represents a workspace configuration
        """

        self.configuration = {}

    def get_dict(self):
        """Returns the internal dictionary that represents this workspace configuration.

        :returns: The internal dictionary
        :rtype: dict
        """

        return self.configuration

    def validate_broker(self):
        """Validates the current broker-specific configuration.

        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`storage.configuration.exceptions.InvalidWorkspaceConfiguration`: If there is a configuration
            problem.
        """

        broker = broker_factory.get_broker(self.configuration['broker']['type'])
        return broker.validate_configuration(self.configuration['broker'])
