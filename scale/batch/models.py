"""Defines the database models for a batch"""
from __future__ import unicode_literals

import logging

import django.contrib.postgres.fields
from django.db import connection, models, transaction
from django.db.models import F, Q
from django.utils.timezone import now

from batch.configuration.configuration import BatchConfiguration
from batch.configuration.json.configuration_v6 import convert_configuration_to_v6, BatchConfigurationV6
from batch.definition.exceptions import InvalidDefinition
from batch.definition.json.definition_v6 import convert_definition_to_v6, BatchDefinitionV6
from batch.definition.json.old.batch_definition import BatchDefinition as OldBatchDefinition
from batch.exceptions import BatchError
from job.configuration.data.job_data import JobData
from job.models import JobType
from messaging.manager import CommandMessageManager
from queue.models import Queue
from recipe.configuration.data.recipe_data import RecipeData
from recipe.messages.reprocess_recipes import create_reprocess_recipes_messages
from recipe.models import Recipe, RecipeTypeRevision
from storage.models import ScaleFile, Workspace
from trigger.models import TriggerEvent
from util import parse as parse_utils
from util import rest as rest_utils


logger = logging.getLogger(__name__)


class BatchManager(models.Manager):
    """Provides additional methods for handling batches"""

    # TODO: remove this when v5 REST API is removed
    @transaction.atomic
    def create_batch_old(self, recipe_type, definition, title=None, description=None):
        """Creates a new batch that represents a group of recipes that should be scheduled for re-processing. This
        method also queues a new system job that will process the batch request. All database changes occur in an atomic
        transaction.

        :param recipe_type: The type of recipes that should be re-processed
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param definition: The definition for running a batch
        :type definition: :class:`batch.definition.json.old.batch_definition.BatchDefinition`
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
        event = TriggerEvent.objects.create_trigger_event('USER', None, trigger_desc, now())

        batch = Batch()
        batch.title = title
        batch.description = description
        batch.recipe_type = recipe_type
        batch.recipe_type_rev = RecipeTypeRevision.objects.get_revision(recipe_type.id, recipe_type.revision_num)
        batch.definition = definition.get_dict()
        configuration = BatchConfiguration()
        if 'priority' in definition.get_dict():
            configuration.priority = definition.get_dict()['priority']
        batch.configuration = convert_configuration_to_v6(configuration).get_dict()
        batch.event = event
        batch.save()

        # Setup the job data to process the batch
        data = JobData()
        data.add_property_input('Batch ID', str(batch.id))

        # Schedule the batch job
        job = Queue.objects.queue_new_job(job_type, data, event)
        batch.creator_job = job
        batch.save()

        # Create models for batch metrics
        batch_metrics_models = []
        for job_name in recipe_type.get_recipe_definition().get_graph().get_topological_order():
            batch_metrics_model = BatchMetrics()
            batch_metrics_model.batch_id = batch.id
            batch_metrics_model.job_name = job_name
            batch_metrics_models.append(batch_metrics_model)
        BatchMetrics.objects.bulk_create(batch_metrics_models)

        return batch

    def create_batch_v6(self, title, description, recipe_type, event, definition, configuration=None):
        """Creates a new batch that will contain a collection of recipes to process. The definition and configuration
        will be stored in version 6 of their respective schemas. This method will only create the batch, not its
        recipes. To create the batch's recipes, a CreateBatchRecipes message needs to be sent to the messaging backend.

        :param title: The human-readable name of the batch
        :type title: string
        :param description: A human-readable description of the batch
        :type description: string
        :param recipe_type: The type of recipes that will be created for this batch
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param event: The event that created this batch
        :type event: :class:`trigger.models.TriggerEvent`
        :param definition: The definition for running the batch
        :type definition: :class:`batch.definition.definition.BatchDefinition`
        :param configuration: The batch configuration
        :type configuration: :class:`batch.configuration.configuration.BatchConfiguration`
        :returns: The newly created batch
        :rtype: :class:`batch.models.Batch`

        :raises :class:`batch.configuration.exceptions.InvalidConfiguration`: If the configuration is invalid
        :raises :class:`batch.definition.exceptions.InvalidDefinition`: If the definition is invalid
        """

        batch = Batch()
        batch.title = title
        batch.description = description
        batch.recipe_type = recipe_type
        batch.recipe_type_rev = RecipeTypeRevision.objects.get_revision(recipe_type.id, recipe_type.revision_num)
        batch.event = event
        batch.definition = convert_definition_to_v6(definition).get_dict()
        batch.configuration = convert_configuration_to_v6(configuration).get_dict()

        with transaction.atomic():
            if definition.root_batch_id is not None:
                # Find latest batch with the root ID and supersede it
                try:
                    superseded_batch = Batch.objects.get_locked_batch_from_root(definition.root_batch_id)
                except Batch.DoesNotExist:
                    raise InvalidDefinition('No batch with that root ID exists')
                batch.root_batch_id = superseded_batch.root_batch_id
                batch.superseded_batch = superseded_batch
                self.supersede_batch(superseded_batch.id, now())

            definition.validate(batch)
            configuration.validate(batch)

            batch.recipes_estimated = definition.estimate_recipe_total(batch)
            batch.save()
            if batch.root_batch_id is None:  # Batches with no superseded batch are their own root
                batch.root_batch_id = batch.id
                Batch.objects.filter(id=batch.id).update(root_batch_id=batch.id)

            # Create models for batch metrics
            batch_metrics_models = []
            for job_name in recipe_type.get_recipe_definition().get_graph().get_topological_order():
                batch_metrics_model = BatchMetrics()
                batch_metrics_model.batch_id = batch.id
                batch_metrics_model.job_name = job_name
                batch_metrics_models.append(batch_metrics_model)
            BatchMetrics.objects.bulk_create(batch_metrics_models)

        return batch

    def edit_batch_v6(self, batch, title=None, description=None, configuration=None):
        """Edits the given batch to update any of the given fields. The configuration will be stored in version 6 of its
        schemas.

        :param batch: The batch to edit
        :type batch: :class:`batch.models.Batch`
        :param title: The human-readable name of the batch
        :type title: string
        :param description: A human-readable description of the batch
        :type description: string
        :param configuration: The batch configuration
        :type configuration: :class:`batch.configuration.configuration.BatchConfiguration`

        :raises :class:`batch.configuration.exceptions.InvalidConfiguration`: If the configuration is invalid
        """

        update_fields = {}

        if title is not None:
            update_fields['title'] = title
        if description is not None:
            update_fields['description'] = description

        if configuration:
            configuration.validate(batch)
            configuration_dict = convert_configuration_to_v6(configuration).get_dict()
            update_fields['configuration'] = configuration_dict

        if update_fields:
            Batch.objects.filter(id=batch.id).update(**update_fields)

    def get_batches_v5(self, started=None, ended=None, statuses=None, recipe_type_ids=None, recipe_type_names=None,
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

    def get_batches_v6(self, started=None, ended=None, recipe_type_ids=None, is_creation_done=None, is_superseded=None,
                       root_batch_ids=None, order=None):
        """Returns a list of batches for the v6 batches REST API

        :param started: Query batches updated after this time
        :type started: :class:`datetime.datetime`
        :param ended: Query batches updated before this time
        :type ended: :class:`datetime.datetime`
        :param recipe_type_ids: Query batches with these recipe types
        :type recipe_type_ids: list
        :param is_creation_done: Query batches that match this value
        :type is_creation_done: bool
        :param is_superseded: Query batches that match this value
        :type is_superseded: bool
        :param root_batch_ids: Query batches with these root batches
        :type root_batch_ids: list
        :param order: A list of fields to control the sort order
        :type order: list
        :returns: The list of batches that match the given criteria
        :rtype: list
        """

        # Fetch a list of batches
        batches = Batch.objects.all()
        batches = batches.select_related('recipe_type', 'recipe_type_rev', 'event', 'root_batch', 'superseded_batch')
        batches = batches.defer('definition', 'configuration')

        # Apply time range filtering
        if started:
            batches = batches.filter(last_modified__gte=started)
        if ended:
            batches = batches.filter(last_modified__lte=ended)

        # Apply additional filters
        if recipe_type_ids:
            batches = batches.filter(recipe_type_id__in=recipe_type_ids)
        if is_creation_done is not None:
            batches = batches.filter(is_creation_done=is_creation_done)
        if is_superseded is not None:
            batches = batches.filter(is_superseded=is_superseded)
        if root_batch_ids:
            batches = batches.filter(root_batch_id__in=root_batch_ids)

        # Apply sorting
        if order:
            batches = batches.order_by(*order)
        else:
            batches = batches.order_by('last_modified')
        return batches

    def get_details_v5(self, batch_id):
        """Returns the batch for the given ID with all detail fields included.

        :param batch_id: The unique identifier of the batch.
        :type batch_id: int
        :returns: The batch with all detail fields included.
        :rtype: :class:`batch.models.Batch`
        """

        # Attempt to get the batch
        return Batch.objects.select_related('creator_job', 'event', 'recipe_type').get(pk=batch_id)

    def get_details_v6(self, batch_id):
        """Returns the batch (and related fields) with the given ID for the v6 batch details REST API

        :param batch_id: The unique identifier of the batch
        :type batch_id: int
        :returns: The batch with all related fields included
        :rtype: :class:`batch.models.Batch`
        """

        qry = Batch.objects.select_related('recipe_type', 'recipe_type_rev', 'event', 'root_batch', 'superseded_batch')
        batch = qry.get(pk=batch_id)

        BatchMetrics.objects.add_metrics_to_batch(batch)

        return batch

    def get_locked_batch_from_root(self, root_batch_id):
        """Locks and returns the latest (non-superseded) batch model with the given root batch ID. The returned model
        will have no related fields populated. Caller must be within an atomic transaction.

        :param root_batch_id: The root batch ID
        :type root_batch_id: int
        :returns: The batch model
        :rtype: :class:`batch.models.Batch`
        """

        return self.select_for_update().get(root_batch_id=root_batch_id, is_superseded=False)

    def mark_creation_done(self, batch_id, when):
        """Marks recipe creation as done for this batch

        :param batch_id: The batch ID
        :type batch_id: int
        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        self.filter(id=batch_id).update(is_creation_done=True, last_modified=when)

    def supersede_batch(self, batch_id, when):
        """Updates the given batch to be superseded

        :param batch_id: The batch ID to supersede
        :type batch_id: list
        :param when: The time that the batch was superseded
        :type when: :class:`datetime.datetime`
        """

        self.filter(id=batch_id).update(is_superseded=True, superseded=when, last_modified=now())

    # TODO: remove this when v5 REST API is removed
    def schedule_recipes(self, batch_id):
        """Schedules each recipe that matches the batch for re-processing and creates associated batch models.

        :param batch_id: The unique identifier of the batch that defines the recipes to schedule.
        :type batch_id: string

        :raises :class:`batch.exceptions.BatchError`: If general batch parameters are invalid.
        """

        # Fetch the requested batch for processing
        batch = Batch.objects.select_related('recipe_type', 'recipe_type__trigger_rule').get(pk=batch_id)
        if batch.status == 'CREATED':
            raise BatchError('Batch already completed: %i', batch_id)
        batch_definition = batch.get_old_definition()

        # Fetch all the recipes of the requested type that are not already superseded
        old_recipes = self.get_matched_recipes(batch.recipe_type, batch_definition)

        # Fetch all the old files that were never triggered for the recipe type
        old_files = self.get_matched_files(batch.recipe_type, batch_definition)

        # Estimate the batch size
        old_recipes_count = old_recipes.count()
        old_files_count = old_files.count()
        if old_recipes_count + old_files_count > batch.total_count:
            batch.total_count = old_recipes_count + old_files_count
            batch.recipes_estimated = batch.total_count
            batch.save()

        # Send messages to reprocess old recipes
        logger.info('Sending messages to reprocess old recipes: %i', old_recipes_count)
        new_rev = RecipeTypeRevision.objects.get_revision(batch.recipe_type_id, batch.recipe_type.revision_num)
        root_recipe_ids = []
        for old_recipe in old_recipes.iterator():
            root_id = old_recipe.root_superseded_recipe_id if old_recipe.root_superseded_recipe_id else old_recipe.id
            root_recipe_ids.append(root_id)
        if root_recipe_ids:
            all_jobs = batch_definition.all_jobs
            job_names = batch_definition.job_names
            messages = create_reprocess_recipes_messages(root_recipe_ids, new_rev.id, batch.event_id, all_jobs=all_jobs,
                                                         job_names=job_names, batch_id=batch.id)
            CommandMessageManager().send_messages(messages)
            # Update the overall batch status
            batch.created_count += old_recipes_count
            batch.save()

        # Determine what trigger rule should be applied
        trigger_config = None
        if batch_definition.trigger_rule:
            trigger_config = batch.recipe_type.trigger_rule.get_configuration()
        elif batch_definition.trigger_config:
            trigger_config = batch_definition.trigger_config

        # Schedule new recipes for old files
        logger.info('Scheduling new batch recipes for old files: %i', old_recipes_count)
        for old_file in old_files.iterator():
            try:
                self._process_trigger(batch, trigger_config, old_file)
            except:
                logger.exception('Unable to trigger batch file: %i', old_file.id)
                batch.failed_count += 1
                batch.save()

        # Update the final batch state
        # Recompute the total to catch models that may have matched after the count query
        logger.info('Created: %i, Failed: %i', batch.created_count, batch.failed_count)
        batch.status = 'CREATED'
        batch.total_count = batch.created_count + batch.failed_count
        batch.is_creation_done = True
        batch.save()

    # TODO: remove this when v5 REST API is removed
    def get_matched_files(self, recipe_type, definition):
        """Gets all the input files that were never triggered against the given batch criteria.

        :param recipe_type: The type of recipes that should be re-processed
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param definition: The definition for running a batch
        :type definition: :class:`batch.definition.json.old.batch_definition.BatchDefinition`
        :returns: A list of files that match the batch definition and were never run before.
        :rtype: [:class:`storage.models.ScaleFile`]
        """

        # Check whether old files should be triggered
        if not definition.trigger_rule and not definition.trigger_config:
            return ScaleFile.objects.none()

        # Fetch all the files that were not already processed by the recipe type
        old_files = ScaleFile.objects.exclude(recipeinputfile__recipe__recipe_type=recipe_type)

        # Optionally filter by date range
        if definition.date_range_type == 'created':
            if definition.started:
                old_files = old_files.filter(created__gte=definition.started)
            if definition.ended:
                old_files = old_files.filter(created__lte=definition.ended)
        elif definition.date_range_type == 'data':
            # The filters must include OR operators since the file data started/ended fields can be null
            if definition.started:
                old_files = old_files.filter(Q(data_started__gte=definition.started) |
                                             Q(data_ended__gte=definition.started))
            if definition.ended:
                old_files = old_files.filter(Q(data_started__lte=definition.ended) |
                                             Q(data_ended__lte=definition.ended))
        return old_files

    # TODO: remove this when v5 REST API is removed
    def get_matched_recipes(self, recipe_type, definition):
        """Gets all the recipes that might be affected by the given batch criteria.

        :param recipe_type: The type of recipes that should be re-processed
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param definition: The definition for running a batch
        :type definition: :class:`batch.definition.json.old.batch_definition.BatchDefinition`
        :returns: A list of recipes that match the batch definition.
        :rtype: [:class:`recipe.models.Recipe`]
        """

        # Fetch all the recipes of the requested type that are not already superseded
        old_recipes = Recipe.objects.filter(recipe_type=recipe_type, is_superseded=False)

        # Exclude recipes that have not actually changed unless requested
        if not (definition.job_names or definition.all_jobs):
            old_recipes = old_recipes.filter(recipe_type__revision_num__gt=F('recipe_type_rev__revision_num'))

        # Optionally filter by date range
        if definition.date_range_type == 'created':
            if definition.started:
                old_recipes = old_recipes.filter(created__gte=definition.started)
            if definition.ended:
                old_recipes = old_recipes.filter(created__lte=definition.ended)
        elif definition.date_range_type == 'data':
            # The filters must include OR operators since the file data started/ended fields can be null
            if definition.started:
                old_recipes = old_recipes.filter(Q(recipeinputfile__scale_file__data_started__gte=definition.started) |
                                                 Q(recipeinputfile__scale_file__data_ended__gte=definition.started))
            if definition.ended:
                old_recipes = old_recipes.filter(Q(recipeinputfile__scale_file__data_started__lte=definition.ended) |
                                                 Q(recipeinputfile__scale_file__data_ended__lte=definition.ended))
        return old_recipes

    def update_batch_metrics(self, batch_ids):
        """Updates the metrics for the batches with the given IDs

        :param batch_ids: The batch IDs
        :type batch_ids: list
        """

        if not batch_ids:
            return

        # Update recipe metrics for batch
        qry = 'UPDATE batch b SET recipes_total = s.recipes_total, recipes_completed = s.recipes_completed '
        qry += 'FROM (SELECT r.batch_id, COUNT(r.id) AS recipes_total, '
        qry += 'COUNT(r.id) FILTER(WHERE r.is_completed) AS recipes_completed '
        qry += 'FROM recipe r WHERE r.batch_id IN %s GROUP BY r.batch_id) s '
        qry += 'WHERE b.id = s.batch_id'
        with connection.cursor() as cursor:
            cursor.execute(qry, [tuple(batch_ids)])

        # Update job metrics for batch
        qry = 'UPDATE batch b SET jobs_total = s.jobs_total, jobs_pending = s.jobs_pending, '
        qry += 'jobs_blocked = s.jobs_blocked, jobs_queued = s.jobs_queued, jobs_running = s.jobs_running, '
        qry += 'jobs_failed = s.jobs_failed, jobs_completed = s.jobs_completed, jobs_canceled = s.jobs_canceled, '
        qry += 'last_modified = %s FROM (SELECT r.batch_id, COUNT(j.id) AS jobs_total, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'PENDING\') AS jobs_pending, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'BLOCKED\') AS jobs_blocked, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'QUEUED\') AS jobs_queued, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'RUNNING\') AS jobs_running, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'FAILED\') AS jobs_failed, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'COMPLETED\') AS jobs_completed, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'CANCELED\') AS jobs_canceled '
        qry += 'FROM recipe_job rj JOIN job j ON rj.job_id = j.id JOIN recipe r ON rj.recipe_id = r.id '
        qry += 'WHERE r.batch_id IN %s GROUP BY r.batch_id) s '
        qry += 'WHERE b.id = s.batch_id'
        with connection.cursor() as cursor:
            cursor.execute(qry, [now(), tuple(batch_ids)])

        BatchMetrics.objects.update_batch_metrics_per_job(batch_ids)

    # TODO: remove this when v5 REST API is removed
    @transaction.atomic
    def _process_trigger(self, batch, trigger_config, input_file):
        """Processes the given input file within the context of a particular batch request.

        Each batch recipe and its batch jobs are created in an atomic transaction to support resuming the batch command
        when it is interrupted prematurely.

        :param batch: The batch that defines the recipes to schedule
        :type batch: :class:`batch.models.Batch`
        :param trigger_config: The trigger rule configuration to use when evaluating source files.
        :type trigger_config: :class:`batch.definition.json.old.batch_definition.BatchTriggerConfiguration`
        :param input_file: The input file that should trigger a new batch recipe
        :type input_file: :class:`storage.models.ScaleFile`
        """

        # Check whether the source file matches the trigger condition
        if hasattr(trigger_config, 'get_condition'):
            condition = trigger_config.get_condition()
            if not condition.is_condition_met(input_file):
                return

        # Build recipe data to pass input file parameters to new recipes
        recipe_data = RecipeData({})
        if hasattr(trigger_config, 'get_input_data_name'):
            recipe_data.add_file_input(trigger_config.get_input_data_name(), input_file.id)
        if hasattr(trigger_config, 'get_workspace_name'):
            workspace = Workspace.objects.get(name=trigger_config.get_workspace_name())
            recipe_data.set_workspace_id(workspace.id)

        description = {
            'version': '1.0',
            'file_id': input_file.id,
            'file_name': input_file.file_name,
        }
        event = TriggerEvent.objects.create_trigger_event('BATCH', None, description, now())
        Queue.objects.queue_new_recipe(batch.recipe_type, recipe_data, event, batch_id=batch.id)
        # Update the overall batch status
        batch.created_count += 1
        batch.save()


