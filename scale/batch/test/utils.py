"""Defines utility methods for testing batches"""
from __future__ import unicode_literals

from batch.definition.definition import BatchDefinition
from batch.definition.json.old.batch_definition import BatchDefinition as OldBatchDefinition
from batch.models import Batch, BatchJob, BatchRecipe
from job.test import utils as job_test_utils
from recipe.test import utils as recipe_test_utils

BATCH_TITLE_COUNTER = 1
BATCH_DESCRIPTION_COUNTER = 1


def create_batch(title=None, description=None, recipe_type=None, definition=None):
    """Creates a batch model for unit testing

    :returns: The batch model
    :rtype: :class:`batch.models.Batch`
    """

    if not recipe_type:
        recipe_type = recipe_test_utils.create_recipe_type()
    if not definition:
        definition = BatchDefinition()
    if not title:
        global BATCH_TITLE_COUNTER
        title = 'Test Batch Title %i' % BATCH_TITLE_COUNTER
        BATCH_TITLE_COUNTER += 1
    if not description:
        global BATCH_DESCRIPTION_COUNTER
        description = 'Test Batch Description %i' % BATCH_DESCRIPTION_COUNTER
        BATCH_DESCRIPTION_COUNTER += 1

    batch = Batch.objects.create_batch(recipe_type=recipe_type, definition=definition, title=title,
                                       description=description)
    return batch


# TODO: remove this when v5 batch creation is removed
def create_batch_old(recipe_type=None, definition=None, title=None, description=None, status=None, recipe_count=0):
    """Creates a batch model for unit testing

    :returns: The batch model
    :rtype: :class:`batch.models.Batch`
    """

    if not recipe_type:
        recipe_type = recipe_test_utils.create_recipe_type()
    if not definition:
        definition = {}
    if not isinstance(definition, OldBatchDefinition):
        definition = OldBatchDefinition(definition)
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

    batch = Batch.objects.create_batch_old(recipe_type=recipe_type, definition=definition, title=title,
                                           description=description)
    if status:
        batch.status = status
        batch.save()
    return batch

def create_batch_job(batch=None, job=None, superseded_job=None):
    """Creates a BatchJob model for unit testing

    :returns: The BatchJob model
    :rtype: :class:`batch.models.BatchJob`
    """

    if not batch:
        batch = create_batch()
    if not job:
        job = job_test_utils.create_job()
    if not superseded_job:
        superseded_job = job_test_utils.create_job()

    batch_job = BatchJob.objects.create(batch=batch, job=job, superseded_job=superseded_job)

    return batch_job

def create_batch_recipe(batch=None, recipe=None, superseded_recipe=None):
    """Creates a BatchRecipe model for unit testing

    :returns: The BatchRecipe model
    :rtype: :class:`batch.models.BatchRecipe`
    """

    if not batch:
        batch = create_batch()
    if not recipe:
        recipe = recipe_test_utils.create_recipe()
    if not superseded_recipe:
        superseded_recipe = recipe_test_utils.create_recipe()

    batch_recipe = BatchRecipe.objects.create(batch=batch, recipe=recipe, superseded_recipe=superseded_recipe)

    return batch_recipe
