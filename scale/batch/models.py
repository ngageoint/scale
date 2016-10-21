"""Defines the database models for a batch"""
from __future__ import unicode_literals

import logging

import django.utils.timezone as timezone
import djorm_pgjson.fields
from django.db import models, transaction
from django.db.models import F

from batch.configuration.definition.batch_definition import BatchDefinition
from batch.exceptions import BatchError
from job.configuration.data.job_data import JobData
from job.models import JobType
from queue.models import Queue
from recipe.models import Recipe, RecipeJob
from trigger.models import TriggerEvent

logger = logging.getLogger(__name__)


class BatchManager(models.Manager):
    """Provides additional methods for handling batches"""

    @transaction.atomic
    def create_batch(self, recipe_type, definition, title=None, description=None):
        """Creates a new batch that represents a group of recipes that should be scheduled for re-processing. This
        method also queues a new system job that will process the batch request. All database changes occur in an atomic
        transaction.

        :param recipe_type: The type of recipes that should be re-processed
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param definition: The definition for running a batch
        :type definition: :class:`batch.configuration.definition.batch_definition.BatchDefinition`
        :param title: The human-readable name of the batch
        :type title: string
        :param description: An optional description of the batch
        :type description: string
        :returns: The newly created batch
        :rtype: :class:`batch.models.Batch`

        :raises :class:`batch.exceptions.BatchError`: If general batch parameters are invalid
        """

        # Attempt to get the batch job type
        try:
            job_type = JobType.objects.filter(name='scale-batch-creator').last()
        except JobType.DoesNotExist:
            raise BatchError('Missing required job type: scale-batch-creator')

        # Create an event to represent this request
        trigger_desc = {'user': 'Anonymous'}
        event = TriggerEvent.objects.create_trigger_event('USER', None, trigger_desc, timezone.now())

        batch = Batch()
        batch.title = title
        batch.description = description
        batch.recipe_type = recipe_type
        batch.definition = definition.get_dict()
        batch.event = event
        batch.save()

        # Setup the job data to process the batch
        data = JobData()
        data.add_property_input('Batch ID', str(batch.id))

        # Schedule the batch job
        job = Queue.objects.queue_new_job(job_type, data, event)
        batch.creator_job = job
        batch.save()

        return batch

    def get_batches(self, started=None, ended=None, statuses=None, recipe_type_ids=None, recipe_type_names=None,
                    order=None):
        """Returns a list of batches within the given time range.

        :param started: Query batches updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query batches updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param statuses: Query batches with the a specific execution status.
        :type statuses: [string]
        :param recipe_type_ids: Query batches for the recipe type associated with the identifier.
        :type recipe_type_ids: [int]
        :param recipe_type_names: Query batches for the recipe type associated with the name.
        :type recipe_type_names: [string]
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of batches that match the time range.
        :rtype: [:class:`batch.models.Batch`]
        """

        # Fetch a list of batches
        batches = Batch.objects.all().select_related('creator_job', 'event', 'recipe_type')
        batches = batches.defer('definition')

        # Apply time range filtering
        if started:
            batches = batches.filter(last_modified__gte=started)
        if ended:
            batches = batches.filter(last_modified__lte=ended)

        # Apply additional filters
        if statuses:
            batches = batches.filter(status__in=statuses)
        if recipe_type_ids:
            batches = batches.filter(recipe_type_id__in=recipe_type_ids)
        if recipe_type_names:
            batches = batches.filter(recipe_type__name__in=recipe_type_names)

        # Apply sorting
        if order:
            batches = batches.order_by(*order)
        else:
            batches = batches.order_by('last_modified')
        return batches

    def get_details(self, batch_id):
        """Returns the batch for the given ID with all detail fields included.

        :param batch_id: The unique identifier of the batch.
        :type batch_id: int
        :returns: The batch with all detail fields included.
        :rtype: :class:`batch.models.Batch`
        """

        # Attempt to get the batch
        return Batch.objects.select_related('creator_job', 'event', 'recipe_type').get(pk=batch_id)

    def schedule_recipes(self, batch_id):
        """Schedules each recipe that matches the batch for re-processing and creates associated batch models.

        :param batch_id: The unique identifier of the batch that defines the recipes to schedule.
        :type batch_id: string

        :raises :class:`batch.exceptions.BatchError`: If general batch parameters are invalid.
        """

        # Fetch the requested batch for processing
        batch = Batch.objects.get(pk=batch_id)
        if batch.status == 'CREATED':
            raise BatchError('Batch already completed: %i', batch_id)
        batch_definition = batch.get_batch_definition()

        # Fetch all the recipes of the requested type that are not already superseded
        old_recipes = Recipe.objects.filter(recipe_type=batch.recipe_type, is_superseded=False)

        # Exclude recipes that have not actually changed unless requested
        if not (batch_definition.job_names or batch_definition.all_jobs):
            old_recipes = old_recipes.filter(recipe_type__revision_num__gt=F('recipe_type_rev__revision_num'))

        # Optionally filter by date range
        if batch_definition.started:
            old_recipes = old_recipes.filter(created__gte=batch_definition.started)
        if batch_definition.ended:
            old_recipes = old_recipes.filter(created__lte=batch_definition.ended)

        total = old_recipes.count()
        logger.info('Scheduling batch recipes: %i', total)
        batch.total_count = total
        batch.save()

        # Schedule all the new recipes/jobs and create corresponding batch models
        for old_recipe in old_recipes.iterator():
            try:
                self._process_recipe(batch, old_recipe)
            except:
                logger.exception('Unable to supersede batch recipe: %i', old_recipe.id)
                batch.failed_count += 1
                batch.save()
        logger.info('Created: %i, Failed: %i', batch.created_count, batch.failed_count)

        # Update the final batch state
        # Recompute the total to catch models that may have matched after the count query
        batch.status = 'CREATED'
        batch.total_count = batch.created_count + batch.failed_count
        batch.save()

    @transaction.atomic
    def _process_recipe(self, batch, old_recipe):
        """Creates all the batch-specific models to track the new jobs that were queued.

        Each batch recipe and its batch jobs are created in an atomic transaction to support resuming the batch command
        when it is interrupted prematurely.

        :param batch: The batch that defines the recipes to schedule
        :type batch: :class:`batch.models.Batch`
        :param old_recipe: The old recipe that was superseded
        :type old_recipe: :class:`recipe.models.Recipe`
        """

        # Check whether the batch recipe already exists
        if BatchRecipe.objects.filter(batch=batch, superseded_recipe=old_recipe).exists():
            return

        # Create the new recipe and its associated jobs
        batch_definition = batch.get_batch_definition()
        handler = Recipe.objects.reprocess_recipe(old_recipe.id, batch_definition.job_names, batch_definition.all_jobs,
                                                  batch_definition.priority)

        # Fetch all the recipe jobs that were just superseded
        old_recipe_jobs = RecipeJob.objects.select_related('job').filter(recipe=old_recipe, job__is_superseded=True)
        superseded_jobs = {rj.job_name: rj.job for rj in old_recipe_jobs}

        # Create a batch job for each new recipe job
        batch_jobs = []
        now = timezone.now()
        for new_recipe_job in handler.recipe_jobs:
            batch_job = BatchJob()
            batch_job.batch = batch
            batch_job.job = new_recipe_job.job
            batch_job.created = now

            # Associate it to a superseded job when possible
            if new_recipe_job.job_name in superseded_jobs:
                batch_job.superseded_job = superseded_jobs[new_recipe_job.job_name]
            batch_jobs.append(batch_job)
        BatchJob.objects.bulk_create(batch_jobs)

        # Create a batch recipe for the new recipe
        batch_recipe = BatchRecipe()
        batch_recipe.batch = batch
        batch_recipe.recipe = handler.recipe
        batch_recipe.superseded_recipe = old_recipe
        batch_recipe.save()

        # Update the overall batch status
        batch.created_count += 1
        batch.save()