class Batch(models.Model):
    """Represents a batch of jobs and recipes to be processed on the cluster

    :keyword title: The human-readable name of the batch
    :type title: :class:`django.db.models.CharField`
    :keyword description: An optional description of the batch
    :type description: :class:`django.db.models.TextField`
    :keyword recipe_type: The type of recipe being processed in this batch
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword recipe_type_rev: The revision of the recipe type being processed in this batch
    :type recipe_type_rev: :class:`django.db.models.ForeignKey`
    :keyword event: The event that triggered the creation of this batch
    :type event: :class:`django.db.models.ForeignKey`

    :keyword status: The status of the batch
    :type status: :class:`django.db.models.CharField`
    :keyword creator_job: The job that will create the batch recipes and jobs for processing
    :type creator_job: :class:`django.db.models.ForeignKey`

    :keyword definition: JSON definition for what is being processed by this batch
    :type definition: :class:`django.contrib.postgres.fields.JSONField`
    :keyword configuration: JSON configuration for running the batch
    :type configuration: :class:`django.contrib.postgres.fields.JSONField`
    :keyword is_creation_done: Indicates whether all of the recipes for the batch have been created (True)
    :type is_creation_done: :class:`django.db.models.BooleanField`

    :keyword created_count: The number of batch recipes created by this batch.
    :type created_count: :class:`django.db.models.IntegerField`
    :keyword failed_count: The number of batch recipes failed by this batch.
    :type failed_count: :class:`django.db.models.IntegerField`
    :keyword total_count: An approximation of the total number of batch recipes that should be created by this batch.
    :type total_count: :class:`django.db.models.IntegerField`

    :keyword is_superseded: Indicates whether this batch has been superseded (re-processed by another batch)
    :type is_superseded: :class:`django.db.models.BooleanField`
    :keyword root_batch: The first (root) batch in this chain of iterative batches. This field will be null for the
        first batch in the chain.
    :type root_batch: :class:`django.db.models.ForeignKey`
    :keyword superseded_batch: The superseded (previous) batch that was re-processed by this batch
    :type superseded_batch: :class:`django.db.models.OneToOneField`

    :keyword jobs_total: The total count of all jobs within the batch
    :type jobs_total: :class:`django.db.models.IntegerField`
    :keyword jobs_pending: The count of all PENDING jobs within the batch
    :type jobs_pending: :class:`django.db.models.IntegerField`
    :keyword jobs_blocked: The count of all BLOCKED jobs within the batch
    :type jobs_blocked: :class:`django.db.models.IntegerField`
    :keyword jobs_queued: The count of all QUEUED jobs within the batch
    :type jobs_queued: :class:`django.db.models.IntegerField`
    :keyword jobs_running: The count of all RUNNING jobs within the batch
    :type jobs_running: :class:`django.db.models.IntegerField`
    :keyword jobs_failed: The count of all FAILED jobs within the batch
    :type jobs_failed: :class:`django.db.models.IntegerField`
    :keyword jobs_completed: The count of all COMPLETED jobs within the batch
    :type jobs_completed: :class:`django.db.models.IntegerField`
    :keyword jobs_canceled: The count of all CANCELED jobs within the batch
    :type jobs_canceled: :class:`django.db.models.IntegerField`
    :keyword recipes_estimated: The estimated count for all recipes that will be created for the batch
    :type recipes_estimated: :class:`django.db.models.IntegerField`
    :keyword recipes_total: The total count for all recipes within the batch
    :type recipes_total: :class:`django.db.models.IntegerField`
    :keyword recipes_completed: The count for all completed recipes within the batch
    :type recipes_completed: :class:`django.db.models.IntegerField`

    :keyword created: When the batch was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword superseded: When this batch was superseded
    :type superseded: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the batch was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    # TODO: remove this after v5 REST API is removed
    BATCH_STATUSES = (
        ('SUBMITTED', 'SUBMITTED'),
        ('CREATED', 'CREATED'),
    )

    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.TextField(blank=True, null=True)
    recipe_type = models.ForeignKey('recipe.RecipeType', on_delete=models.PROTECT)
    recipe_type_rev = models.ForeignKey('recipe.RecipeTypeRevision', on_delete=models.PROTECT)
    event = models.ForeignKey('trigger.TriggerEvent', on_delete=models.PROTECT)

    # TODO: remove this after v5 REST API is removed
    status = models.CharField(choices=BATCH_STATUSES, default='SUBMITTED', max_length=50, db_index=True)
    creator_job = models.ForeignKey('job.Job', related_name='batch_creator_job', blank=True, null=True,
                                    on_delete=models.PROTECT)

    definition = django.contrib.postgres.fields.JSONField(default=dict)
    configuration = django.contrib.postgres.fields.JSONField(default=dict)
    is_creation_done = models.BooleanField(default=False)

    # TODO: remove these fields after v5 REST API is removed
    created_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    completed_job_count = models.IntegerField(default=0)
    completed_recipe_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)

    # Fields for linking iterative batches together
    is_superseded = models.BooleanField(default=False)
    root_batch = models.ForeignKey('batch.Batch', related_name='linked_batches', blank=True, null=True,
                                   on_delete=models.PROTECT)
    superseded_batch = models.OneToOneField('batch.Batch', related_name='next_batch', blank=True, null=True,
                                            on_delete=models.PROTECT)

    # Metrics fields
    jobs_total = models.IntegerField(default=0)
    jobs_pending = models.IntegerField(default=0)
    jobs_blocked = models.IntegerField(default=0)
    jobs_queued = models.IntegerField(default=0)
    jobs_running = models.IntegerField(default=0)
    jobs_failed = models.IntegerField(default=0)
    jobs_completed = models.IntegerField(default=0)
    jobs_canceled = models.IntegerField(default=0)
    recipes_estimated = models.IntegerField(default=0)
    recipes_total = models.IntegerField(default=0)
    recipes_completed = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    superseded = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = BatchManager()

    def get_configuration(self):
        """Returns the configuration for this batch

        :returns: The configuration for this batch
        :rtype: :class:`batch.configuration.configuration.BatchConfiguration`
        """

        return BatchConfigurationV6(configuration=self.configuration, do_validate=False).get_configuration()

    def get_definition(self):
        """Returns the definition for this batch

        :returns: The definition for this batch
        :rtype: :class:`batch.definition.definition.BatchDefinition`
        """

        return BatchDefinitionV6(definition=self.definition, do_validate=False).get_definition()

    def get_old_definition(self):
        """Returns the definition for this batch

        :returns: The definition for this batch
        :rtype: :class:`batch.definition.json.old.batch_definition.BatchDefinition`
        """

        return OldBatchDefinition(self.definition)

    def get_old_definition_json(self):
        """Returns the batch definition in the old version of the JSON schema

        :returns: The batch definition in the old version of the JSON schema
        :rtype: dict
        """

        # Handle batches with new (v6 and newer) definitions
        if 'version' in self.definition and self.definition['version'] == '6':
            json_dict = {'version': '1.0'}
            if 'previous_batch' in self.definition:
                prev_batch_dict = self.definition['previous_batch']
                if 'job_names' in prev_batch_dict:
                    json_dict['job_names'] = prev_batch_dict['job_names']
                if 'all_jobs' in prev_batch_dict:
                    json_dict['all_jobs'] = prev_batch_dict['all_jobs']
            return json_dict

        return self.definition

    def get_v6_configuration_json(self):
        """Returns the batch configuration in v6 of the JSON schema

        :returns: The batch configuration in v6 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_configuration_to_v6(self.get_configuration()).get_dict())

    def get_v6_definition_json(self):
        """Returns the batch definition in v6 of the JSON schema

        :returns: The batch definition in v6 of the JSON schema
        :rtype: dict
        """

        # Handle batches with old (pre-v6) definitions
        if 'version' in self.definition and self.definition['version'] == '1.0':
            return {}

        return rest_utils.strip_schema_version(convert_definition_to_v6(self.get_definition()).get_dict())

    class Meta(object):
        """meta information for the db"""
        db_table = 'batch'


