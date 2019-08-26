"""Defines the class for managing a batch definition"""
from __future__ import unicode_literals

from batch.definition.exceptions import InvalidDefinition
from recipe.diff.diff import RecipeDiff


class BatchDefinition(object):
    """Represents a batch definition"""

    def __init__(self):
        """Constructor
        """
        self.dataset = None
        self.supersedes = True
        self.root_batch_id = None
        self.forced_nodes = None

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

        # Re-processing a previous batch
        if self.root_batch_id:
            if batch.recipe_type_id != batch.superseded_batch.recipe_type_id:
                raise InvalidDefinition('MISMATCHED_RECIPE_TYPE',
                                        'New batch and previous batch must have the same recipe type')
            if not batch.superseded_batch.is_creation_done:
                raise InvalidDefinition('PREV_BATCH_STILL_CREATING',
                                        'Previous batch must have completed creating all of its recipes')

            # Generate recipe diff against the previous batch
            recipe_def = batch.recipe_type_rev.get_definition()
            prev_recipe_def = batch.superseded_batch.recipe_type_rev.get_definition()
            self.prev_batch_diff = RecipeDiff(prev_recipe_def, recipe_def)
            if self.forced_nodes:
                self.prev_batch_diff.set_force_reprocess(self.forced_nodes)
            if not self.prev_batch_diff.can_be_reprocessed:
                raise InvalidDefinition('PREV_BATCH_NO_REPROCESS', 'Previous batch cannot be reprocessed')
        
        # New batch - need to validate dataset parameters against recipe revision
        elif self.dataset:
            from data.interface.exceptions import InvalidInterfaceConnection
            from data.models import DataSet
            from recipe.models import RecipeTypeRevision
            
            dataset_definition = DataSet.objects.get(pk=self.dataset).get_definition()
            recipe_type_rev = RecipeTypeRevision.objects.get_revision(name=batch.recipe_type.name, revision_num=batch.recipe_type_rev.revision_num).recipe_type

            # combine the parameters
            dataset_parameters = dataset_definition.global_parameters
            for param in dataset_definition.parameters.parameters:
                dataset_parameters.add_parameter(dataset_definition.parameters.parameters[param])

            try:
                recipe_type_rev.get_definition().input_interface.validate_connection(dataset_parameters)
            except InvalidInterfaceConnection as ex:
                raise InvalidDefinition('NO_MATCHING_PARAMS', 'No parameters in the dataset match the recipe type inputs')
                
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
        
        from batch.models import Batch
        self.estimated_recipes = 0
        self.estimated_recipes += Batch.objects.calculate_estimated_recipes(batch, self)

