"""Defines the database models for a batch"""
from __future__ import unicode_literals

import logging

import django.contrib.postgres.fields
from django.db import connection, models, transaction
from django.db.models import F, Q
from django.utils.timezone import now

from batch.configuration.definition.batch_definition import BatchDefinition
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

logger = logging.getLogger(__name__)


class BatchManager(models.Manager):
    """Provides additional methods for handling batches"""

    def count_completed_job(self, batch_id):
        """Performs a count-plus-one on the completed job field of a Batch

        :param batch_id: The unique identifier of the batch.
        :type batch_id: int
        """

        Batch.objects.filter(id=batch_id).update(completed_job_count=F('completed_job_count') + 1)

    def count_completed_recipe(self, batch_id):
        """Performs a count-plus-one on the completed recipe field of a Batch

        :param batch_id: The unique identifier of the batch.
        :type batch_id: int
        """

        Batch.objects.filter(id=batch_id).update(completed_recipe_count=F('completed_recipe_count') + 1)

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
        event = TriggerEvent.objects.create_trigger_event('USER', None, trigger_desc, now())

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

        # Create models for batch metrics
        batch_metrics_models = []
        for job_name in recipe_type.get_recipe_definition().get_graph().get_topological_order():
            batch_metrics_model = BatchMetrics()
            batch_metrics_model.batch_id = batch.id
            batch_metrics_model.job_name = job_name
            batch_metrics_models.append(batch_metrics_model)
        BatchMetrics.objects.bulk_create(batch_metrics_models)

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
        batch = Batch.objects.select_related('recipe_type', 'recipe_type__trigger_rule').get(pk=batch_id)
        if batch.status == 'CREATED':
            raise BatchError('Batch already completed: %i', batch_id)
        batch_definition = batch.get_batch_definition()

        # Fetch all the recipes of the requested type that are not already superseded
        old_recipes = self.get_matched_recipes(batch.recipe_type, batch_definition)

        # Fetch all the old files that were never triggered for the recipe type
        old_files = self.get_matched_files(batch.recipe_type, batch_definition)

        # Estimate the batch size
        old_recipes_count = old_recipes.count()
        old_files_count = old_files.count()
        if old_recipes_count + old_files_count > batch.total_count:
            batch.total_count = old_recipes_count + old_files_count
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
        batch.save()

    def get_matched_files(self, recipe_type, definition):
        """Gets all the input files that were never triggered against the given batch criteria.

        :param recipe_type: The type of recipes that should be re-processed
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param definition: The definition for running a batch
        :type definition: :class:`batch.configuration.definition.batch_definition.BatchDefinition`
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

    def get_matched_recipes(self, recipe_type, definition):
        """Gets all the recipes that might be affected by the given batch criteria.

        :param recipe_type: The type of recipes that should be re-processed
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param definition: The definition for running a batch
        :type definition: :class:`batch.configuration.definition.batch_definition.BatchDefinition`
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

        # TODO: unit tests for update_batch_metrics message
        # TODO: create wiki description for update_batch_metrics
        # TODO: update logic to use new metrics fields instead of old ones and document removing old fields

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

    @transaction.atomic
    def _process_trigger(self, batch, trigger_config, input_file):
        """Processes the given input file within the context of a particular batch request.

        Each batch recipe and its batch jobs are created in an atomic transaction to support resuming the batch command
        when it is interrupted prematurely.

        :param batch: The batch that defines the recipes to schedule
        :type batch: :class:`batch.models.Batch`
        :param trigger_config: The trigger rule configuration to use when evaluating source files.
        :type trigger_config: :class:`batch.configuration.definition.batch_definition.BatchTriggerConfiguration`
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
    :keyword status: The status of the batch
    :type status: :class:`django.db.models.CharField`

    :keyword recipe_type: The type of recipe to re-process
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword event: The event that triggered the creation of this batch
    :type event: :class:`django.db.models.ForeignKey`
    :keyword creator_job: The job that will create the batch recipes and jobs for processing
    :type creator_job: :class:`django.db.models.ForeignKey`

    :keyword definition: JSON definition for setting up the batch
    :type definition: :class:`django.contrib.postgres.fields.JSONField`

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
    creator_job = models.ForeignKey('job.Job', related_name='batch_creator_job', blank=True, null=True,
                                    on_delete=models.PROTECT)

    definition = django.contrib.postgres.fields.JSONField(default=dict)

    created_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    completed_job_count = models.IntegerField(default=0)
    completed_recipe_count = models.IntegerField(default=0)
    total_count = models.IntegerField(default=0)

    # Metrics fields
    jobs_total = models.IntegerField(default=0)
    jobs_pending = models.IntegerField(default=0)
    jobs_blocked = models.IntegerField(default=0)
    jobs_queued = models.IntegerField(default=0)
    jobs_running = models.IntegerField(default=0)
    jobs_failed = models.IntegerField(default=0)
    jobs_completed = models.IntegerField(default=0)
    jobs_canceled = models.IntegerField(default=0)
    recipes_total = models.IntegerField(default=0)
    recipes_completed = models.IntegerField(default=0)

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


class BatchMetricsManager(models.Manager):
    """Provides additional methods for handling batch metrics
    """

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
        qry += 'max_job_duration = s.max_job_duration, last_modified = %s '
        qry += 'FROM (SELECT r.batch_id, rj.job_name COUNT(j.id) AS jobs_total, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'PENDING\') AS jobs_pending, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'BLOCKED\') AS jobs_blocked, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'QUEUED\') AS jobs_queued, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'RUNNING\') AS jobs_running, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'FAILED\') AS jobs_failed, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'COMPLETED\') AS jobs_completed, '
        qry += 'MIN(j.ended - j.started) FILTER(WHERE status = \'COMPLETED\') AS min_job_duration, '
        qry += 'AVG(j.ended - j.started) FILTER(WHERE status = \'COMPLETED\') AS avg_job_duration, '
        qry += 'MAX(j.ended - j.started) FILTER(WHERE status = \'COMPLETED\') AS max_job_duration '
        qry += 'FROM recipe_job rj JOIN job j ON rj.job_id = j.id JOIN recipe r ON rj.recipe_id = r.id '
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

    :keyword min_alg_duration: The shortest algorithm duration for all completed jobs for this job name within the batch
    :type min_alg_duration: :class:`django.db.models.DurationField`
    :keyword avg_alg_duration: The average algorithm duration for all completed jobs for this job name within the batch
    :type avg_alg_duration: :class:`django.db.models.DurationField`
    :keyword max_alg_duration: The longest algorithm duration for all completed jobs for this job name within the batch
    :type max_alg_duration: :class:`django.db.models.DurationField`
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

    min_alg_duration = models.DurationField(blank=True, null=True)
    avg_alg_duration = models.DurationField(blank=True, null=True)
    max_alg_duration = models.DurationField(blank=True, null=True)
    min_job_duration = models.DurationField(blank=True, null=True)
    avg_job_duration = models.DurationField(blank=True, null=True)
    max_job_duration = models.DurationField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = BatchMetricsManager()

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
