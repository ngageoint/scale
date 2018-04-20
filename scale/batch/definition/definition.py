"""Defines the class for managing a batch definition"""
from __future__ import unicode_literals

from batch.definition.exceptions import InvalidDefinition
from recipe.handlers.graph_delta import RecipeGraphDelta


class BatchDefinition(object):
    """Represents a batch definition"""

    def __init__(self):
        """Constructor
        """

        self.root_batch_id = None
        self.job_names = []
        self.all_jobs = False

        # Derived fields
        self.estimated_recipes = 0
        self.prev_batch_diff = None

    def validate(self, batch):
        """Validates the given batch to make sure it is valid with respect to this batch definition. The given batch
        must have all of its related fields populated, though id and root_batch_id may be None. The derived definition
        attributes, such as estimated recipe total and previous batch diff, will be populated by this method.

        :param batch: The batch model
        :type batch: :class:`batch.models.Batch`
        :returns: A list of warnings discovered during validation
        :rtype: list

        :raises :class:`batch.definition.exceptions.InvalidDefinition`: If the definition is invalid
        """

        if self.root_batch_id:
            if batch.recipe_type_id != batch.superseded_batch.recipe_type_id:
                raise InvalidDefinition('MISMATCHED_RECIPE_TYPE',
                                        'New batch and previous batch must have the same recipe type')
            if not batch.superseded_batch.is_creation_done:
                raise InvalidDefinition('PREV_BATCH_STILL_CREATING',
                                        'Previous batch must have completed creating all of its recipes')

            # Generate recipe diff against the previous batch
            recipe_graph = batch.recipe_type_rev.get_recipe_definition().get_graph()
            prev_recipe_graph = batch.superseded_batch.recipe_type_rev.get_recipe_definition().get_graph()
            self.prev_batch_diff = RecipeGraphDelta(prev_recipe_graph, recipe_graph)
            if self.all_jobs:
                self.job_names = recipe_graph.get_topological_order()
            if self.job_names:
                for job_name in self.job_names:
                    self.prev_batch_diff.reprocess_identical_node(job_name)
            if not self.prev_batch_diff.can_be_reprocessed:
                raise InvalidDefinition('PREV_BATCH_NO_REPROCESS', 'Previous batch cannot be reprocessed')

        self._estimate_recipe_total(batch)
        if not self.estimated_recipes:
            raise InvalidDefinition('NO_RECIPES', 'Batch definition must result in creating at least one recipe')

        return []

    def _estimate_recipe_total(self, batch):
        """Estimates the number of recipes that will be created for the given batch. The given batch must have all of
        its related fields populated, though id and root_batch_id may be None.

        :param batch: The batch model
        :type batch: :class:`batch.models.Batch`
        """

        self.estimated_recipes = 0

        if batch.superseded_batch:
            self.estimated_recipes += batch.superseded_batch.recipes_total
