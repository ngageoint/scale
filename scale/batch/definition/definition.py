"""Defines the class for managing a batch definition"""
from __future__ import unicode_literals

from batch.definition.exceptions import InvalidDefinition


class BatchDefinition(object):
    """Represents a batch definition"""

    def __init__(self):
        """Constructor
        """

        self.root_batch_id = None
        self.job_names = []
        self.all_jobs = False

    def estimate_recipe_total(self, batch):
        """Estimates the number of recipes that will be created for the given batch. The given batch must have all of
        its related fields populated, though id and root_batch_id may be None.

        :param batch: The batch model
        :type batch: :class:`batch.models.Batch`
        :returns: The estimated number of recipes that will be created by the batch
        :rtype: int
        """

        estimate = 0

        if batch.superseded_batch:
            estimate += batch.superseded_batch.recipes_total

        return estimate

    def validate(self, batch):
        """Validates the given batch to make sure it is valid with respect to this batch definition. The given batch
        must have all of its related fields populated, though id and root_batch_id may be None.

        :param batch: The batch model
        :type batch: :class:`batch.models.Batch`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`batch.definition.exceptions.InvalidDefinition`: If the definition is invalid
        """

        if self.root_batch_id is None:
            raise InvalidDefinition('Batch definition must result in creating at least one recipe')

        if self.root_batch_id:
            if batch.recipe_type_id != batch.superseded_batch.recipe_type_id:
                raise InvalidDefinition('New batch and previous batch must have the same recipe type')
            if not batch.superseded_batch.is_creation_done:
                raise InvalidDefinition('Previous batch must have completed creating all of its recipes')
