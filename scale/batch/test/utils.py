"""Defines utility methods for testing batches"""
from __future__ import unicode_literals

import recipe.test.utils as recipe_test_utils
from batch.configuration.definition.batch_definition import BatchDefinition
from batch.models import Batch

BATCH_TITLE_COUNTER = 1
BATCH_DESCRIPTION_COUNTER = 1


def create_batch(recipe_type=None, definition=None, title=None, description=None, recipe_count=0):
    """Creates a batch model for unit testing

    :returns: The batch model
    :rtype: :class:`batch.models.Batch`
    """

    if not recipe_type:
        recipe_type = recipe_test_utils.create_recipe_type()
    if not definition:
        definition = {}
    if not isinstance(definition, BatchDefinition):
        definition = BatchDefinition(definition)
    if not title:
        global BATCH_TITLE_COUNTER
        title = 'Test Batch Title %i' % BATCH_TITLE_COUNTER
        BATCH_TITLE_COUNTER += 1
    if not description:
        global BATCH_DESCRIPTION_COUNTER
        description = 'Test Batch Description %i' % BATCH_DESCRIPTION_COUNTER
        BATCH_DESCRIPTION_COUNTER += 1

    for i in range(recipe_count):
        recipe_test_utils.create_recipe(recipe_type=recipe_type)

    return Batch.objects.create_batch(recipe_type=recipe_type, definition=definition, title=title,
                                      description=description)
