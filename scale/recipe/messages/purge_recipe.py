"""Defines a command message that purges a recipe"""
from __future__ import unicode_literals

import logging

from django.db.models import F, Q

from batch.models import BatchRecipe
from job.messages.spawn_delete_files_job import create_spawn_delete_files_job
from messaging.messages.message import CommandMessage
from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition
from recipe.models import Recipe, RecipeInputFile, RecipeNode
from source.messages.purge_source_file import create_purge_source_file_message
from storage.models import PurgeResults


logger = logging.getLogger(__name__)


def create_purge_recipe_message(recipe_id, trigger_id, source_file_id):
    """Creates messages to remove the given recipe by ID

    :param recipe_id: The recipe ID
    :type purge_job_ids: int
    :param trigger_id: The trigger event ID for the purge operation
    :type trigger_id: int
    :param source_file_id: The source file id for the original file being purged
    :type source_file_id: int
    :return: The purge recipe message
    :rtype: :class:`recipe.messages.purge_recipe.PurgeRecipe`
    """

    message = PurgeRecipe()
    message.recipe_id = recipe_id
    message.trigger_id = trigger_id
    message.source_file_id = source_file_id

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
        self.source_file_id = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'recipe_id': self.recipe_id, 'trigger_id': self.trigger_id, 'source_file_id': self.source_file_id}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = PurgeRecipe()
        message.recipe_id = json_dict['recipe_id']
        message.trigger_id = json_dict['trigger_id']
        message.source_file_id = json_dict['source_file_id']

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        recipe = Recipe.objects.select_related('superseded_recipe').get(id=self.recipe_id)

        # Kick off purge_source_file for the source file
        self.new_messages.append(create_purge_source_file_message(source_file_id=self.source_file_id,
                                                                  trigger_id=self.trigger_id))

        recipe_inst = Recipe.objects.get_recipe_instance(self.recipe_id)
        recipe_nodes = recipe_inst.get_original_leaf_nodes()  # {Node_Name: Node}
        parent_recipes = RecipeNode.objects.filter(sub_recipe=recipe, is_original=True)

        if recipe_nodes:
            # Kick off a delete_files job for leaf node jobs
            leaf_jobs = [node for node in recipe_nodes.values() if node.node_type == JobNodeDefinition.NODE_TYPE]
            for node in leaf_jobs:
                self.new_messages.append(create_spawn_delete_files_job(job_id=node.job.id,
                                                                       trigger_id=self.trigger_id,
                                                                       source_file_id=self.source_file_id,
                                                                       purge=True))

            # Kick off a purge_recipe for leaf node recipes
            leaf_recipes = [node for node in recipe_nodes.values() if node.node_type == RecipeNodeDefinition.NODE_TYPE]
            for node in leaf_recipes:
                self.new_messages.append(create_purge_recipe_message(recipe_id=node.recipe.id,
                                                                     trigger_id=self.trigger_id,
                                                                     source_file_id=self.source_file_id))
        else:
            # Kick off a purge_recipe for a parent recipe
            if parent_recipes:
                for parent_recipe in parent_recipes:
                    self.new_messages.append(create_purge_recipe_message(recipe_id=parent_recipe.recipe.id,
                                                                         trigger_id=self.trigger_id,
                                                                         source_file_id=self.source_file_id))
                    RecipeNode.objects.filter(sub_recipe=recipe).delete()

            # Kick off purge_recipe for a superseded recipe
            elif recipe.superseded_recipe:
                self.new_messages.append(create_purge_recipe_message(recipe_id=recipe.superseded_recipe.id,
                                                                     trigger_id=self.trigger_id,
                                                                     source_file_id=self.source_file_id))

            # Delete BatchRecipe, RecipeNode, RecipeInputFile, and Recipe
            BatchRecipe.objects.filter(recipe=recipe).delete()
            RecipeNode.objects.filter(Q(recipe=recipe) | Q(sub_recipe=recipe)).delete()
            RecipeInputFile.objects.filter(recipe=recipe).delete()
            recipe.delete()
            PurgeResults.objects.filter(source_file_id=self.source_file_id).update(
                num_recipes_deleted=F('num_recipes_deleted') + 1)

        return True
