"""Defines a command message that processes the input for a recipe"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from data.data.exceptions import InvalidData
from messaging.messages.message import CommandMessage
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6, ForcedNodesV6
from recipe.models import Recipe, RecipeNode


logger = logging.getLogger(__name__)


def create_process_recipe_input_messages(recipe_ids, forced_nodes=None):
    """Creates messages to process the input for the given recipes

    :param recipe_ids: The recipe IDs
    :type recipe_ids: list
    :param forced_nodes: Describes the nodes that have been forced to reprocess
    :type forced_nodes: :class:`recipe.diff.forced_nodes.ForcedNodes`
    :return: The list of messages
    :rtype: list
    """

    messages = []

    for recipe_id in recipe_ids:
        message = ProcessRecipeInput()
        message.recipe_id = recipe_id
        message.forced_nodes = forced_nodes
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
        self.forced_nodes = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'recipe_id': self.recipe_id}

        if self.forced_nodes:
            json_dict['forced_nodes'] = convert_forced_nodes_to_v6(self.forced_nodes).get_dict()

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = ProcessRecipeInput()
        message.recipe_id = json_dict['recipe_id']
        if 'forced_nodes' in json_dict:
            message.forced_nodes = ForcedNodesV6(json_dict['forced_nodes']).get_forced_nodes()

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        recipe = Recipe.objects.get_recipe_with_interfaces(self.recipe_id)

        if not recipe.has_input():
            if not recipe.recipe:
                logger.error('Recipe %d has no input and is not in a recipe. Message will not re-run.', self.recipe_id)
                return True

            try:
                self._generate_input_data_from_recipe(recipe)
            except InvalidData:
                msg = 'Recipe created invalid input data for sub-recipe %d. Message will not re-run.'
                logger.exception(msg, self.recipe_id)
                return True

        # Lock recipe model and process recipe's input data
        with transaction.atomic():
            recipe = Recipe.objects.get_locked_recipe(self.recipe_id)
            root_recipe_id = recipe.root_superseded_recipe_id if recipe.root_superseded_recipe_id else recipe.id
            Recipe.objects.process_recipe_input(recipe)

        # Create message to update the recipe
        from recipe.messages.update_recipe import create_update_recipe_message
        logger.info('Processed input for recipe %d, sending message to update recipe', self.recipe_id)
        self.new_messages.append(create_update_recipe_message(root_recipe_id, forced_nodes=self.forced_nodes))

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
        Recipe.objects.set_recipe_input_data_v6(sub_recipe, input_data)
