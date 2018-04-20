"""Defines a command message that creates batch recipes"""
from __future__ import unicode_literals

import logging

from django.utils.timezone import now

from batch.models import Batch
from messaging.messages.message import CommandMessage
from recipe.messages.reprocess_recipes import create_reprocess_recipes_messages
from recipe.models import Recipe

# How many recipes to handle in a single execution of this message
MAX_RECIPE_NUM = 1000


logger = logging.getLogger(__name__)


def create_batch_recipes_message(batch_id):
    """Creates a message to create the recipes for the given batch

    :param batch_id: The batch ID
    :type batch_id: int
    :return: The message
    :rtype: :class:`batch.messages.create_batch_recipes.CreateBatchRecipes`
    """

    message = CreateBatchRecipes()
    message.batch_id = batch_id

    return message


class CreateBatchRecipes(CommandMessage):
    """Command message that creates batch recipes
    """

    def __init__(self):
        """Constructor
        """

        super(CreateBatchRecipes, self).__init__('create_batch_recipes')

        self.batch_id = None
        self.is_prev_batch_done = False  # Indicates if all recipes from pervious batch have been handled
        self.current_recipe_id = None  # Keeps track of the last recipe that was reprocessed

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'batch_id': self.batch_id, 'is_prev_batch_done': self.is_prev_batch_done}
        if self.current_recipe_id is not None:
            json_dict['current_recipe_id'] = self.current_recipe_id

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CreateBatchRecipes()
        message.batch_id = json_dict['batch_id']
        message.is_prev_batch_done = json_dict['is_prev_batch_done']
        if 'current_recipe_id' in json_dict:
            message.current_recipe_id = json_dict['current_recipe_id']

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        batch = Batch.objects.get(id=self.batch_id)
        definition = batch.get_definition()
        new_messages = []

        # Reprocess recipes from previous batch
        if not self.is_prev_batch_done:
            new_messages.extend(self._handle_previous_batch(batch, definition))

        if self.is_prev_batch_done:
            logger.info('All re-processing messages created, marking recipe creation as done')
            Batch.objects.mark_creation_done(self.batch_id, now())
        else:
            logger.info('Creating new message for next set of batch recipes')
            msg = CreateBatchRecipes.from_json(self.to_json())
            self.new_messages.append(msg)

        self.new_messages.extend(new_messages)
        return True

    def _handle_previous_batch(self, batch, definition):
        """Handles re-processing all recipes in the previous batch, returning any messages needed for the re-processing

        :param batch: The batch
        :type batch: :class:`batch.models.Batch`
        :param definition: The batch definition
        :type definition: :class:`batch.definition.definition.BatchDefinition`
        :return: The messages needed for the re-processing
        :rtype: list
        """

        messages = []
        if definition.root_batch_id is None:
            self.is_prev_batch_done = True
            return messages

        recipe_qry = Recipe.objects.filter(batch_id=batch.superseded_batch_id)
        if self.current_recipe_id:
            recipe_qry = recipe_qry.filter(id__lt=self.current_recipe_id)
        recipe_qry = recipe_qry.order_by('-id')

        root_recipe_ids = []
        last_recipe_id = None
        for recipe in recipe_qry.defer('input')[:MAX_RECIPE_NUM]:
            last_recipe_id = recipe.id
            if recipe.root_superseded_recipe_id is not None:
                root_recipe_ids.append(recipe.root_superseded_recipe_id)
            else:
                root_recipe_ids.append(recipe.id)
        recipe_count = len(root_recipe_ids)

        self.current_recipe_id = last_recipe_id
        if recipe_count > 0:
            logger.info('Found %d recipe(s) from previous batch to reprocess, creating messages', recipe_count)
            msgs = create_reprocess_recipes_messages(root_recipe_ids, batch.recipe_type_rev_id, batch.event_id,
                                                     all_jobs=definition.all_jobs, job_names=definition.job_names,
                                                     batch_id=batch.id)
            messages.extend(msgs)

        if recipe_count < MAX_RECIPE_NUM:
            # Handled less than the max number of recipes, so recipes from previous batch must be done
            self.is_prev_batch_done = True

        return messages
