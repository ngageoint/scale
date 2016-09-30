"""Defines the database models for a batch"""
from __future__ import unicode_literals

import django.utils.timezone as timezone
import djorm_pgjson.fields
from django.db import models, transaction

from batch.configuration.definition.batch_definition import BatchDefinition
from batch.exceptions import BatchError
from job.configuration.data.job_data import JobData
from job.models import JobType
from queue.models import Queue
from trigger.models import TriggerEvent


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
