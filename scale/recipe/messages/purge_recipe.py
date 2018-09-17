"""Defines a command message that purges a recipe"""
from __future__ import unicode_literals

import logging

from batch.models import BatchRecipe
from job.messages.spawn_delete_files_job import create_spawn_delete_files_job
from recipe.models import Recipe, RecipeInputFile, RecipeNode
from messaging.messages.message import CommandMessage
from util.parse import datetime_to_string, parse_datetime


logger = logging.getLogger(__name__)


def create_purge_recipe_message(recipe_id, trigger_id, when):
    """Creates messages to remove the given recipe by ID

    :param recipe_id: The recipe ID
    :type purge_job_ids: int
    :param trigger_id: The trigger event id for the purge operation
    :type trigger_id: int
    :param when: The current time
    :type when: :class:`datetime.datetime`
    :return: The list of messages
    :rtype: :class:`recipe.messages.purge_recipe.PurgeRecipe`
    """

    message = PurgeRecipe()
    message.recipe_id = recipe_id
    message.trigger_id = trigger_id
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
        self.trigger_id = None
        self.when = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'recipe_id': self.recipe_id, 'trigger_id': self.trigger_id, 'when': datetime_to_string(self.when)}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        when = parse_datetime(json_dict['when'])

        message = PurgeRecipe()
        message.recipe_id = json_dict['recipe_id']
        message.trigger_id = json_dict['trigger_id']
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
        recipe_nodes = RecipeNode.objects.filter(recipe=recipe)

        for recipe_node in recipe_nodes:
            if recipe_node.is_original == True and recipe_node.sub_recipe:
                # Kick off a purge_recipe for sub-recipes
                self.new_messages.append(create_purge_recipe_message(recipe_id=recipe_node.recipe,
                                                                     trigger_id=self.trigger_id,
                                                                     when=self.when))
            # Kick off a delete files job for the node job
            self.new_messages.append(create_spawn_delete_files_job(job_id=recipe_node.job,
                                                                   trigger_id=self.trigger_id,
                                                                   purge=True))
            # Kick off a purge recipe for the ???
            self.new_messages.append(create_purge_recipe_message(recipe_id=recipe_node.recipe,
                                                                 trigger_id=self.trigger_id,
                                                                 when=self.when))
            pass

        # Delete BatchRecipe, RecipeNode, RecipeInputFile, and Recipe
        BatchRecipe.objects.filter(recipe=recipe).delete()
        RecipeNode.objects.filter(recipe=recipe).delete()
        RecipeInputFile.objects.filter(recipe=recipe).delete()
        recipe.delete()

        parent_recipe_nodes = RecipeNode.objects.filter(sub_recipe=recipe, is_original=True)

        if parent_recipe_nodes:
            for parent_recipe in parent_recipe_nodes:
                # Kick off PurgeRecipe for parent recipes
                messages.append(create_purge_recipe_message(recipe_id=recipe_node.recipe,
                                                            trigger_id=self.trigger_id,
                                                            when=self.when))
        elif recipe.is_superseded:

        return True
