'''Defines the functions used to export configuration'''
from __future__ import unicode_literals

import logging

from django.db.models import Q

import port.serializers as serializers
from error.models import Error
from job.models import JobType
from port.schema import Configuration
from recipe.models import RecipeType

logger = logging.getLogger(__name__)


def get_recipe_types(recipe_type_ids=None, recipe_type_names=None):
    '''Exports all the recipe types in the system based on the given filters.

    :param recipe_type_ids: A list of unique recipe type identifiers to include.
    :type recipe_type_ids: list[str]
    :param recipe_type_names: A list of recipe type system names to include.
    :type recipe_type_names: list[str]
    :returns: A list of matching recipe types.
    :rtype: list[:class:`recipe.models.RecipeType`]
    '''
    recipe_types = RecipeType.objects.all().select_related('trigger_rule')

    if recipe_type_ids:
        recipe_types = recipe_types.filter(id__in=recipe_type_ids)
    if recipe_type_names:
        recipe_types = recipe_types.filter(name__in=recipe_type_names)

    return recipe_types


def get_job_types(recipe_types=None, job_type_ids=None, job_type_names=None, job_type_categories=None):
    '''Exports all the job types in the system based on the given filters.

    :param recipe_types: Only include job types that are referenced by the given recipe types.
    :type recipe_types: list[:class:`recipe.models.RecipeType`]
    :param job_type_ids: A list of unique job type identifiers to include.
    :type job_type_ids: list[str]
    :param job_type_names: A list of job type system names to include.
    :type job_type_names: list[str]
    :param job_type_categories: A list of job type category names to include.
    :type job_type_categories: list[str]
    :returns: A list of matching job types.
    :rtype: list[:class:`job.models.JobType`]
    '''

    # Build a set of job type keys referenced by the recipe types
    job_type_keys = set()
    if recipe_types and not (job_type_ids or job_type_names or job_type_categories):
        for recipe_type in recipe_types:
            job_type_keys.update(recipe_type.get_recipe_definition().get_job_type_keys())
        if not job_type_keys:
            return []

    # System job types should never be exported
    job_types = JobType.objects.exclude(category='system').select_related('trigger_rule')

    # Filter by the referenced job type keys
    job_type_filters = []
    for job_type_key in job_type_keys:
        job_type_filter = Q(name=job_type_key[0], version=job_type_key[1])
        job_type_filters = job_type_filters | job_type_filter if job_type_filters else job_type_filter
    if job_type_filters:
        job_types = job_types.filter(job_type_filters)

    # Filter by additional passed arguments
    if job_type_ids:
        job_types = job_types.filter(id__in=job_type_ids)
    if job_type_names:
        job_types = job_types.filter(name__in=job_type_names)
    if job_type_categories:
        job_types = job_types.filter(category__in=job_type_categories)

    return job_types


def get_errors(job_types=None, error_ids=None, error_names=None):
    '''Exports all the errors in the system based on the given filters.

    :param job_types: Only include errors that are referenced by the given job types.
    :type job_types: list[:class:`job.models.JobType`]
    :param error_ids: A list of unique error identifiers to include.
    :type error_ids: list[str]
    :param error_names: A list of error system names to include.
    :type error_names: list[str]
    :returns: A list of matching errors.
    :rtype: list[:class:`error.models.Error`]
    '''

    # Build a set of error names referenced by the job types
    error_names = set(error_names) if error_names else set()
    if job_types and not (error_ids or error_names):
        for job_type in job_types:
            error_names.update(job_type.get_error_interface().get_error_names())
        if not error_names:
            return []

    # System errors should never be exported
    errors = Error.objects.exclude(category='SYSTEM')

    # Filter by additional passed arguments
    if error_ids:
        errors = errors.filter(id__in=error_ids)
    if error_names:
        errors = errors.filter(name__in=error_names)

    return errors


def export_config(recipe_types=None, job_types=None, errors=None):
    recipe_types = recipe_types or []
    job_types = job_types or []
    errors = errors or []

    export_config = {
        'version': '1.0',
        'recipe_types': [serializers.ConfigurationRecipeTypeSerializer(r).data for r in recipe_types],
        'job_types': [serializers.ConfigurationJobTypeSerializer(j).data for j in job_types],
        'errors': [serializers.ConfigurationErrorSerializer(e).data for e in errors],
    }
    return Configuration(export_config)
