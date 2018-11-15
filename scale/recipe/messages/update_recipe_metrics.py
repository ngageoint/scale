"""Defines a command message that updates recipe metrics"""
from __future__ import unicode_literals

import logging

from messaging.messages.message import CommandMessage
from recipe.models import Recipe

# This is the maximum number of recipe models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100


logger = logging.getLogger(__name__)


def create_update_recipe_metrics_messages(recipe_ids):
    """Creates messages to update the metrics for the given recipes

    :param recipe_ids: The recipe IDs
    :type recipe_ids: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for recipe_id in recipe_ids:
        if not message:
            message = UpdateRecipeMetrics()
        elif not message.can_fit_more():
            messages.append(message)
            message = UpdateRecipeMetrics()
        message.add_recipe(recipe_id)
    if message:
        messages.append(message)

    return messages


def create_update_recipe_metrics_messages_from_jobs(job_ids):
    """Creates messages to update the metrics for the recipes affected by the given jobs

    :param job_ids: The job IDs
    :type job_ids: list
    :return: The list of messages
    :rtype: list
    """

    recipe_ids = Recipe.objects.get_recipe_ids_for_jobs(job_ids)
    return create_update_recipe_metrics_messages(recipe_ids)


def create_update_recipe_metrics_messages_from_sub_recipes(sub_recipe_ids):
    """Creates messages to update the metrics for the recipes affected by the given sub-recipes

    :param sub_recipe_ids: The sub-recipe IDs
    :type sub_recipe_ids: list
    :return: The list of messages
    :rtype: list
    """

    recipe_ids = Recipe.objects.get_recipe_ids_for_sub_recipes(sub_recipe_ids)
    return create_update_recipe_metrics_messages(recipe_ids)


class UpdateRecipeMetrics(CommandMessage):
    """Command message that updates recipe metrics
    """

    def __init__(self):
        """Constructor
        """

        super(UpdateRecipeMetrics, self).__init__('update_recipe_metrics')

        self._recipe_ids = []

    def add_recipe(self, recipe_id):
        """Adds the given recipe ID to this message

        :param recipe_id: The recipe ID
        :type recipe_id: int
        """

        self._recipe_ids.append(recipe_id)

    def can_fit_more(self):
        """Indicates whether more recipes can fit in this message

        :return: True if more recipes can fit, False otherwise
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

        message = UpdateRecipeMetrics()
        for recipe_id in json_dict['recipe_ids']:
            message.add_recipe(recipe_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        Recipe.objects.update_recipe_metrics(self._recipe_ids)

        # If any of these recipes are sub-recipes, update the metrics of the recipes that contain these
        self.new_messages.extend(create_update_recipe_metrics_messages_from_sub_recipes(self._recipe_ids))

        # If any of these recipes are sub-recipes, grab root recipe IDs and update those recipes
        root_recipe_ids = set()
        for recipe in Recipe.objects.filter(id__in=self._recipe_ids):
            if recipe.root_recipe_id:
                root_recipe_ids.add(recipe.root_recipe_id)
        if root_recipe_ids:
            from recipe.messages.update_recipe import create_update_recipe_messages_from_node
            self.new_messages.extend(create_update_recipe_messages_from_node(root_recipe_ids))

        # For any top-level recipes (not a sub-recipe) update any batches that these recipes belong to
        from batch.messages.update_batch_metrics import create_update_batch_metrics_messages
        batch_ids = set()
        qry = Recipe.objects.filter(id__in=self._recipe_ids, recipe__isnull=True, batch__isnull=False).only('batch_id')
        for recipe in qry:
            batch_ids.add(recipe.batch_id)
        if batch_ids:
            self.new_messages.extend(create_update_batch_metrics_messages(batch_ids))

        return True
