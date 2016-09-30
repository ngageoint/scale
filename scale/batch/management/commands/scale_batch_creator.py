"""Defines the command line method for creating a Scale batch"""
from __future__ import unicode_literals

import logging
import sys
from optparse import make_option

import django.utils.timezone as timezone
from django.core.management.base import BaseCommand
from django.db.models import F

from batch.models import Batch, BatchJob, BatchRecipe
from recipe.models import Recipe, RecipeJob

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command that creates a Scale batch"""

    option_list = BaseCommand.option_list + (
        make_option('-i', '--batch-id', action='store', type='int', help='The ID of the batch to create'),
    )

    help = 'Creates a new batch of jobs and recipes to be processed on the cluster'

    def __init__(self):
        """Constructor"""
        super(Command, self).__init__()

    def handle(self, **options):
        """See :meth:`django.core.management.base.BaseCommand.handle`.

        This method starts the Scale batch creation process.
        """

        batch_id = options.get('batch_id')

        logger.info('Command starting: scale_batch_creator - Batch ID: %i', batch_id)
        try:
            batch = Batch.objects.get(pk=batch_id)
        except Batch.DoesNotExist:
            logger.exception('Unable to find batch: %i', batch_id)
            sys.exit(1)

        logger.info('Creating batch: %i', batch.id)

        # Schedule all the batch recipes
        self._schedule_recipes(batch)

        logger.info('Command completed: scale_batch_creator')

    def _schedule_recipes(self, batch):
        """Schedules each recipe that matches the batch for re-processing and creates associated batch models.

        :param batch: The batch that defines the recipes to schedule
        :type batch: :class:`batch.models.Batch`

        :raises :class:`batch.exceptions.BatchError`: If general batch parameters are invalid
        """

        # Fetch all the recipes of the requested type that are not already superseded and have actually been changed
        old_recipes = Recipe.objects.filter(recipe_type=batch.recipe_type, is_superseded=False,
                                            recipe_type__revision_num__gt=F('recipe_type_rev__revision_num'))
        total = old_recipes.count()
        logger.info('Scheduling batch recipes: %i', total)

        # Schedule all the new recipes/jobs and create corresponding batch models
        created = 0
        failed = 0
        for old_recipe in old_recipes.iterator():
            try:
                handler = Recipe.objects.reprocess_recipe(old_recipe.id)
                self._handle_recipe(batch, old_recipe, handler.recipe, handler.recipe_jobs)
                created += 1
            except:
                logger.exception('Unable to supersede batch recipe: %i', old_recipe.id)
                failed += 1
        logger.info('Created: %i, Failed: %i', created, failed)

        # Update batch state
        batch.status = 'CREATED'
        batch.save()

    def _handle_recipe(self, batch, old_recipe, new_recipe, new_recipe_jobs):
        """Creates all the batch-specific models to track the new jobs that were queued

        :param batch: The batch that defines the recipes to schedule
        :type batch: :class:`batch.models.Batch`
        :param old_recipe: The old recipe that was superseded
        :type old_recipe: :class:`recipe.models.Recipe`
        :param new_recipe: The new recipe that was just queued
        :type new_recipe: :class:`recipe.models.Recipe`
        :param new_recipe_jobs: The new recipe jobs that were just queued
        :type new_recipe_jobs: [:class:`recipe.models.RecipeJob`]
        """

        # Create a batch recipe for the new recipe
        batch_recipe = BatchRecipe()
        batch_recipe.batch = batch
        batch_recipe.recipe = new_recipe
        batch_recipe.superseded_recipe = old_recipe
        batch_recipe.save()

        # Fetch all the recipe jobs that were superseded
        old_recipe_jobs = RecipeJob.objects.select_related('job').filter(recipe=old_recipe, job__is_superseded=True)
        superseded_jobs = {rj.job_name: rj.job for rj in old_recipe_jobs}

        # Create a batch job for each new recipe job
        batch_jobs = []
        now = timezone.now()
        for new_recipe_job in new_recipe_jobs:
            batch_job = BatchJob()
            batch_job.batch = batch
            batch_job.job = new_recipe_job.job
            batch_job.created = now

            # Associate it to a superseded job when possible
            if new_recipe_job.job_name in superseded_jobs:
                batch_job.superseded_job = superseded_jobs[new_recipe_job.job_name]
            batch_jobs.append(batch_job)
        BatchJob.objects.bulk_create(batch_jobs)