class BatchMetricsManager(models.Manager):
    """Provides additional methods for handling batch metrics
    """

    def add_metrics_to_batch(self, batch):
        """Adds the metrics per recipe job to the given batch

        :param batch: The batch
        :type batch: :class:`batch.models.Batch`
        """

        job_metrics_dict = {}
        for metrics in self.get_batch_metrics(batch.id):
            job_metrics_dict[metrics.job_name] = metrics.to_dict()
        batch.job_metrics = job_metrics_dict

    def get_batch_metrics(self, batch_id):
        """Returns the metrics models for the given batch ID

        :param batch_id: The batch ID
        :type batch_id: int
        :returns: The metrics models for the batch
        :rtype: list
        """

        return self.filter(batch_id=batch_id)

    def update_batch_metrics_per_job(self, batch_ids):
        """Updates the metrics per job name for the batches with the given IDs

        :param batch_ids: The batch IDs
        :type batch_ids: list
        """

        if not batch_ids:
            return

        qry = 'UPDATE batch_metrics bm SET jobs_total = s.jobs_total, jobs_pending = s.jobs_pending, '
        qry += 'jobs_blocked = s.jobs_blocked, jobs_queued = s.jobs_queued, jobs_running = s.jobs_running, '
        qry += 'jobs_failed = s.jobs_failed, jobs_completed = s.jobs_completed, jobs_canceled = s.jobs_canceled, '
        qry += 'min_job_duration = s.min_job_duration, avg_job_duration = s.avg_job_duration, '
        qry += 'max_job_duration = s.max_job_duration, min_seed_duration = s.min_seed_duration, '
        qry += 'avg_seed_duration = s.avg_seed_duration, max_seed_duration = s.max_seed_duration, last_modified = %s '
        qry += 'FROM (SELECT r.batch_id, rj.job_name, COUNT(j.id) AS jobs_total, '
        qry += 'COUNT(j.id) FILTER(WHERE j.status = \'PENDING\') AS jobs_pending, '
        qry += 'COUNT(j.id) FILTER(WHERE j.status = \'BLOCKED\') AS jobs_blocked, '
        qry += 'COUNT(j.id) FILTER(WHERE j.status = \'QUEUED\') AS jobs_queued, '
        qry += 'COUNT(j.id) FILTER(WHERE j.status = \'RUNNING\') AS jobs_running, '
        qry += 'COUNT(j.id) FILTER(WHERE j.status = \'FAILED\') AS jobs_failed, '
        qry += 'COUNT(j.id) FILTER(WHERE j.status = \'COMPLETED\') AS jobs_completed, '
        qry += 'COUNT(j.id) FILTER(WHERE j.status = \'CANCELED\') AS jobs_canceled, '
        qry += 'MIN(j.ended - j.started) FILTER(WHERE j.status = \'COMPLETED\') AS min_job_duration, '
        qry += 'AVG(j.ended - j.started) FILTER(WHERE j.status = \'COMPLETED\') AS avg_job_duration, '
        qry += 'MAX(j.ended - j.started) FILTER(WHERE j.status = \'COMPLETED\') AS max_job_duration, '
        qry += 'MIN(je.seed_ended - je.seed_started) FILTER(WHERE j.status = \'COMPLETED\') AS min_seed_duration, '
        qry += 'AVG(je.seed_ended - je.seed_started) FILTER(WHERE j.status = \'COMPLETED\') AS avg_seed_duration, '
        qry += 'MAX(je.seed_ended - je.seed_started) FILTER(WHERE j.status = \'COMPLETED\') AS max_seed_duration '
        qry += 'FROM recipe_job rj JOIN job j ON rj.job_id = j.id JOIN recipe r ON rj.recipe_id = r.id '
        qry += 'LEFT OUTER JOIN job_exe_end je ON je.job_id = j.id AND je.exe_num = j.num_exes '
        qry += 'WHERE r.batch_id IN %s GROUP BY r.batch_id, rj.job_name) s '
        qry += 'WHERE bm.batch_id = s.batch_id AND bm.job_name = s.job_name'
        with connection.cursor() as cursor:
            cursor.execute(qry, [now(), tuple(batch_ids)])


