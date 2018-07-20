"""Defines a command message that processes the input for a recipe"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from messaging.messages.message import CommandMessage
from recipe.messages.update_recipes import create_update_recipes_messages
from recipe.models import Recipe, RecipeNode


logger = logging.getLogger(__name__)


def create_process_recipe_input_messages(recipe_ids):
    """Creates messages to process the input for the given recipes

    :param recipe_ids: The recipe IDs
    :type recipe_ids: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    for recipe_id in recipe_ids:
        message = ProcessRecipeInput()
        message.recipe_id = recipe_id
        messages.append(message)

    return messages


class ProcessRecipeInput(CommandMessage):
    """Command message that processes the input for a recipes
    """

    def __init__(self):
        """Constructor
        """

        super(ProcessRecipeInput, self).__init__('process_recipe_input')

        self.recipe_id = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'recipe_id': self.recipe_id}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = ProcessRecipeInput()
        message.recipe_id = json_dict['recipe_id']
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        with transaction.atomic():
            # Retrieve locked recipe models
            recipe_models = Recipe.objects.get_locked_recipes(self._recipe_ids)

            # Process recipe input
            Recipe.objects.process_recipe_input(recipe_models)

        # TODO: create message to update recipe
        logger.info('Processed recipe inputs for %d recipe(s)', len(self._recipe_ids))
        self.new_messages.extend(create_update_recipes_messages(self._recipe_ids))

        return True

    def _generate_input_data_from_recipe(self, sub_recipe):
        """Generates the sub-recipe's input data from its recipe dependencies and validates and sets the input data on
        the sub-recipe

        :param sub_recipe: The sub-recipe with related recipe_type_rev and recipe__recipe_type_rev models
        :type sub_recipe: :class:`recipe.models.Recipe`

        :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
        """

        # TODO: this is a hack to work with old legacy recipe data with workspaces, remove when legacy job types go
        old_recipe_input_dict = dict(sub_recipe.recipe.input)

        # Get sub-recipe input from dependencies in the recipe
        recipe_input_data = sub_recipe.recipe.get_input_data()
        node_outputs = RecipeNode.objects.get_recipe_node_outputs(sub_recipe.recipe_id)
        for node_output in node_outputs.values():
            if node_output.node_type == 'recipe' and node_output.id == sub_recipe.id:
                node_name = node_output.node_name
                break

        # TODO: this is a hack to work with old legacy recipe data with workspaces, remove when legacy job types go
        sub_recipe.recipe.input = old_recipe_input_dict

        definition = sub_recipe.recipe.recipe_type_rev.get_definition()
        input_data = definition.generate_node_input_data(node_name, recipe_input_data, node_outputs)
        Job.objects.set_job_input_data_v6(job, input_data)
