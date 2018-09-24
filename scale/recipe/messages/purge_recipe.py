"""Defines a command message that purges a recipe"""
from __future__ import unicode_literals

import logging

from batch.models import BatchRecipe
from job.messages.spawn_delete_files_job import create_spawn_delete_files_job
from recipe.models import Recipe, RecipeInputFile, RecipeNode
from messaging.messages.message import CommandMessage


logger = logging.getLogger(__name__)


def create_purge_recipe_message(recipe_id, trigger_id):
    """Creates messages to remove the given recipe by ID

    :param recipe_id: The recipe ID
    :type purge_job_ids: int
    :param trigger_id: The trigger event ID for the purge operation
    :type trigger_id: int
    :return: The purge recipe message
    :rtype: :class:`recipe.messages.purge_recipe.PurgeRecipe`
    """

    message = PurgeRecipe()
    message.recipe_id = recipe_id
    message.trigger_id = trigger_id

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

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'recipe_id': self.recipe_id, 'trigger_id': self.trigger_id}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = PurgeRecipe()
        message.recipe_id = json_dict['recipe_id']
        message.trigger_id = json_dict['trigger_id']

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        recipe = Recipe.objects.select_related('superseded_recipe').get(id=self.recipe_id)
        recipe_inst = Recipe.objects.get_recipe_instance(self.recipe_id)
        recipe_nodes = recipe_inst.get_original_leaf_nodes()  # {'jobs': [j.id, j.id, ..], 'recipes': [r.id, r.id, ..]}
        parent_recipes = RecipeNode.objects.filter(sub_recipe=recipe, is_original=True)

        # Kick off a delete files job node jobs
        for job_id in recipe_nodes['jobs']:
            self.new_messages.append(create_spawn_delete_files_job(job_id=job_id,
                                                                   trigger_id=self.trigger_id,
                                                                   purge=True))

        # Kick off a purge_recipe for node recipes (sub-recipes)
        for recipe_id in recipe_nodes['recipes']:
            self.new_messages.append(create_purge_recipe_message(recipe_id=recipe_id,
                                                                 trigger_id=self.trigger_id))

        # Kick off a purge_recipe for a parent recipe
        if parent_recipes:
            for parent_recipe in parent_recipes:
                self.new_messages.append(create_purge_recipe_message(recipe_id=parent_recipe.recipe.id,
                                                                     trigger_id=self.trigger_id))
                RecipeNode.objects.filter(sub_recipe=recipe).delete()

        # Kick off purge_recipe for a superseded recipe
        elif recipe.superseded_recipe:
            self.new_messages.append(create_purge_recipe_message(recipe_id=recipe.superseded_recipe.id,
                                                                 trigger_id=self.trigger_id))

        # Delete BatchRecipe, RecipeNode, RecipeInputFile, and Recipe
        BatchRecipe.objects.filter(recipe=recipe).delete()
        RecipeNode.objects.filter(recipe=recipe).delete()
        RecipeInputFile.objects.filter(recipe=recipe).delete()
        recipe.delete()

        return True
