"""Defines the class for managing a batch configuration"""
from __future__ import unicode_literals


class BatchConfiguration(object):
    """Represents a batch configuration"""

    def __init__(self):
        """Constructor
        """

        self.priority = None

    def validate(self, batch):
        """Validates the given batch to make sure it is valid with respect to this batch configuration. This method will
        perform database calls as needed to perform the validation.

        :param batch: The batch model
        :type batch: :class:`batch.models.Batch`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`batch.configuration.exceptions.InvalidConfiguration`: If the configuration is invalid
        """

        # Currently nothing to do
        pass
