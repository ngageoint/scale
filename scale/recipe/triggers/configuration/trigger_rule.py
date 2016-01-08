'''Defines the base configuration class for a trigger rule that triggers recipe creation'''
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod

from job.triggers.configuration.trigger_rule import JobTriggerRuleConfiguration


class RecipeTriggerRuleConfiguration(JobTriggerRuleConfiguration):
    '''The base class that represents trigger rule configurations that can create jobs and/or recipes when triggered
    '''

    __metaclass__ = ABCMeta

    @abstractmethod
    def validate_trigger_for_recipe(self, recipe_definition):
        '''Validates the trigger rule configuration to ensure it correctly connects with the given recipe type
        definition

        :param recipe_definition: The recipe type definition
        :type recipe_definition: :class:`recipe.configuration.definition.recipe_definition.RecipeDefinition`
        :returns: A list of warnings discovered during validation
        :rtype: list[:class:`recipe.configuration.data.recipe_data.ValidationWarning`]

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeConnection`: If the trigger rule connection to
            the recipe type definition is not valid
        '''

        raise NotImplementedError()
