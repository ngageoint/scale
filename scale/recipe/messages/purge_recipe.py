"""Defines a command message that purges a recipe"""
from __future__ import unicode_literals

import logging

from recipe.models import Recipe, RecipeNode
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime

# This is the maximum number of job models that can fit in one message. This maximum ensures that every message of this
# type is less than 25 KiB long.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_purge_recipe_message(recipe_id, when):
    """Creates messages to remove the given recipe by ID

    :param recipe_id: The recipe ID
    :type purge_job_ids: int
    :param when: The current time
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: :class:`recipe.messages.purge_recipe.PurgeRecipe`
    """

    message = PurgeRecipe()
    message.recipe_id = recipe_id
    message.when = when

    return message


class PurgeRecipe(CommandMessage):
    """Command message that purges recipe components
    """

    def __init__(self):
        """Constructor
        """

        super(PurgeRecipe, self).__init__('purge_recipe')

        self.recipe_id = None
        self.when = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'recipe_id': self.recipe_id, 'when': datetime_to_string(self.when)}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        when = parse_datetime(json_dict['when'])

        message = PurgeRecipe()
        message.recipe_id = json_dict['recipe_ID']
        message.when = when

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        """
        Create a purge_recipe message that takes a single recipe ID:

        - message should retrieve the recipe instance and determine the current, original leaf nodes (is_original == True),
            delete_job_files messages (with purge) for original leaf jobs and send purge_recipe messages for original leaf recipes

        - if there are no original nodes left in the recipe, delete BatchRecipe, RecipeNode (matched on sub_recipe or recipe),
            RecipeInputFile, and Recipe model for this recipe ID

        - if this recipe had a higher-level recipe containing it (had an is_original == True RecipeNode model matched on sub_recipe),
            send a purge_recipe message for the higher-level recipe

        - if the recipe did not have a higher-level recipe (is top-level) but has superseded another recipe, send a purge_recipe message for the superseded recipe

        - Update the purge_jobs message to send a purge_recipe message if the job had an is_original == True RecipeNode model attached to it.
            This way when a job is purged, it will alert its original recipe which can then purge that job's parents.

        RecipeNode = Links a recipe with a node within that recipe. Nodes within a recipe may represent either a job or another
            recipe. The same node may exist in multiple recipes due to superseding. For an original node and recipe combination,
            the is_original flag is True. When recipe B supersedes recipe A, the non-superseded nodes from recipe A that are
            being copied to recipe B will have models with is_original set to False.
        """

        recipe = Recipe.objects.get(id=self.recipe_id)
        original_recipe_nodes = RecipeNode.objects.filter(recipe=recipe, is_original=True)
        
        # Kick off PurgeRecipe for parent recipes
        parent_recipe_nodes = RecipeNode.objects.filter(sub_recipe=recipe, is_original=True)
        if parent_recipe_nodes:
            for parent_recipe in parent_recipe_nodes:
                messages.append(create_purge_recipe_message(parent_recipe.recipe.id))
        
        elif recipe.is_superseeded:



        # Determine if recipe is original
        for recipe_node in recipe_nodes:
            if recipe_node.is_original == True and recipe_node.sub_recipe:
                # Kick off a purge_recipe for sub-recipes
                messages.append(create_purge_recipe_message(recipe_node.recipe.id))

                
            else:
                
            pass
        return True
