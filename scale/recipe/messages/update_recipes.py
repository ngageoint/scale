"""Defines a command message that evaluates and updates recipes"""
from __future__ import unicode_literals

import logging

from messaging.messages.message import CommandMessage
from recipe.messages.update_recipe import create_update_recipe_message
from recipe.models import Recipe

# This is the maximum number of recipe models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100

# This is the maximum number of jobs to handle at a time so that the message handler memory is not exceeded.
MAX_JOBS_AT_A_TIME = 1000


logger = logging.getLogger(__name__)


# TODO: This message is deprecated and should no longer be used. Use the update_recipe message instead.
class UpdateRecipes(CommandMessage):
    """Command message that evaluates and updates recipes
    """

    def __init__(self):
        """Constructor
        """

        super(UpdateRecipes, self).__init__('update_recipes')

        self._count = 0
        self._recipe_ids = []

    def add_recipe(self, recipe_id):
        """Adds the given recipe ID to this message

        :param recipe_id: The recipe ID
        :type recipe_id: int
        """

        self._count += 1
        self._recipe_ids.append(recipe_id)

    def can_fit_more(self):
        """Indicates whether more recipes can fit in this message

        :return: True if more recipes can fit, False otherwise
        :rtype: bool
        """

        return self._count < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'recipe_ids': self._recipe_ids}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = UpdateRecipes()
        for recipe_id in json_dict['recipe_ids']:
            message.add_recipe(recipe_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        for recipe in Recipe.objects.filter(id__in=self._recipe_ids):
            root_recipe_id = recipe.root_superseded_recipe_id if recipe.root_superseded_recipe_id else recipe.id
            self.new_messages.append(create_update_recipe_message(root_recipe_id))

        logger.info('Found %d message(s) to update recipes', len(self.new_messages))

        return True
