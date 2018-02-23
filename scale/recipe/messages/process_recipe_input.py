"""Defines a command message that processes the input for a list of recipes"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from messaging.messages.message import CommandMessage
from recipe.messages.update_recipes import create_update_recipes_messages
from recipe.models import Recipe

# This is the maximum number of recipe models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_process_recipe_input_messages(recipe_ids):
    """Creates messages to process the input for the given recipes

    :param recipe_ids: The recipe IDs
    :type recipe_ids: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for recipe_id in recipe_ids:
        if not message:
            message = ProcessRecipeInput()
        elif not message.can_fit_more():
            messages.append(message)
            message = ProcessRecipeInput()
        message.add_recipe(recipe_id)
    if message:
        messages.append(message)

    return messages


class ProcessRecipeInput(CommandMessage):
    """Command message that processes the input for a list of recipes
    """

    def __init__(self):
        """Constructor
        """

        super(ProcessRecipeInput, self).__init__('process_recipe_input')

        self._recipe_ids = []

    def add_recipe(self, recipe_id):
        """Adds the given recipe ID to this message

        :param recipe_id: The recipe ID
        :type recipe_id: int
        """

        self._recipe_ids.append(recipe_id)

    def can_fit_more(self):
        """Indicates whether more jobs can fit in this message

        :return: True if more jobs can fit, False otherwise
        :rtype: bool
        """

        return len(self._recipe_ids) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'recipe_ids': self._recipe_ids}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = ProcessRecipeInput()
        for recipe_id in json_dict['recipe_ids']:
            message.add_recipe(recipe_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        with transaction.atomic():
            # Retrieve locked recipe models
            recipe_models = Recipe.objects.get_locked_recipes(self._recipe_ids)

            # Process recipe input
            Recipe.objects.process_recipe_input(recipe_models)

        logger.info('Processed recipe inputs for %d recipe(s)', len(self._recipe_ids))
        self.new_messages.extend(create_update_recipes_messages(self._recipe_ids))

        return True
