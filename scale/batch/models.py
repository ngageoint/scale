"""Defines the database models for a batch"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

import django.contrib.postgres.fields
from django.db import connection, models, transaction
from django.db.models import F, Q
from django.utils.timezone import now

from batch.configuration.configuration import BatchConfiguration
from batch.configuration.json.configuration_v6 import convert_configuration_to_v6, BatchConfigurationV6
from batch.definition.exceptions import InvalidDefinition
from batch.definition.json.definition_v6 import convert_definition_to_v6, BatchDefinitionV6
from batch.exceptions import BatchError
from job.models import JobType
from messaging.manager import CommandMessageManager
from queue.models import Queue
from recipe.configuration.data.recipe_data import LegacyRecipeData
from recipe.diff.forced_nodes import ForcedNodes
from recipe.messages.create_recipes import create_reprocess_messages
from recipe.models import Recipe, RecipeType, RecipeTypeRevision
from storage.models import ScaleFile, Workspace
from trigger.models import TriggerEvent
from util import parse as parse_utils
from util import rest as rest_utils
from util.exceptions import ValidationException


logger = logging.getLogger(__name__)


BatchValidation = namedtuple('BatchValidation', ['is_valid', 'errors', 'warnings', 'batch'])


class BatchManager(models.Manager):
    """Provides additional methods for handling batches"""

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
        batch.recipe_type_rev = RecipeTypeRevision.objects.get_revision(recipe_type.name, recipe_type.revision_num)
        batch.event = event
        batch.definition = convert_definition_to_v6(definition).get_dict()
        batch.configuration = convert_configuration_to_v6(configuration).get_dict()

        with transaction.atomic():
            if definition.root_batch_id is not None:
                # Find latest batch with the root ID and supersede it
                try:
                    superseded_batch = Batch.objects.get_locked_batch_from_root(definition.root_batch_id)
                except Batch.DoesNotExist:
                    raise InvalidDefinition('PREV_BATCH_NOT_FOUND', 'No batch with that root ID exists')
                batch.root_batch_id = superseded_batch.root_batch_id
                batch.superseded_batch = superseded_batch
                self.supersede_batch(superseded_batch.id, now())

            definition.validate(batch)
            configuration.validate(batch)

            batch.recipes_estimated = definition.estimated_recipes
            batch.save()
            if batch.root_batch_id is None:  # Batches with no superseded batch are their own root
                batch.root_batch_id = batch.id
                Batch.objects.filter(id=batch.id).update(root_batch_id=batch.id)

            # Create models for batch metrics
            batch_metrics_models = []
            for job_name in recipe_type.get_definition().get_topological_order():
                batch_metrics_model = BatchMetrics()
                batch_metrics_model.batch_id = batch.id
                batch_metrics_model.job_name = job_name
                batch_metrics_models.append(batch_metrics_model)
            BatchMetrics.objects.bulk_create(batch_metrics_models)

        return batch
        
    def calculate_estimated_recipes(self, batch, definition):
        """Calculates the estimated number of recipes that will be created for this batch. 
        This number is calculated by:
        1. The number of existing recipes for the specific recipe type that are 
           not currently superseded
        2. The number of sub-recipes in the recipe
           These should be filtered if not changed/marked for re-run?
           
        """
        
        # If this is a previous batch, use the previous batch total
        if batch.superseded_batch:
            return batch.superseded_batch.recipes_total
        
        # No files defined to run on, so no recipes will be created
        if not definition.dataset:
            return 0

        #: The number of recipes are calculated based on the following:
        #      - If the dataset has a global parameter matching the input of the 
        #        recipe type, count the number of files in each dataset member
        #      - If the dataset has a parameter matching the input of the recipe
        #        type, count the number of files in each member that matches the parameter
        
        from data.interface.exceptions import InvalidInterfaceConnection
        from data.models import DataSet, DataSetMember, DataSetFile
        dataset = DataSet.objects.get(pk=definition.dataset)
        dataset_definition = dataset.get_definition()
        recipe_type = RecipeTypeRevision.objects.get_revision(name=batch.recipe_type.name, revision_num=batch.recipe_type_rev.revision_num).recipe_type

        # combine the parameters
        dataset_parameters = dataset_definition.global_parameters
        for param in dataset_definition.parameters.parameters:
            dataset_parameters.add_parameter(dataset_definition.parameters.parameters[param])
        
        try:
            recipe_type.get_definition().input_interface.validate_connection(dataset_parameters)
        except InvalidInterfaceConnection as ex:
            logger.info('DataSet parameters do not match the recipe inputs; no recipes will be created: %s' % unicode(ex))
            return 0
        
        recipe_inputs = recipe_type.get_definition().get_input_keys()

        # Base count of recipes are number of files in the dataset that match the recipe inputs
        files = DataSetFile.objects.get_files([dataset.id], recipe_inputs)
        num_files = len(files)
        
        from recipe.models import RecipeTypeSubLink
        estimated_recipes = num_files
        # If all nodes are forced:
        if definition.forced_nodes and definition.forced_nodes.all_nodes:
            # Count the number of sub-recipes
            subs_count = RecipeTypeSubLink.objects.count_subrecipes(batch.recipe_type_id, recurse=True)
            estimated_recipes += (num_files * subs_count)
                
        else:
            # Only count the sub-recipes nodes that are forced, or in the lineage of a forced node
            nodes = recipe_type.get_v6_definition_json()['nodes']
            subs = [node for node in nodes if nodes[node]['node_type']['node_type'] == 'recipe']
            
            for sub in subs:
                sub_type_id = RecipeType.objects.get(name=nodes[sub]['node_type']['recipe_type_name'], revision_num=nodes[sub]['node_type']['recipe_type_revision']).id
                
                # If sub-recipe is selected as a forced node
                if sub in definition.forced_nodes.get_sub_recipe_names():
                    estimated_recipes += (1 + RecipeTypeSubLink.objects.count_subrecipes(sub_type_id, recurse=True)) * num_files
                
                # If it's a child of a forced job node, we're going to need to run it
                else:
                    recipe_type_def = recipe_type.get_definition()
                    for job_node in definition.forced_nodes.get_forced_node_names():
                        if recipe_type_def.has_descendant(job_node, sub):
                            estimated_recipes += (1 + RecipeTypeSubLink.objects.count_subrecipes(sub_type_id, recurse=True)) * num_files
      
        return estimated_recipes

    def get_batch_from_root(self, root_batch_id):
        """Returns the latest (non-superseded) batch model with the given root batch ID. The returned model
        will have no related fields populated.

        :param root_batch_id: The root batch ID
        :type root_batch_id: int
        :returns: The batch model
        :rtype: :class:`batch.models.Batch`
        """

        return self.get(root_batch_id=root_batch_id, is_superseded=False)

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

    def get_batch_comparison_v6(self, root_batch_id):
        """Returns the batch metrics for the v6 batch comparison REST API

        :param root_batch_id: The root batch ID of the batches to compare
        :type root_batch_id: int
        :returns: The list of batches in the chain
        :rtype: list
        """

        from batch.serializers import BatchBaseSerializerV6

        batches = Batch.objects.filter(root_batch_id=root_batch_id).prefetch_related('metrics')
        batches = batches.defer('definition', 'configuration').order_by('id')

        batch_list = []
        job_metrics_dict = {}
        for batch in batches:
            batch_list.append(BatchBaseSerializerV6(batch).data)
            batch.batch_metrics_dict = {}
            for batch_metrics in batch.metrics.all():
                batch.batch_metrics_dict[batch_metrics.job_name] = batch_metrics
                if batch_metrics.job_name not in job_metrics_dict:
                    job_metrics = {'jobs_total': [], 'jobs_pending': [], 'jobs_blocked': [], 'jobs_queued': [],
                                   'jobs_running': [], 'jobs_failed': [], 'jobs_completed': [], 'jobs_canceled': [],
                                   'min_seed_duration': [], 'avg_seed_duration': [], 'max_seed_duration': [],
                                   'min_job_duration': [], 'avg_job_duration': [], 'max_job_duration': []}
                    job_metrics_dict[batch_metrics.job_name] = job_metrics
        metrics_dict = {'jobs_total': [], 'jobs_pending': [], 'jobs_blocked': [], 'jobs_queued': [], 'jobs_running': [],
                        'jobs_failed': [], 'jobs_completed': [], 'jobs_canceled': [], 'recipes_estimated': [],
                        'recipes_total': [], 'recipes_completed': [], 'job_metrics': job_metrics_dict}

        for batch in batches:
            metrics_dict['jobs_total'].append(batch.jobs_total)
            metrics_dict['jobs_pending'].append(batch.jobs_pending)
            metrics_dict['jobs_blocked'].append(batch.jobs_blocked)
            metrics_dict['jobs_queued'].append(batch.jobs_queued)
            metrics_dict['jobs_running'].append(batch.jobs_running)
            metrics_dict['jobs_failed'].append(batch.jobs_failed)
            metrics_dict['jobs_completed'].append(batch.jobs_completed)
            metrics_dict['jobs_canceled'].append(batch.jobs_canceled)
            metrics_dict['recipes_estimated'].append(batch.recipes_estimated)
            metrics_dict['recipes_total'].append(batch.recipes_total)
            metrics_dict['recipes_completed'].append(batch.recipes_completed)
            for job_name, job_metrics in job_metrics_dict.items():
                if job_name in batch.batch_metrics_dict:
                    batch_metrics = batch.batch_metrics_dict[job_name]
                    job_metrics['jobs_total'].append(batch_metrics.jobs_total)
                    job_metrics['jobs_pending'].append(batch_metrics.jobs_pending)
                    job_metrics['jobs_blocked'].append(batch_metrics.jobs_blocked)
                    job_metrics['jobs_queued'].append(batch_metrics.jobs_queued)
                    job_metrics['jobs_running'].append(batch_metrics.jobs_running)
                    job_metrics['jobs_failed'].append(batch_metrics.jobs_failed)
                    job_metrics['jobs_completed'].append(batch_metrics.jobs_completed)
                    job_metrics['jobs_canceled'].append(batch_metrics.jobs_canceled)
                    if batch_metrics.min_seed_duration is not None:
                        min_seed_duration = parse_utils.duration_to_string(batch_metrics.min_seed_duration)
                    else:
                        min_seed_duration = None
                    job_metrics['min_seed_duration'].append(min_seed_duration)
                    if batch_metrics.avg_seed_duration is not None:
                        avg_seed_duration = parse_utils.duration_to_string(batch_metrics.avg_seed_duration)
                    else:
                        avg_seed_duration = None
                    job_metrics['avg_seed_duration'].append(avg_seed_duration)
                    if batch_metrics.max_seed_duration is not None:
                        max_seed_duration = parse_utils.duration_to_string(batch_metrics.max_seed_duration)
                    else:
                        max_seed_duration = None
                    job_metrics['max_seed_duration'].append(max_seed_duration)
                    if batch_metrics.min_job_duration is not None:
                        min_job_duration = parse_utils.duration_to_string(batch_metrics.min_job_duration)
                    else:
                        min_job_duration = None
                    job_metrics['min_job_duration'].append(min_job_duration)
                    if batch_metrics.avg_job_duration is not None:
                        avg_job_duration = parse_utils.duration_to_string(batch_metrics.avg_job_duration)
                    else:
                        avg_job_duration = None
                    job_metrics['avg_job_duration'].append(avg_job_duration)
                    if batch_metrics.max_job_duration is not None:
                        max_job_duration = parse_utils.duration_to_string(batch_metrics.max_job_duration)
                    else:
                        max_job_duration = None
                    job_metrics['max_job_duration'].append(max_job_duration)
                else:
                    for metric_name in job_metrics:
                        job_metrics[metric_name].append(None)  # Batch does not have this job, fill in metrics with None

        return {'batches': batch_list, 'metrics': metrics_dict}

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

    def update_batch_metrics(self, batch_ids):
        """Updates the metrics for the batches with the given IDs

        :param batch_ids: The batch IDs
        :type batch_ids: list
        """

        if not batch_ids:
            return

        qry = 'UPDATE batch b SET recipes_total = s.recipes_total, recipes_completed = s.recipes_completed, '
        qry += 'jobs_total = s.jobs_total, jobs_pending = s.jobs_pending, jobs_blocked = s.jobs_blocked, '
        qry += 'jobs_queued = s.jobs_queued, jobs_running = s.jobs_running, jobs_failed = s.jobs_failed, '
        qry += 'jobs_completed = s.jobs_completed, jobs_canceled = s.jobs_canceled, last_modified = %s '
        qry += 'FROM (SELECT r.batch_id, COUNT(r.id) + SUM(r.sub_recipes_total) AS recipes_total, '
        qry += 'COUNT(r.id) FILTER(WHERE r.is_completed) + SUM(r.sub_recipes_completed) AS recipes_completed, '
        qry += 'SUM(r.jobs_total) AS jobs_total, SUM(r.jobs_pending) AS jobs_pending, '
        qry += 'SUM(r.jobs_blocked) AS jobs_blocked, SUM(r.jobs_queued) AS jobs_queued, '
        qry += 'SUM(r.jobs_running) AS jobs_running, SUM(r.jobs_failed) AS jobs_failed, '
        qry += 'SUM(r.jobs_completed) AS jobs_completed, SUM(r.jobs_canceled) AS jobs_canceled '
        qry += 'FROM recipe r WHERE r.batch_id IN %s AND r.recipe_id IS NULL GROUP BY r.batch_id) s '
        qry += 'WHERE b.id = s.batch_id'
        with connection.cursor() as cursor:
            cursor.execute(qry, [now(), tuple(batch_ids)])

        BatchMetrics.objects.update_batch_metrics_per_job(batch_ids)

    def validate_batch_v6(self, recipe_type, definition, configuration=None):
        """Validates the given recipe type, definition, and configuration for creating a new batch

        :param recipe_type: The type of recipes that will be created for this batch
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param definition: The definition for running the batch
        :type definition: :class:`batch.definition.definition.BatchDefinition`
        :param configuration: The batch configuration
        :type configuration: :class:`batch.configuration.configuration.BatchConfiguration`
        :returns: The batch validation
        :rtype: :class:`batch.models.BatchValidation`
        """

        is_valid = True
        errors = []
        warnings = []

        try:
            batch = Batch()
            batch.recipe_type = recipe_type
            batch.recipe_type_rev = RecipeTypeRevision.objects.get_revision(recipe_type.name, recipe_type.revision_num)
            batch.definition = convert_definition_to_v6(definition).get_dict()
            batch.configuration = convert_configuration_to_v6(configuration).get_dict()

            if definition.root_batch_id is not None:
                # Find latest batch with the root ID
                try:
                    superseded_batch = Batch.objects.get_batch_from_root(definition.root_batch_id)
                except Batch.DoesNotExist:
                    raise InvalidDefinition('PREV_BATCH_NOT_FOUND', 'No batch with that root ID exists')
                batch.root_batch_id = superseded_batch.root_batch_id
                batch.superseded_batch = superseded_batch

            warnings.extend(definition.validate(batch))
            warnings.extend(configuration.validate(batch))
        except ValidationException as ex:
            is_valid = False
            errors.append(ex.error)

        batch.recipes_estimated = definition.estimated_recipes
        return BatchValidation(is_valid, errors, warnings, batch)

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

    :keyword creator_job: The job that will create the batch recipes and jobs for processing
    :type creator_job: :class:`django.db.models.ForeignKey`

    :keyword definition: JSON definition for what is being processed by this batch
    :type definition: :class:`django.contrib.postgres.fields.JSONField`
    :keyword configuration: JSON configuration for running the batch
    :type configuration: :class:`django.contrib.postgres.fields.JSONField`
    :keyword is_creation_done: Indicates whether all of the recipes for the batch have been created (True)
    :type is_creation_done: :class:`django.db.models.BooleanField`

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
    :keyword recipes_estimated: The estimated count for all recipes (including sub-recipes) that will be created for the
        batch
    :type recipes_estimated: :class:`django.db.models.IntegerField`
    :keyword recipes_total: The total count for all recipes (including sub-recipes) within the batch
    :type recipes_total: :class:`django.db.models.IntegerField`
    :keyword recipes_completed: The count for all completed recipes (including sub-recipes) within the batch
    :type recipes_completed: :class:`django.db.models.IntegerField`

    :keyword created: When the batch was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword superseded: When this batch was superseded
    :type superseded: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the batch was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.TextField(blank=True, null=True)
    recipe_type = models.ForeignKey('recipe.RecipeType', on_delete=models.PROTECT)
    recipe_type_rev = models.ForeignKey('recipe.RecipeTypeRevision', on_delete=models.PROTECT)
    event = models.ForeignKey('trigger.TriggerEvent', on_delete=models.PROTECT)

    creator_job = models.ForeignKey('job.Job', related_name='batch_creator_job', blank=True, null=True,
                                    on_delete=models.PROTECT)

    definition = django.contrib.postgres.fields.JSONField(default=dict)
    configuration = django.contrib.postgres.fields.JSONField(default=dict)
    is_creation_done = models.BooleanField(default=False)

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
        qry += 'FROM (SELECT r.batch_id, rn.node_name, COUNT(j.id) AS jobs_total, '
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
        qry += 'FROM recipe_node rn JOIN job j ON rn.job_id = j.id JOIN recipe r ON rn.recipe_id = r.id '
        qry += 'LEFT OUTER JOIN job_exe_end je ON je.job_id = j.id AND je.exe_num = j.num_exes '
        qry += 'WHERE r.batch_id IN %s AND r.recipe_id IS NULL GROUP BY r.batch_id, rn.node_name) s '
        qry += 'WHERE bm.batch_id = s.batch_id AND bm.job_name = s.node_name'
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

    batch = models.ForeignKey('batch.Batch', related_name='metrics', on_delete=models.PROTECT)
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
