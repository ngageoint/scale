"""Defines a command message that processes a recipe condition"""
from __future__ import unicode_literals

import json
import logging

from data.data.exceptions import InvalidData
from data.data.json.data_v6 import convert_data_to_v6_json
from messaging.messages.message import CommandMessage
from recipe.models import RecipeCondition, RecipeNode


logger = logging.getLogger(__name__)


def create_process_condition_messages(condition_ids):
    """Creates messages to process the given conditions

    :param condition_ids: The condition IDs
    :type condition_ids: :func:`list`
    :return: The list of messages
    :rtype: :func:`list`
    """

    messages = []

    for condition_id in condition_ids:
        message = ProcessCondition()
        message.condition_id = condition_id
        messages.append(message)

    return messages


class ProcessCondition(CommandMessage):
    """Command message that processes a recipe condition
    """

    def __init__(self):
        """Constructor
        """

        super(ProcessCondition, self).__init__('process_condition')

        self.condition_id = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'condition_id': self.condition_id}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = ProcessCondition()
        message.condition_id = json_dict['condition_id']
        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        condition = RecipeCondition.objects.get_condition_with_interfaces(self.condition_id)

        if not condition.is_processed:
            definition = condition.recipe.recipe_type_rev.get_definition()

            # Get condition data from dependencies in the recipe
            recipe_input_data = condition.recipe.get_input_data()
            node_outputs = RecipeNode.objects.get_recipe_node_outputs(condition.recipe_id)
            for node_output in node_outputs.values():
                if node_output.node_type == 'condition' and node_output.id == condition.id:
                    node_name = node_output.node_name
                    break

            # Set data on the condition model
            try:
                data = definition.generate_node_input_data(node_name, recipe_input_data, node_outputs)
                RecipeCondition.objects.set_condition_data_v6(condition, data, node_name)
            except InvalidData:
                logger.exception('Recipe %d created invalid input data for condition %d. Message will not re-run.',
                                 condition.recipe_id, self.condition_id)
                return True

            # Process filter and set whether condition was accepted
            data_filter = definition.graph[node_name].data_filter
            is_accepted = data_filter.is_data_accepted(data)
            RecipeCondition.objects.set_processed(condition.id, is_accepted)

            # Log results
            filter_str = json.dumps(data_filter.filter_list, sort_keys=True, indent=4, separators=(',', ': '))
            data_str = json.dumps(convert_data_to_v6_json(data).get_dict(), sort_keys=True, indent=4, separators=(',', ': '))
            logger.info('Condition %d (recipe %d at %s) evaluated to %s:\nCondition: %s\nInput Data: %s', condition.id, condition.recipe_id, node_name, is_accepted, filter_str, data_str)
            
        # Create message to update the condition's recipe
        from recipe.messages.update_recipe import create_update_recipe_message
        root_recipe_id = condition.recipe.root_recipe_id if condition.recipe.root_recipe_id else condition.recipe_id
        logger.info('Processed data for condition %d, sending message to update recipe %d', self.condition_id, root_recipe_id)
        self.new_messages.append(create_update_recipe_message(root_recipe_id))

        return True
