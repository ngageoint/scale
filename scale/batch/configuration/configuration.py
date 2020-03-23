"""Defines the class for managing a batch configuration"""
from __future__ import unicode_literals

from batch.configuration.exceptions import InvalidConfiguration

class BatchConfiguration(object):
    """Represents a batch configuration"""

    def __init__(self):
        """Constructor
        """

        self.priority = None
        self.input_map = None

    def validate(self, batch):
        """Validates the given batch to make sure it is valid with respect to this batch configuration. This method will
        perform database calls as needed to perform the validation.

        :param batch: The batch model
        :type batch: :class:`batch.models.Batch`
        :returns: A list of warnings discovered during validation
        :rtype: :func:`list`

        :raises :class:`batch.configuration.exceptions.InvalidConfiguration`: If the configuration is invalid
        """

        warnings = []

        # Verify the configuration input map matches the dataset parameters
        if self.input_map and batch.get_definition().dataset:
            from data.models import DataSet
            the_dataset = DataSet.objects.get(pk=batch.get_definition().dataset)
            for input in self.input_map:
                param_name = input['datasetParameter']
                if param_name not in the_dataset.get_definition().param_names:
                    msg = '%s does not exist in the dataset parameter list' % param_name
                    raise InvalidConfiguration('INVALID_INPUT_MAP', msg)

        return warnings