class Batch(models.Model):
    """Represents a batch of jobs and recipes to be processed on the cluster

    :keyword title: The human-readable name of the batch
    :type title: :class:`django.db.models.CharField`
    :keyword description: An optional description of the batch
    :type description: :class:`django.db.models.TextField`
    :keyword status: The status of the batch
    :type status: :class:`django.db.models.CharField`

    :keyword recipe_type: The type of recipe to re-process
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword event: The event that triggered the creation of this batch
    :type event: :class:`django.db.models.ForeignKey`
    :keyword creator_job: The job that will create the batch recipes and jobs for processing
    :type creator_job: :class:`django.db.models.ForeignKey`

    :keyword definition: JSON definition for setting up the batch
    :type definition: :class:`djorm_pgjson.fields.JSONField`

    :keyword created_count: The number of batch recipes created by this batch.
    :type created_count: :class:`django.db.models.IntegerField`
    :keyword failed_count: The number of batch recipes failed by this batch.
    :type failed_count: :class:`django.db.models.IntegerField`
    :keyword total_count: An approximation of the total number of batch recipes that should be created by this batch.
    :type total_count: :class:`django.db.models.IntegerField`

    :keyword created: When the batch was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the batch was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    BATCH_STATUSES = (
        ('SUBMITTED', 'SUBMITTED'),
        ('CREATED', 'CREATED'),
    )

    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(choices=BATCH_STATUSES, default='SUBMITTED', max_length=50, db_index=True)

    recipe_type = models.ForeignKey('recipe.RecipeType', on_delete=models.PROTECT)
    event = models.ForeignKey('trigger.TriggerEvent', on_delete=models.PROTECT)
    creator_job = models.ForeignKey('job.Job', blank=True, null=True, on_delete=models.PROTECT)

    definition = djorm_pgjson.fields.JSONField()

    created_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = BatchManager()

    def get_batch_definition(self):
        """Returns the definition for this batch

        :returns: The definition for this batch
        :rtype: :class:`batch.configuration.definition.batch_definition.BatchDefinition`
        """

        return BatchDefinition(self.definition)

    class Meta(object):
        """meta information for the db"""
        db_table = 'batch'


class BatchJob(models.Model):
    """Links a new job and a batch together and associates it to the previous job being superseded

    :keyword batch: The batch that the job originated from
    :type batch: :class:`django.db.models.ForeignKey`

    :keyword job: The job scheduled by the associated batch
    :type job: :class:`django.db.models.ForeignKey`
    :keyword superseded_job: The previous job that is being replaced by the new batch job
    :type superseded_job: :class:`django.db.models.ForeignKey`

    :keyword created: When the batch job was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    batch = models.ForeignKey('batch.Batch', on_delete=models.PROTECT)

    job = models.ForeignKey('job.Job', blank=True, null=True, on_delete=models.PROTECT)
    superseded_job = models.ForeignKey('job.Job', related_name='superseded_by_batch', blank=True, null=True,
                                       on_delete=models.PROTECT)

    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        """meta information for the db"""
        db_table = 'batch_job'


class BatchRecipe(models.Model):
    """Links a new recipe and a batch together and associates it to the previous recipe being superseded

    :keyword batch: The batch that the recipe originated from
    :type batch: :class:`django.db.models.ForeignKey`

    :keyword recipe: The recipe scheduled by the associated batch
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword superseded_recipe: The previous recipe that is being replaced by the new batch recipe
    :type superseded_recipe: :class:`django.db.models.ForeignKey`

    :keyword created: When the batch recipe was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    batch = models.ForeignKey('batch.Batch', on_delete=models.PROTECT)

    recipe = models.ForeignKey('recipe.Recipe', blank=True, null=True, on_delete=models.PROTECT)
    superseded_recipe = models.ForeignKey('recipe.Recipe', related_name='superseded_by_batch', blank=True, null=True,
                                          on_delete=models.PROTECT)

    created = models.DateTimeField(auto_now_add=True)

    class Meta(object):
        """meta information for the db"""
        db_table = 'batch_recipe'
