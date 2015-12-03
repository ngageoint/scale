'''Defines utility methods for testing jobs and job types'''
from __future__ import unicode_literals

import job.test.utils as job_utils
import trigger.test.utils as trigger_utils
from recipe.models import Recipe, RecipeJob, RecipeType, RecipeTypeRevision

NAME_COUNTER = 1
VERSION_COUNTER = 1
TITLE_COUNTER = 1
DESCRIPTION_COUNTER = 1


def create_recipe_type(name=None, version=None, title=None, description=None, definition=None):
    '''Creates a recipe type for unit testing

    :returns: The RecipeType model
    :rtype: :class:`recipe.models.RecipeType`
    '''

    if not name:
        global NAME_COUNTER
        name = 'test-recipe-type-%i' % NAME_COUNTER
        NAME_COUNTER = NAME_COUNTER + 1

    if not version:
        global VERSION_COUNTER
        version = '%i.0.0' % VERSION_COUNTER
        VERSION_COUNTER = VERSION_COUNTER + 1

    if not title:
        global TITLE_COUNTER
        title = 'Test Recipe Type %i' % TITLE_COUNTER
        TITLE_COUNTER = TITLE_COUNTER + 1

    if not description:
        global DESCRIPTION_COUNTER
        description = 'Test Description %i' % DESCRIPTION_COUNTER
        DESCRIPTION_COUNTER = DESCRIPTION_COUNTER + 1

    if not definition:
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [],
        }

    recipe_type = RecipeType()
    recipe_type.name = name
    recipe_type.version = version
    recipe_type.title = title
    recipe_type.description = description
    recipe_type.definition = definition
    recipe_type.save()

    RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)

    return recipe_type


def create_recipe(recipe_type=None, data=None, event=None):
    '''Creates a job type model for unit testing

    :param recipe_type: The associated recipe type
    :type recipe_type: :class:'recipe.models.RecipeType'
    :param data: The associated data for the recipe
    :type data: dict
    :param event: The associated event
    :type event: :class:'trigger.models.TriggerEvent'
    :returns: The recipe model
    :rtype: :class:`recipe.models.Recipe`
    '''

    if not data:
        data = {}

    if not recipe_type:
        recipe_type = create_recipe_type()

    if not event:
        event = trigger_utils.create_trigger_event()

    recipe = Recipe()
    recipe.recipe_type = recipe_type
    recipe.recipe_type_rev = RecipeTypeRevision.objects.get_latest_revision(recipe_type.id)
    recipe.event = event
    recipe.data = data
    recipe.save()

    return recipe


def create_recipe_job(recipe=None, job_name=None, job=None):
    '''Creates a job type model for unit testing

    :param recipe: The associated recipe
    :type recipe: :class:'recipe.models.Recipe'
    :param job_name: The associated name for the recipe job
    :type data: string
    :param job: The associated job
    :type job: :class:'job.models.Job'
    :returns: The recipe job model
    :rtype: :class:`recipe.models.RecipeJob`
    '''
    if not recipe:
        recipe = create_recipe()

    if not job_name:
        job_name = 'Test Job Name'

    if not job:
        job = job_utils.create_job()

    recipe_job = RecipeJob()
    recipe_job.job_name = job_name
    recipe_job.job = job
    recipe_job.recipe = recipe
    recipe_job.save()
    return recipe_job
