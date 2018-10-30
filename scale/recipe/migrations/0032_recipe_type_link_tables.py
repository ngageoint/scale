# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import operator

from django.db import migrations
from django.db.models import Q

from recipe.definition.json.definition_v6 import RecipeDefinitionV6

def get_recipe_job_type_ids(apps, definition):
    """Gets the model ids of the job types contained in the given RecipeDefinition

    :param definition: RecipeDefinition to search for job types
    :type definition: :class:`recipe.definition.definition.RecipeDefinition`
    :returns: set of JobType ids
    :rtype: set[int]
    """

    JobType = apps.get_model('job', 'JobType')

    types = definition.get_job_type_keys()
    ids = []
    if types:
        query = reduce(
            operator.or_,
            (Q(name=type.name, version=type.version) for type in types)
        )
        ids = JobType.objects.filter(query).values_list('pk', flat=True)

    return ids


def create_recipe_type_job_links(apps, recipe_type_ids, job_type_ids):
    """Creates the appropriate links for the given recipe and job types. All database changes are
    made in an atomic transaction.

    :param recipe_type_ids: List of recipe type IDs
    :type recipe_type_ids: list of int
    :param job_type_ids: List of job type IDs.
    :type job_type_ids: list of int
    """

    RecipeTypeJobLink = apps.get_model('recipe', 'RecipeTypeJobLink')

    if len(recipe_type_ids) != len(job_type_ids):
        raise Exception('Recipe Type and Job Type lists must be equal length!')

    # Delete any previous links for the given recipe
    RecipeTypeJobLink.objects.filter(recipe_type_id__in=recipe_type_ids).delete()

    new_links = []

    for id, job in zip(recipe_type_ids, job_type_ids):
        link = RecipeTypeJobLink(recipe_type_id=id, job_type_id=job)
        new_links.append(link)

    RecipeTypeJobLink.objects.bulk_create(new_links)


def create_recipe_type_job_links_from_definition(apps, recipe_type):
    """Goes through a recipe type definition and gets all the job types it contains and creates the appropriate links

    :param recipe_type: New/updated recipe type
    :type recipe_type: :class:`recipe.models.RecipeType`

    :raises :class:`recipe.models.JobType.DoesNotExist`: If it contains a job type that does not exist
    """

    definition = RecipeDefinitionV6(definition=recipe_type.definition, do_validate=False).get_definition()

    job_type_ids = get_recipe_job_type_ids(apps, definition)

    if len(job_type_ids) > 0:
        recipe_type_ids = [recipe_type.id] * len(job_type_ids)
        create_recipe_type_job_links(apps, recipe_type_ids, job_type_ids)


def create_recipe_type_sub_links(apps, recipe_type_ids, sub_recipe_type_ids):
    """Creates the appropriate links for the given parent and child recipe types. All database changes are
    made in an atomic transaction.

    :param recipe_type_ids: List of parent recipe type IDs
    :type recipe_type_ids: list of int
    :param sub_recipe_type_ids: List of child recipe type IDs.
    :type sub_recipe_type_ids: list of int
    """

    RecipeTypeSubLink = apps.get_model('recipe', 'RecipeTypeSubLink')

    if len(recipe_type_ids) != len(sub_recipe_type_ids):
        raise Exception('Recipe Type and Sub recipe type lists must be equal length!')

    # Delete any previous links for the given recipe
    RecipeTypeSubLink.objects.filter(recipe_type_id__in=recipe_type_ids).delete()

    new_links = []

    for id, sub in zip(recipe_type_ids, sub_recipe_type_ids):
        link = RecipeTypeSubLink(recipe_type_id=id, sub_recipe_type_id=sub)
        new_links.append(link)

    RecipeTypeSubLink.objects.bulk_create(new_links)


def create_recipe_type_sub_links_from_definition(apps, recipe_type):
    """Goes through a recipe type definition, gets all the recipe types it contains and creates the appropriate links

    :param recipe_type: New/updated recipe type
    :type recipe_type: :class:`recipe.models.RecipeType`

    :raises :class:`recipe.models.RecipeType.DoesNotExist`: If it contains a sub recipe type that does not exist
    """

    RecipeType = apps.get_model('recipe', 'RecipeType')

    definition = RecipeDefinitionV6(definition=recipe_type.definition, do_validate=False).get_definition()

    sub_type_names = definition.get_recipe_type_names()

    sub_type_ids = RecipeType.objects.all().filter(name__in=sub_type_names).values_list('pk', flat=True)

    if len(sub_type_ids) > 0:
        recipe_type_ids = [recipe_type.id] * len(sub_type_ids)
        create_recipe_type_sub_links(recipe_type_ids, sub_type_ids)

def populate_recipe_type_link_tables(apps, schema_editor):
    # Go through all of the recipe type models and create links for their sub recipes and job types
    JobType = apps.get_model('job', 'JobType')
    RecipeType = apps.get_model('recipe', 'RecipeType')

    total_count = RecipeType.objects.all().count()
    if not total_count:
        return

    print('\nCreating new recipe link table rows: %i' % total_count)
    recipe_types = RecipeType.objects.all()
    done_count = 0
    fail_count = 0
    for rt in recipe_types:
        try:
            create_recipe_type_job_links_from_definition(apps, rt)
            create_recipe_type_sub_links_from_definition(apps, rt)
        except (JobType.DoesNotExist, RecipeType.DoesNotExist) as ex:
            fail_count += 1
            print ('Failed creating links for recipe type %i: %s' % (rt.id, ex))

        done_count += 1
        percent = (float(done_count) / float(total_count)) * 100.00
        print('Progress: %i/%i (%.2f%%)' % (done_count, total_count, percent))

    print ('Migration finished. Failed: %i' % fail_count)


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0031_auto_20181026_1417'),
    ]

    operations = [
        migrations.RunPython(populate_recipe_type_link_tables),
    ]
