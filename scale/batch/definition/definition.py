"""Defines the class for managing a batch definition"""
from __future__ import unicode_literals

from batch.definition.exceptions import InvalidDefinition


class BatchDefinition(object):
    """Represents a batch definition"""

    def __init__(self):
        """Constructor
        """

        self.prev_batch_id = None
        self.job_names = []
        self.all_jobs = False

    def validate(self, batch):
        """Validates the given batch to make sure it is valid with respect to this batch definition. This method will
        perform database calls as needed to perform the validation.

        :param batch: The batch model
        :type batch: :class:`batch.models.Batch`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`batch.definition.exceptions.InvalidDefinition`: If the definition is invalid
        """

        if self.prev_batch_id is None:
            raise InvalidDefinition('Batch definition must result in creating at least one recipe')

        if self.prev_batch_id:
            from batch.models import Batch
            prev_batch = Batch.objects.get(id=self.prev_batch_id)
            if batch.recipe_type_id != prev_batch.recipe_type_id:
                raise InvalidDefinition('New batch and previous batch must have the same recipe type')
            if not prev_batch.is_creation_done:
                raise InvalidDefinition('Previous batch must have completed creating all of its recipes')