class BatchMetrics(models.Model):
    """Contains a set of metrics for a given job name ("node" within a recipe graph) for a given batch

    :keyword batch: The batch
    :type batch: :class:`django.db.models.ForeignKey`
    :keyword job_name: The unique name of the job within the batch
    :type job_name: :class:`django.db.models.CharField`

    :keyword jobs_total: The total count of all jobs for this job name within the batch
    :type jobs_total: :class:`django.db.models.IntegerField`
    :keyword jobs_pending: The count of all PENDING jobs for this job name within the batch
    :type jobs_pending: :class:`django.db.models.IntegerField`
    :keyword jobs_blocked: The count of all BLOCKED jobs for this job name within the batch
    :type jobs_blocked: :class:`django.db.models.IntegerField`
    :keyword jobs_queued: The count of all QUEUED jobs for this job name within the batch
    :type jobs_queued: :class:`django.db.models.IntegerField`
    :keyword jobs_running: The count of all RUNNING jobs for this job name within the batch
    :type jobs_running: :class:`django.db.models.IntegerField`
    :keyword jobs_failed: The count of all FAILED jobs for this job name within the batch
    :type jobs_failed: :class:`django.db.models.IntegerField`
    :keyword jobs_completed: The count of all COMPLETED jobs for this job name within the batch
    :type jobs_completed: :class:`django.db.models.IntegerField`
    :keyword jobs_canceled: The count of all CANCELED jobs for this job name within the batch
    :type jobs_canceled: :class:`django.db.models.IntegerField`

    :keyword min_seed_duration: The shortest Seed run duration for all completed jobs for this job name within the batch
    :type min_seed_duration: :class:`django.db.models.DurationField`
    :keyword avg_seed_duration: The average Seed run duration for all completed jobs for this job name within the batch
    :type avg_seed_duration: :class:`django.db.models.DurationField`
    :keyword max_seed_duration: The longest Seed run duration for all completed jobs for this job name within the batch
    :type max_seed_duration: :class:`django.db.models.DurationField`
    :keyword min_job_duration: The shortest job duration for all completed jobs for this job name within the batch
    :type min_job_duration: :class:`django.db.models.DurationField`
    :keyword avg_job_duration: The average job duration for all completed jobs for this job name within the batch
    :type avg_job_duration: :class:`django.db.models.DurationField`
    :keyword max_job_duration: The longest job duration for all completed jobs for this job name within the batch
    :type max_job_duration: :class:`django.db.models.DurationField`

    :keyword created: When these metrics were created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When these metrics were last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    batch = models.ForeignKey('batch.Batch', on_delete=models.PROTECT)
    job_name = models.CharField(max_length=100)

    jobs_total = models.IntegerField(default=0)
    jobs_pending = models.IntegerField(default=0)
    jobs_blocked = models.IntegerField(default=0)
    jobs_queued = models.IntegerField(default=0)
    jobs_running = models.IntegerField(default=0)
    jobs_failed = models.IntegerField(default=0)
    jobs_completed = models.IntegerField(default=0)
    jobs_canceled = models.IntegerField(default=0)

    min_seed_duration = models.DurationField(blank=True, null=True)
    avg_seed_duration = models.DurationField(blank=True, null=True)
    max_seed_duration = models.DurationField(blank=True, null=True)
    min_job_duration = models.DurationField(blank=True, null=True)
    avg_job_duration = models.DurationField(blank=True, null=True)
    max_job_duration = models.DurationField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = BatchMetricsManager()

    def to_dict(self):
        """Returns a dict representing these metrics

        :returns: The dict representing these metrics
        :rtype: dict
        """

        metrics_dict = {'jobs_total': self.jobs_total, 'jobs_pending': self.jobs_pending,
                        'jobs_blocked': self.jobs_blocked, 'jobs_queued': self.jobs_queued,
                        'jobs_running': self.jobs_running, 'jobs_failed': self.jobs_failed,
                        'jobs_completed': self.jobs_completed, 'jobs_canceled': self.jobs_canceled,
                        'min_seed_duration': None, 'avg_seed_duration': None, 'max_seed_duration': None,
                        'min_job_duration': None, 'avg_job_duration': None, 'max_job_duration': None}
        if self.min_seed_duration:
            metrics_dict['min_seed_duration'] = parse_utils.duration_to_string(self.min_seed_duration)
        if self.avg_seed_duration:
            metrics_dict['avg_seed_duration'] = parse_utils.duration_to_string(self.avg_seed_duration)
        if self.max_seed_duration:
            metrics_dict['max_seed_duration'] = parse_utils.duration_to_string(self.max_seed_duration)
        if self.min_job_duration:
            metrics_dict['min_job_duration'] = parse_utils.duration_to_string(self.min_job_duration)
        if self.avg_job_duration:
            metrics_dict['avg_job_duration'] = parse_utils.duration_to_string(self.avg_job_duration)
        if self.max_job_duration:
            metrics_dict['max_job_duration'] = parse_utils.duration_to_string(self.max_job_duration)

        return metrics_dict

    class Meta(object):
        """meta information for the db"""
        db_table = 'batch_metrics'
        unique_together = ('batch', 'job_name')


# TODO: when removing this and BatchRecipe, remove them from the databse update and make a note in the next release that
# Scale needs to have the databse update run before upgrading to this new release
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
