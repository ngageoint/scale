"""Defines the database models for recipes and recipe types"""
from __future__ import unicode_literals

import copy
import logging
from collections import namedtuple

import django.contrib.postgres.fields
from django.db import connection, models, transaction
from django.db.models import Q
from django.utils.timezone import now

from data.data.data import Data
from data.data.json.data_v1 import convert_data_to_v1_json
from data.data.json.data_v6 import convert_data_to_v6_json, DataV6
from data.interface.interface import Interface
from data.interface.parameter import FileParameter
from job.models import Job, JobType
from messaging.manager import CommandMessageManager
from recipe.configuration.definition.recipe_definition import LegacyRecipeDefinition
from recipe.configuration.json.recipe_config_v6 import convert_config_to_v6_json, RecipeConfigurationV6
from recipe.definition.definition import RecipeDefinition
from recipe.definition.json.definition_v1 import convert_recipe_definition_to_v1_json
from recipe.definition.json.definition_v6 import convert_recipe_definition_to_v6_json, RecipeDefinitionV6
from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition
from recipe.deprecation import RecipeDefinitionSunset, RecipeDataSunset
from recipe.diff.diff import RecipeDiff
from recipe.diff.json.diff_v6 import convert_recipe_diff_to_v6_json
from recipe.exceptions import CreateRecipeError, ReprocessError, SupersedeError
from recipe.handlers.handler import RecipeHandler
from recipe.instance.recipe import RecipeInstance
from recipe.instance.json.recipe_v6 import convert_recipe_to_v6_json, RecipeInstanceV6
from storage.models import ScaleFile, Workspace
from trigger.configuration.exceptions import InvalidTriggerType
from trigger.models import TriggerRule
from util import rest as rest_utils
from util.validation import ValidationWarning

logger = logging.getLogger(__name__)

RecipeNodeCopy = namedtuple('RecipeNodeCopy', ['superseded_recipe_id', 'recipe_id', 'node_names'])

RecipeNodeOutput = namedtuple('RecipeNodeOutput', ['node_name', 'node_type', 'id', 'output_data'])

RecipeTypeValidation = namedtuple('RecipeTypeValidation', ['is_valid', 'errors', 'warnings', 'diff'])

ForcedNodesValidation = namedtuple('ForcedNodesValidation', ['is_valid', 'errors', 'warnings', 'forced_nodes'])



INPUT_FILE_BATCH_SIZE = 500  # Maximum batch size for creating RecipeInputFile models

# IMPORTANT NOTE: Locking order
# Always adhere to the following model order for obtaining row locks via select_for_update() in order to prevent
# deadlocks and ensure query efficiency
# When editing a job/recipe type: RecipeType, JobType, TriggerRule


class RecipeManager(models.Manager):
    """Provides additional methods for handling recipes
    """

    def complete_recipes(self, recipe_ids, when):
        """Marks the recipes with the given IDs as being completed

        :param recipe_ids: The recipe IDs
        :type recipe_ids: list
        :param when: The time that the recipes were completed
        :type when: :class:`datetime.datetime`
        """

        qry = self.filter(id__in=recipe_ids, is_completed=False)
        qry.update(is_completed=True, completed=when, last_modified=now())

    # TODO: remove this in Scale v6 when the deprecated message reprocess_recipes is removed
    def create_recipe(self, recipe_type, revision, event_id, input, batch_id=None, superseded_recipe=None):
        """Creates a new recipe model for the given type and returns it. The model will not be saved in the database.
        :param recipe_type: The type of the recipe to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param revision: The recipe type revision
        :type revision: :class:`recipe.models.RecipeTypeRevision`
        :param event_id: The ID of the event that triggered the creation of this recipe
        :type event_id: int
        :param input: The recipe input to run on, should be None if superseded_recipe is provided
        :type input: :class:`recipe.data.recipe_data.RecipeData`
        :param batch_id: The ID of the batch that contains this recipe
        :type batch_id: int
        :param superseded_recipe: The recipe that the created recipe is superseding, possibly None
        :type superseded_recipe: :class:`recipe.models.Recipe`
        :returns: A handler for the new recipe
        :rtype: :class:`recipe.models.Recipe`
        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the recipe input is invalid
        """

        recipe = Recipe()
        recipe.recipe_type = recipe_type
        recipe.recipe_type_rev = revision
        recipe.event_id = event_id
        recipe.batch_id = batch_id
        recipe_definition = recipe.get_recipe_definition()

        if superseded_recipe:
            # Use input from superseded recipe
            input = superseded_recipe.get_recipe_data()

            # New recipe references superseded recipe
            root_id = superseded_recipe.root_superseded_recipe_id
            if root_id is None:
                root_id = superseded_recipe.id
            recipe.root_superseded_recipe_id = root_id
            recipe.superseded_recipe = superseded_recipe

        # Validate recipe input and save recipe
        recipe_definition.validate_data(input)
        recipe.input = input.get_dict()

        return recipe

    def create_recipe_v6(self, recipe_type_rev, event_id=None, ingest_id=None, input_data=None, root_recipe_id=None, recipe_id=None,
                         recipe_config=None, batch_id=None, superseded_recipe=None, copy_superseded_input=False):
        """Creates a new recipe for the given recipe type revision and returns the (unsaved) recipe model

        :param recipe_type_rev: The recipe type revision (with populated recipe_type model) of the recipe to create
        :type recipe_type_rev: :class:`recipe.models.RecipeTypeRevision`
        :param event_id: The event ID that triggered the creation of this recipe
        :type event_id: int
        :param ingest_id: The ingest event ID that triggered the creation of this recipe
        :type ingest_id: int
        :param input_data: The recipe's input data, possibly None
        :type input_data: :class:`data.data.data.Data`
        :param root_recipe_id: The ID of the root recipe that contains this sub-recipe, possibly None
        :type root_recipe_id: int
        :param recipe_id: The ID of the original recipe that created this sub-recipe, possibly None
        :type recipe_id: int
        :param batch_id: The ID of the batch that contains this recipe, possibly None
        :type batch_id: int
        :param recipe_config: The configuration for running this recipe, possibly None
        :type recipe_config: :class:`recipe.configuration.configuration.RecipeConfiguration`
        :param superseded_recipe: The recipe that the created recipe is superseding, possibly None
        :type superseded_recipe: :class:`recipe.models.Recipe`
        :param copy_superseded_input: Whether to copy the input data from the superseded recipe
        :type copy_superseded_input: bool
        :returns: The new recipe model
        :rtype: :class:`recipe.models.Recipe`

        :raises :class:`data.data.exceptions.InvalidData`: If the input data is invalid
        """

        recipe = Recipe()
        recipe.recipe_type = recipe_type_rev.recipe_type
        recipe.recipe_type_rev = recipe_type_rev
        recipe.event_id = event_id
        recipe.ingest_event_id = ingest_id
        recipe.root_recipe_id = root_recipe_id if root_recipe_id else recipe_id
        recipe.recipe_id = recipe_id
        recipe.batch_id = batch_id

        if recipe_config:
            recipe.configuration = convert_config_to_v6_json(recipe_config).get_dict()

        if superseded_recipe:
            root_id = superseded_recipe.root_superseded_recipe_id
            if not root_id:
                root_id = superseded_recipe.id
            recipe.root_superseded_recipe_id = root_id
            recipe.superseded_recipe = superseded_recipe

            if copy_superseded_input:
                input_data = superseded_recipe.get_input_data()

                # TODO: Remove when legacy recipes go away
                # get workspace ids from v1 data and pass them on to job configs so we don't lose them
                workspace_id = superseded_recipe.get_recipe_data().get_workspace_id()
                workspace = None
                try:
                    workspace = Workspace.objects.get(pk=workspace_id)
                except Workspace.DoesNotExist:
                    logger.exception('Could not copy workspace from superseded recipe. Workspace does not exist: %d', workspace_id)

                config = RecipeConfigurationV6(recipe.configuration)
                if workspace:
                    config.get_configuration().default_output_workspace = workspace.name
                    recipe.configuration = config.get_dict()

        if input_data:
            input_data.validate(recipe_type_rev.get_input_interface())
            recipe.input = convert_data_to_v6_json(input_data).get_dict()

        return recipe

    # TODO: remove this once it is no longer used
    @transaction.atomic
    def create_recipe_old(self, recipe_type, input, event, batch_id=None, superseded_recipe=None, delta=None,
                          superseded_jobs=None, priority=None):
        """Creates a new recipe for the given type and returns a recipe handler for it. All jobs for the recipe will
        also be created. If the new recipe is superseding an old recipe, superseded_recipe, delta, and superseded_jobs
        must be provided and the caller must have obtained a model lock on all job models in superseded_jobs and on the
        superseded_recipe model. All database changes occur in an atomic transaction.

        :param recipe_type: The type of the recipe to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param input: The recipe input to run on, should be None if superseded_recipe is provided
        :type input: :class:`recipe.data.recipe_data.RecipeData`
        :param event: The event that triggered the creation of this recipe
        :type event: :class:`trigger.models.TriggerEvent`
        :param batch_id: The ID of the batch that contains this recipe
        :type batch_id: int
        :param superseded_recipe: The recipe that the created recipe is superseding, possibly None
        :type superseded_recipe: :class:`recipe.models.Recipe`
        :param delta: If not None, represents the changes between the old recipe to supersede and the new recipe
        :type delta: :class:`recipe.handlers.graph_delta.RecipeGraphDelta`
        :param superseded_jobs: If not None, represents the job models (stored by job name) of the old recipe to
            supersede. This mapping must include all jobs created by the previous recipe, not just the ones that will
            actually be replaced by the new recipe definition.
        :type superseded_jobs: {string: :class:`job.models.Job`}
        :param priority: An optional argument to set the priority of the new recipe jobs
        :type priority: int
        :returns: A handler for the new recipe
        :rtype: :class:`recipe.handlers.handler.RecipeHandler`

        :raises :class:`recipe.exceptions.CreateRecipeError`: If general recipe parameters are invalid
        :raises :class:`recipe.exceptions.SupersedeError`: If the superseded parameters are invalid
        :raises :class:`recipe.exceptions.ReprocessError`: If recipe cannot be reprocessed
        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the recipe data is invalid
        """

        if not recipe_type.is_active:
            raise CreateRecipeError('Recipe type is no longer active')
        if event is None:
            raise CreateRecipeError('Event that triggered recipe creation is required')

        recipe = Recipe()
        recipe.recipe_type = recipe_type
        recipe.recipe_type_rev = RecipeTypeRevision.objects.get_revision(recipe_type.name, recipe_type.revision_num)
        recipe.event = event
        recipe.batch_id = batch_id
        recipe_definition = recipe.get_recipe_definition()
        when = now()

        if superseded_recipe:
            # Mark superseded recipe
            superseded_recipe.is_superseded = True
            superseded_recipe.superseded = when
            superseded_recipe.save()

            # Use data from superseded recipe
            input = superseded_recipe.get_recipe_data()
            if not delta:
                raise SupersedeError('Cannot supersede a recipe without delta')

            # New recipe references superseded recipe
            root_id = superseded_recipe.root_superseded_recipe_id
            if not root_id:
                root_id = superseded_recipe.id
            recipe.root_superseded_recipe_id = root_id
            recipe.superseded_recipe = superseded_recipe
        else:
            if delta:
                raise SupersedeError('delta must be provided with a superseded recipe')

        # Validate recipe data and save recipe
        recipe_definition.validate_data(input)
        recipe.input = input.get_dict()
        recipe.save()

        # Save models for each recipe input file
        recipe_files = []
        for input_file_info in input.get_input_file_info():
            recipe_file = RecipeInputFile()
            recipe_file.recipe_id = recipe.id
            recipe_file.input_file_id = input_file_info[0]
            recipe_file.recipe_input = input_file_info[1]
            recipe_file.created = recipe.created
            recipe_files.append(recipe_file)
        RecipeInputFile.objects.bulk_create(recipe_files)

        # Create recipe jobs and link them to the recipe
        recipe_jobs = self._create_recipe_jobs_old(batch_id, recipe, event, when, delta, superseded_jobs, priority)
        handler = RecipeHandler(recipe, recipe_jobs)
        # Block any new jobs that need to be blocked
        jobs_to_blocked = handler.get_blocked_jobs()
        if jobs_to_blocked:
            Job.objects.update_status(jobs_to_blocked, 'BLOCKED', when)
        return handler

    # TODO: remove this in Scale v6 when the deprecated message reprocess_recipes is removed
    def create_recipes_for_reprocess(self, recipe_type, revisions, superseded_recipes, event_id, batch_id=None):
        """Creates and returns new recipe models for reprocessing. The models will not be saved in the database.

        :param recipe_type: The type of the new recipes to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param revisions: A dict of recipe type revisions stored by revision ID
        :type revisions: dict
        :param superseded_recipes: The recipes that are being superseded
        :type superseded_recipes: list
        :param event_id: The ID of the event that triggered the reprocessing
        :type event_id: int
        :param batch_id: The ID of the batch for this reprocessing
        :type batch_id: int
        :returns: The new recipe models
        :rtype: list

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If a recipe input is invalid
        """

        recipes = []

        for superseded_recipe in superseded_recipes:
            revision = revisions[superseded_recipe.recipe_type_rev_id]
            recipe = self.create_recipe(recipe_type, revision, event_id, None, batch_id=batch_id,
                                        superseded_recipe=superseded_recipe)
            recipes.append(recipe)

        return recipes

    # TODO: remove this once it is no longer used
    def _create_recipe_jobs_old(self, batch_id, recipe, event, when, delta, superseded_jobs, priority=None):
        """Creates and returns the job and recipe_job models for the given new recipe. If the new recipe is superseding
        an old recipe, both delta and superseded_jobs must be provided and the caller must have obtained a model lock on
        all job models in superseded_jobs.

        :param batch_id: The ID of the batch that contains this recipe
        :type batch_id: int
        :param recipe: The new recipe
        :type recipe: :class:`recipe.models.Recipe`
        :param event: The event that triggered the creation of this recipe
        :type event: :class:`trigger.models.TriggerEvent`
        :param when: The time that the recipe was created
        :type when: :class:`datetime.datetime`
        :param delta: If not None, represents the changes between the old recipe to supersede and the new recipe
        :type delta: :class:`recipe.handlers.graph_delta.RecipeGraphDelta`
        :param superseded_jobs: If not None, represents the job models (stored by job name) of the old recipe to
            supersede. This mapping must include all jobs created by the previous recipe, not just the ones that will
            actually be replaced by the new recipe definition.
        :type superseded_jobs: {string: :class:`job.models.Job`}
        :param priority: An optional argument to set the priority of the new recipe jobs
        :type priority: int
        :returns: The list of newly created recipe_job models (without id field populated)
        :rtype: [:class:`recipe.models.RecipeNode`]

        :raises :class:`recipe.exceptions.ReprocessError`: If recipe cannot be reprocessed
        """

        recipe_jobs_to_create = []
        jobs_to_supersede = []
        for job_tuple in recipe.get_recipe_definition().get_jobs_to_create():
            job_name = job_tuple[0]
            job_type = job_tuple[1]
            superseded_job = None

            if delta:  # Look at changes from recipe we are superseding
                if not delta.can_be_reprocessed:
                    raise ReprocessError('Cannot reprocess recipe')
                if job_name in delta.get_identical_nodes():  # Identical jobs should be copied
                    copied_job = superseded_jobs[delta.get_identical_nodes()[job_name]]
                    recipe_job = RecipeNode()
                    recipe_job.job = copied_job
                    recipe_job.node_name = job_name
                    recipe_job.recipe = recipe
                    recipe_job.is_original = False
                    recipe_jobs_to_create.append(recipe_job)
                    continue  # Don't create a new job, just copy old one
                elif job_name in delta.get_changed_nodes():  # Changed jobs should be superseded
                    superseded_job = superseded_jobs[delta.get_changed_nodes()[job_name]]
                    jobs_to_supersede.append(superseded_job)

            job = Job.objects.create_job_old(job_type, event.id, root_recipe_id=recipe.root_superseded_recipe_id,
                                             recipe_id=recipe.id, batch_id=batch_id, superseded_job=superseded_job)
            if priority is not None:
                job.priority = priority
            job.save()
            recipe_job = RecipeNode()
            recipe_job.job = job
            recipe_job.node_name = job_name
            recipe_job.recipe = recipe
            recipe_jobs_to_create.append(recipe_job)

        if delta:
            # Go through deleted jobs, unpublish their products, and get ready to supersede them
            try:
                from product.models import ProductFile
            except ImportError:
                ProductFile = None
            for deleted_job_name in delta.get_deleted_nodes():
                deleted_job = superseded_jobs[deleted_job_name]
                jobs_to_supersede.append(deleted_job)
                root_job_id = deleted_job.root_superseded_job_id
                if not root_job_id:
                    root_job_id = deleted_job.id
                if ProductFile:
                    ProductFile.objects.unpublish_products_old(root_job_id, when)
        if jobs_to_supersede:
            # Supersede any jobs that were changed or deleted in new recipe
            Job.objects.supersede_jobs_old(jobs_to_supersede, when)

        RecipeNode.objects.bulk_create(recipe_jobs_to_create)
        return recipe_jobs_to_create

    # TODO: remove this in Scale v6 when the deprecated message update_recipes is removed
    def get_latest_recipe_ids_for_jobs(self, job_ids):
        """Returns the IDs of the latest (non-superseded) recipes that contain the jobs with the given IDs

        :param job_ids: The job IDs
        :type job_ids: list
        :returns: The recipe IDs
        :rtype: list
        """

        recipe_ids = set()
        # A job should match at most one non-superseded recipe
        for recipe_job in RecipeNode.objects.filter(job_id__in=job_ids, recipe__is_superseded=False).only('recipe_id'):
            recipe_ids.add(recipe_job.recipe_id)

        return list(recipe_ids)

    def get_locked_recipe(self, recipe_id):
        """Locks and returns the recipe model for the given ID with no related fields. Caller must be within an atomic
        transaction.

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :returns: The recipe model
        :rtype: :class:`recipe.models.Recipe`
        """

        return self.get_locked_recipes([recipe_id])[0]

    def get_locked_recipes(self, recipe_ids):
        """Locks and returns the recipe models for the given IDs with no related fields. Caller must be within an atomic
        transaction.

        :param recipe_ids: The recipe IDs
        :type recipe_ids: list
        :returns: The recipe models
        :rtype: list
        """

        # Recipe models are always locked in order of ascending ID to prevent deadlocks
        return list(self.select_for_update().filter(id__in=recipe_ids).order_by('id').iterator())

    def get_locked_recipes_from_root(self, root_recipe_ids):
        """Locks and returns the latest (non-superseded) recipe model for each recipe family with the given root recipe
        IDs. The returned models have no related fields populated. Caller must be within an atomic transaction.

        :param root_recipe_ids: The root recipe IDs
        :type root_recipe_ids: list
        :returns: The recipe models
        :rtype: list
        """

        root_recipe_ids = set(root_recipe_ids)  # Ensure no duplicates
        qry = self.select_for_update()
        qry = qry.filter(models.Q(id__in=root_recipe_ids) | models.Q(root_superseded_recipe_id__in=root_recipe_ids))
        qry = qry.filter(is_superseded=False)
        # Recipe models are always locked in order of ascending ID to prevent deadlocks
        return list(qry.order_by('id').iterator())

    # TODO: remove this in Scale v6 when the deprecated message reprocess_recipes is removed
    def get_locked_recipes_from_root_old(self, root_recipe_ids, event_id=None):
        """Locks and returns the latest (non-superseded) recipe model for each recipe family with the given root recipe
        IDs. The returned models have no related fields populated. Caller must be within an atomic transaction. The
        optional event ID ensures that recipes are not reprocessed multiple times due to one event.
        :param root_recipe_ids: The root recipe IDs
        :type root_recipe_ids: list
        :param event_id: The event ID
        :type event_id: int
        :returns: The recipe models
        :rtype: list
        """

        root_recipe_ids = set(root_recipe_ids)  # Ensure no duplicates
        qry = self.select_for_update()
        qry = qry.filter(models.Q(id__in=root_recipe_ids) | models.Q(root_superseded_recipe_id__in=root_recipe_ids))
        qry = qry.filter(is_superseded=False)
        if event_id is not None:
            qry = qry.exclude(event_id=event_id)  # Do not return recipes with this event ID
        # Recipe models are always locked in order of ascending ID to prevent deadlocks
        return list(qry.order_by('id').iterator())

    # TODO: remove this once database calls are no longer done in the post-task and this is not needed
    def get_recipe_for_job(self, job_id):
        """Returns the original recipe for the job with the given ID (returns None if the job is not in a recipe). The
        returned model will have its related recipe_type and recipe_type_rev models populated. If the job exists in
        multiple recipes due to superseding, the original (first) recipe is returned.

        :param job_id: The job ID
        :type job_id: int
        :returns: The recipe_job model with related recipe_type and recipe_type-rev, possibly None
        :rtype: :class:`recipe.models.RecipeNode`
        """

        recipe_job_qry = RecipeNode.objects.select_related('recipe__recipe_type', 'recipe__recipe_type_rev')
        try:
            recipe_job = recipe_job_qry.get(job_id=job_id, is_original=True)
        except RecipeNode.DoesNotExist:
            return None
        return recipe_job

    def get_recipe_ids_for_jobs(self, job_ids):
        """Returns the IDs of all recipes that contain the jobs with the given IDs. This will include superseded
        recipes.

        :param job_ids: The job IDs
        :type job_ids: list
        :returns: The recipe IDs
        :rtype: list
        """

        recipe_ids = set()
        for recipe_node in RecipeNode.objects.filter(job_id__in=job_ids).only('recipe_id'):
            recipe_ids.add(recipe_node.recipe_id)

        return list(recipe_ids)

    def get_recipe_ids_for_sub_recipes(self, sub_recipe_ids):
        """Returns the IDs of all recipes that contain the sub-recipes with the given IDs. This will include superseded
        recipes.

        :param sub_recipe_ids: The sub-recipe IDs
        :type sub_recipe_ids: list
        :returns: The recipe IDs
        :rtype: list
        """

        recipe_ids = set()
        for recipe_node in RecipeNode.objects.filter(sub_recipe_id__in=sub_recipe_ids).only('recipe_id'):
            recipe_ids.add(recipe_node.recipe_id)

        return list(recipe_ids)

    def get_recipe_instance(self, recipe_id):
        """Returns the recipe instance for the given recipe ID

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :returns: The recipe instance
        :rtype: :class:`recipe.instance.recipe.RecipeInstance`
        """

        recipe = Recipe.objects.select_related('recipe_type_rev').get(id=recipe_id)
        recipe_nodes = RecipeNode.objects.get_recipe_nodes(recipe_id)
        return RecipeInstance(recipe.recipe_type_rev.get_definition(), recipe, recipe_nodes)

    def get_recipe_instance_from_root(self, root_recipe_id):
        """Returns the non-superseded recipe instance for the given root recipe ID

        :param root_recipe_id: The root recipe ID
        :type root_recipe_id: int
        :returns: The recipe instance
        :rtype: :class:`recipe.instance.recipe.RecipeInstance`
        """

        qry = self.select_related('recipe_type_rev')
        qry = qry.filter(models.Q(id=root_recipe_id) | models.Q(root_superseded_recipe_id=root_recipe_id))
        recipe = qry.filter(is_superseded=False).order_by('-created').first()
        recipe_nodes = RecipeNode.objects.get_recipe_nodes(recipe.id)
        return RecipeInstance(recipe.recipe_type_rev.get_definition(), recipe, recipe_nodes)

    def get_recipe_with_interfaces(self, recipe_id):
        """Gets the recipe model for the given ID with related recipe_type_rev and recipe__recipe_type_rev models

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :returns: The recipe model with related recipe_type_rev and recipe__recipe_type_rev models
        :rtype: :class:`recipe.models.Recipe`
        """

        return self.select_related('recipe_type_rev', 'recipe__recipe_type_rev').get(id=recipe_id)

    def get_recipes_v5(self, started=None, ended=None, type_ids=None, type_names=None, batch_ids=None,
                    include_superseded=False, order=None):
        """Returns a list of recipes within the given time range.

        :param started: Query recipes updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query recipes updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param type_ids: Query recipes of the type associated with the identifier.
        :type type_ids: [int]
        :param type_names: Query recipes of the type associated with the name.
        :type type_names: [string]
        :param batch_ids: Query jobs associated with batches with the given identifiers.
        :type batch_ids: list[int]
        :param include_superseded: Whether to include recipes that are superseded.
        :type include_superseded: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of recipes that match the time range.
        :rtype: [:class:`recipe.models.Recipe`]
        """

        # Fetch a list of recipes
        recipes = Recipe.objects.all()
        recipes = recipes.select_related('recipe_type', 'recipe_type_rev', 'event',)
        recipes = recipes.defer('recipe_type__definition', 'recipe_type_rev__recipe_type',
                                'recipe_type_rev__definition')

        # Apply time range filtering
        if started:
            recipes = recipes.filter(last_modified__gte=started)
        if ended:
            recipes = recipes.filter(last_modified__lte=ended)

        # Apply type filtering
        if type_ids:
            recipes = recipes.filter(recipe_type_id__in=type_ids)
        if type_names:
            recipes = recipes.filter(recipe_type__name__in=type_names)

        # Apply batch filtering
        if batch_ids:
            recipes = recipes.filter(batch_id__in=batch_ids)

        # Apply additional filters
        if not include_superseded:
            recipes = recipes.filter(is_superseded=False)

        # Apply sorting
        if order:
            recipes = recipes.order_by(*order)
        else:
            recipes = recipes.order_by('last_modified')
        return recipes

    def get_recipes_v6(self, started=None, ended=None, source_started=None, source_ended=None,
                    source_sensor_classes=None, source_sensors=None, source_collections=None,
                    source_tasks=None, ids=None, type_ids=None, type_names=None, batch_ids=None,
                    is_superseded=None, is_completed=None, order=None):
        """Returns a list of recipes within the given time range.

        :param started: Query recipes updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query recipes updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param source_started: Query recipes where source collection started after this time.
        :type source_started: :class:`datetime.datetime`
        :param source_ended: Query recipes where source collection ended before this time.
        :type source_ended: :class:`datetime.datetime`
        :param source_sensor_classes: Query recipes with the given source sensor class.
        :type source_sensor_classes: list
        :param source_sensor: Query recipes with the given source sensor.
        :type source_sensor: list
        :param source_collection: Query recipes with the given source class.
        :type source_collection: list
        :param source_tasks: Query recipes with the given source tasks.
        :type source_tasks: list
        :param ids: Query recipes associated with the given identifiers.
        :type ids: [int]
        :param type_ids: Query recipes of the type associated with the identifiers.
        :type type_ids: [int]
        :param type_names: Query recipes of the type associated with the name.
        :type type_names: [string]
        :param batch_ids: Query recipes associated with batches with the given identifiers.
        :type batch_ids: list[int]
        :param is_superseded: Query recipes that match the is_superseded flag.
        :type is_superseded: bool
        :param is_completed: Query recipes that match the is_completed flag.
        :type is_completed: bool
        :param order: A list of fields to control the sort order.
        :type order: [string]
        :returns: The list of recipes that match the time range.
        :rtype: [:class:`recipe.models.Recipe`]
        """

        # Fetch a list of recipes
        recipes = Recipe.objects.all()
        recipes = recipes.select_related('recipe_type', 'recipe_type_rev', 'event', 'batch')
        recipes = recipes.defer('recipe_type__definition', 'recipe_type_rev__recipe_type',
                                'recipe_type_rev__definition')

        # Apply time range filtering
        if started:
            recipes = recipes.filter(last_modified__gte=started)
        if ended:
            recipes = recipes.filter(last_modified__lte=ended)

        if source_started:
            recipes = recipes.filter(source_started__gte=source_started)
        if source_ended:
            recipes = recipes.filter(source_ended__lte=source_ended)
        if source_sensor_classes:
            recipes = recipes.filter(source_sensor_class__in=source_sensor_classes)
        if source_sensors:
            recipes = recipes.filter(source_sensor__in=source_sensors)
        if source_collections:
            recipes = recipes.filter(source_collection__in=source_collections)
        if source_tasks:
            recipes = recipes.filter(source_task__in=source_tasks)

        if ids:
            recipes = recipes.filter(id__in=ids)

        # Apply type filtering
        if type_ids:
            recipes = recipes.filter(recipe_type_id__in=type_ids)
        if type_names:
            recipes = recipes.filter(recipe_type__name__in=type_names)

        # Apply batch filtering
        if batch_ids:
            recipes = recipes.filter(batch_id__in=batch_ids)

        # Apply additional filters
        if is_superseded is not None:
            recipes = recipes.filter(is_superseded=is_superseded)
        if is_completed is not None:
            recipes = recipes.filter(is_completed=is_completed)

        # Apply sorting
        if order:
            recipes = recipes.order_by(*order)
        else:
            recipes = recipes.order_by('last_modified')
        return recipes

    def get_details(self, recipe_id):
        """Gets the details for a given recipe including its associated jobs and input files.

        :param recipe_id: The unique identifier of the recipe to fetch.
        :type recipe_id: :int
        :returns: A recipe with additional information.
        :rtype: :class:`recipe.models.Recipe`
        """

        # Attempt to fetch the requested recipe
        recipe = Recipe.objects.select_related(
            'recipe_type_rev', 'event', 'batch', 'root_superseded_recipe',
            'root_superseded_recipe__recipe_type', 'superseded_recipe', 'superseded_recipe__recipe_type',
            'superseded_by_recipe', 'superseded_by_recipe__recipe_type'
        ).get(pk=recipe_id)

        # Update the recipe with job types and sub recipes
        jt_ids = RecipeTypeJobLink.objects.get_job_type_ids([recipe.recipe_type.id])
        recipe.job_types = JobType.objects.all().filter(id__in=jt_ids)
        sub_ids = RecipeTypeSubLink.objects.get_sub_recipe_type_ids([recipe.recipe_type.id])
        recipe.sub_recipe_types = RecipeType.objects.all().filter(id__in=sub_ids)
        return recipe

    # TODO: remove function when REST API v5 is removed
    def get_details_v5(self, recipe_id):
        """Gets the details for a given recipe including its associated jobs and input files.

        :param recipe_id: The unique identifier of the recipe to fetch.
        :type recipe_id: :int
        :returns: A recipe with additional information.
        :rtype: :class:`recipe.models.Recipe`
        """

        # Attempt to fetch the requested recipe
        recipe = Recipe.objects.select_related(
            'recipe_type', 'recipe_type_rev', 'event', 'event__rule', 'root_superseded_recipe',
            'root_superseded_recipe__recipe_type', 'superseded_recipe', 'superseded_recipe__recipe_type',
            'superseded_by_recipe', 'superseded_by_recipe__recipe_type'
        ).get(pk=recipe_id)

        # Update the recipe with source file models
        input_file_ids = []
        for file_value in recipe.get_input_data().values.values():
            if file_value.param_type != FileParameter.PARAM_TYPE:
                continue
            input_file_ids.extend(file_value.file_ids)
        input_files = ScaleFile.objects.filter(id__in=input_file_ids)
        input_files = input_files.select_related('workspace').defer('workspace__json_config')
        input_files = input_files.order_by('id').distinct('id')

        interface = recipe.recipe_type_rev.get_definition().input_interface
        recipe_def_dict = convert_recipe_definition_to_v1_json(recipe.recipe_type_rev.get_definition()).get_dict()
        recipe_data_dict = convert_data_to_v1_json(recipe.get_input_data(), interface).get_dict()
        recipe.inputs = self._merge_recipe_data(recipe_def_dict['input_data'], recipe_data_dict['input_data'],
                                                input_files)

        # Update the recipe with job models
        jobs = RecipeNode.objects.filter(recipe_id=recipe.id)
        jobs = jobs.select_related('job', 'job__job_type', 'job__event', 'job__error')
        recipe.jobs = jobs
        return recipe

    def process_recipe_input(self, recipe):
        """Processes the input data for the given recipe to populate its input file models and input meta-data fields.
        The caller must have obtained a model lock on the given recipe model.

        :param recipe: The locked recipe models
        :type recipe: :class:`recipe.models.Recipe`
        """

        if recipe.input_file_size is not None:
            return  # Recipe has already had its input processed

        # Create RecipeInputFile models in batches
        all_file_ids = set()
        input_file_models = []
        for file_value in recipe.get_input_data().values.values():
            if file_value.param_type != FileParameter.PARAM_TYPE:
                continue
            for file_id in file_value.file_ids:
                all_file_ids.add(file_id)
                recipe_input_file = RecipeInputFile()
                recipe_input_file.recipe_id = recipe.id
                recipe_input_file.input_file_id = file_id
                recipe_input_file.recipe_input = file_value.name
                input_file_models.append(recipe_input_file)
                if len(input_file_models) >= INPUT_FILE_BATCH_SIZE:
                    RecipeInputFile.objects.bulk_create(input_file_models)
                    input_file_models = []

        # Finish creating any remaining JobInputFile models
        if input_file_models:
            RecipeInputFile.objects.bulk_create(input_file_models)

        if len(all_file_ids) == 0:
            # If there are no input files, just zero out the file size and skip input meta-data fields
            self.filter(id=recipe.id).update(input_file_size=0.0)
            return

        # Set input meta-data fields on the recipe
        # Total input file size is in MiB rounded up to the nearest whole MiB
        qry = 'UPDATE recipe r SET input_file_size = CEILING(s.total_file_size / (1024.0 * 1024.0)), '
        qry += 'source_started = s.source_started, source_ended = s.source_ended, last_modified = %s, '
        qry += 'source_sensor_class = s.source_sensor_class, source_sensor = s.source_sensor, '
        qry += 'source_collection = s.source_collection, source_task = s.source_task FROM ('
        qry += 'SELECT rif.recipe_id, MIN(f.source_started) AS source_started, MAX(f.source_ended) AS source_ended, '
        qry += 'COALESCE(SUM(f.file_size), 0.0) AS total_file_size, '
        qry += 'MAX(f.source_sensor_class) AS source_sensor_class, '
        qry += 'MAX(f.source_sensor) AS source_sensor, '
        qry += 'MAX(f.source_collection) AS source_collection, '
        qry += 'MAX(f.source_task) AS source_task '
        qry += 'FROM scale_file f JOIN recipe_input_file rif ON f.id = rif.input_file_id '
        qry += 'WHERE rif.recipe_id = %s GROUP BY rif.recipe_id) s '
        qry += 'WHERE r.id = s.recipe_id'
        with connection.cursor() as cursor:
            cursor.execute(qry, [now(), recipe.id])

    def set_recipe_input_data_v6(self, recipe, input_data):
        """Sets the given input data as a v6 JSON for the given recipe. The recipe model must have its related
        recipe_type_rev model populated.

        :param recipe: The recipe model with related recipe_type_rev model
        :type recipe: :class:`recipe.models.Recipe`
        :param input_data: The input data for the recipe
        :type input_data: :class:`data.data.data.Data`

        :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
        """

        # TODO: remove when legacy trigger system is removed
        definition_version = recipe.recipe_type_rev.definition['version']

        recipe_definition = recipe.recipe_type_rev.get_definition()
        input_data.validate(recipe_definition.input_interface)
        input_dict = None

        # TODO: this code path supports passing output workspace ID in recipe data, remove when legacy trigger system is
        # removed
        config = None
        if definition_version == '1.0' and recipe.recipe:
            if 'workspace_id' in recipe.recipe.input:
                input_dict = convert_data_to_v1_json(input_data, recipe_definition.input_interface).get_dict()
                input_dict['workspace_id'] = recipe.recipe.input['workspace_id']

                # store workspace id in config so it isn't lost
                workspace_id = input_dict['workspace_id']
                workspace = None
                try:
                    workspace = Workspace.objects.get(pk=workspace_id)
                except Workspace.DoesNotExist:
                    logger.exception('Could not set workspace from input data. Workspace does not exist: %d', workspace_id)

                config = RecipeConfigurationV6(recipe.configuration)
                if workspace:
                    config.get_configuration().default_output_workspace = workspace.name
                    config = config.get_dict()

        if not input_dict:
            input_dict = convert_data_to_v6_json(input_data).get_dict()

        if config:
            self.filter(id=recipe.id).update(input=input_dict, configuration=config)
        else:
            self.filter(id=recipe.id).update(input=input_dict)

    def supersede_recipes(self, recipe_ids, when):
        """Updates the given recipes to be superseded

        :param recipe_ids: The recipe IDs to supersede
        :type recipe_ids: list
        :param when: The time that the recipes were superseded
        :type when: :class:`datetime.datetime`
        """

        qry = self.filter(id__in=recipe_ids, is_superseded=False)
        qry.update(is_superseded=True, superseded=when, last_modified=now())

    def update_recipe_metrics(self, recipe_ids):
        """Updates the metrics for the recipes with the given IDs

        :param recipe_ids: The recipe IDs
        :type recipe_ids: list
        """

        if not recipe_ids:
            return

        qry = 'UPDATE recipe r SET jobs_total = s.jobs_total, jobs_pending = s.jobs_pending, '
        qry += 'jobs_blocked = s.jobs_blocked, jobs_queued = s.jobs_queued, jobs_running = s.jobs_running, '
        qry += 'jobs_failed = s.jobs_failed, jobs_completed = s.jobs_completed, jobs_canceled = s.jobs_canceled, '
        qry += 'sub_recipes_total = s.sub_recipes_total, sub_recipes_completed = s.sub_recipes_completed, '
        qry += 'last_modified = %s FROM ('
        qry += 'SELECT rn.recipe_id, COUNT(j.id) + COALESCE(SUM(r.jobs_total), 0) AS jobs_total, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'PENDING\') + COALESCE(SUM(r.jobs_pending), 0) AS jobs_pending, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'BLOCKED\') + COALESCE(SUM(r.jobs_blocked), 0) AS jobs_blocked, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'QUEUED\') + COALESCE(SUM(r.jobs_queued), 0) AS jobs_queued, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'RUNNING\') + COALESCE(SUM(r.jobs_running), 0) AS jobs_running, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'FAILED\') + COALESCE(SUM(r.jobs_failed), 0) AS jobs_failed, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'COMPLETED\') '
        qry += '+ COALESCE(SUM(r.jobs_completed), 0) AS jobs_completed, '
        qry += 'COUNT(j.id) FILTER(WHERE status = \'CANCELED\') + COALESCE(SUM(r.jobs_canceled), 0) AS jobs_canceled, '
        qry += 'COUNT(r.id) + COALESCE(SUM(r.sub_recipes_total), 0) AS sub_recipes_total, '
        qry += 'COUNT(r.id) FILTER(WHERE r.is_completed) '
        qry += '+ COALESCE(SUM(r.sub_recipes_completed), 0) AS sub_recipes_completed '
        qry += 'FROM recipe_node rn LEFT OUTER JOIN job j ON rn.job_id = j.id '
        qry += 'LEFT OUTER JOIN recipe r ON rn.sub_recipe_id = r.id WHERE rn.recipe_id IN %s GROUP BY rn.recipe_id) s '
        qry += 'WHERE r.id = s.recipe_id'
        with connection.cursor() as cursor:
            cursor.execute(qry, [now(), tuple(recipe_ids)])

    # TODO: remove this function when REST API v5 is removed
    def _merge_recipe_data(self, recipe_definition_dict, recipe_data_dict, recipe_files):
        """Merges data for a single recipe instance with its recipe definition to produce a mapping of key/values.

        :param recipe_definition_dict: A dictionary representation of the recipe type definition.
        :type recipe_definition_dict: dict
        :param recipe_data_dict: A dictionary representation of the recipe instance data.
        :type recipe_data_dict: dict
        :param recipe_files: A list of files that are referenced by the recipe data.
        :type recipe_files: [:class:`storage.models.ScaleFile`]
        :return: A dictionary of each definition key mapped to the corresponding data value.
        :rtype: dict
        """

        # Setup the basic structure for merged results
        merged_dicts = copy.deepcopy(recipe_definition_dict)
        name_map = {merged_dict['name']: merged_dict for merged_dict in merged_dicts}
        file_map = {recipe_file.id: recipe_file for recipe_file in recipe_files}

        # Merge the recipe data with the definition attributes
        for data_dict in recipe_data_dict:
            value = None
            if 'value' in data_dict:
                value = data_dict['value']
            elif 'file_id' in data_dict:
                value = file_map[data_dict['file_id']]
            elif 'file_ids' in data_dict:
                value = [file_map[file_id] for file_id in data_dict['file_ids']]

            merged_dict = name_map[data_dict['name']]
            merged_dict['value'] = value
        return merged_dicts


class Recipe(models.Model):
    """Represents a recipe to be run on the cluster. A model lock must be obtained using select_for_update() on any
    recipe model before adding new jobs to it or superseding it.

    :keyword recipe_type: The type of this recipe
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword recipe_type_rev: The revision of the recipe type when this recipe was created
    :type recipe_type_rev: :class:`django.db.models.ForeignKey`
    :keyword event: The event that triggered the creation of this recipe
    :type event: :class:`django.db.models.ForeignKey`
    :keyword ingest_event: The ingest event that triggered the creation of this recipe
    :type ingest_event: :class:`django.db.models.ForeignKey`
    :keyword root_recipe: The root recipe that contains this recipe
    :type root_recipe: :class:`django.db.models.ForeignKey`
    :keyword recipe: The original recipe that created this recipe
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword batch: The batch that contains this recipe
    :type batch: :class:`django.db.models.ForeignKey`

    :keyword is_superseded: Whether this recipe has been superseded and is obsolete. This may be true while
        superseded_by_recipe (the reverse relationship of superseded_recipe) is null, indicating that this recipe is
        obsolete, but there is no new recipe that has directly taken its place.
    :type is_superseded: :class:`django.db.models.BooleanField`
    :keyword root_superseded_recipe: The first recipe in the chain of superseded recipes. This field will be null for
        the first recipe in the chain (i.e. recipes that have a null superseded_recipe field).
    :type root_superseded_recipe: :class:`django.db.models.ForeignKey`
    :keyword superseded_recipe: The recipe that was directly superseded by this recipe. The reverse relationship can be
        accessed using 'superseded_by_recipe'.
    :type superseded_recipe: :class:`django.db.models.ForeignKey`

    :keyword input: JSON description defining the input for this recipe
    :type input: :class:`django.contrib.postgres.fields.JSONField`
    :keyword input_file_size: The total size in MiB for all input files in this recipe
    :type input_file_size: :class:`django.db.models.FloatField`
    :keyword configuration: JSON describing the overriding recipe configuration for this recipe instance
    :type configuration: :class:`django.contrib.postgres.fields.JSONField`

    :keyword source_started: The start time of the source data for this recipe
    :type source_started: :class:`django.db.models.DateTimeField`
    :keyword source_ended: The end time of the source data for this recipe
    :type source_ended: :class:`django.db.models.DateTimeField`
    :keyword source_sensor_class: The class of sensor used to produce the source file for this recipe
    :type source_sensor_class: :class:`django.db.models.CharField`
    :keyword source_sensor: The specific identifier of the sensor used to produce the source file for this recipe
    :type source_sensor: :class:`django.db.models.CharField`
    :keyword source_collection: The collection of the source file for this recipe
    :type source_collection: :class:`django.db.models.CharField`
    :keyword source_task: The task that produced the source file for this recipe
    :type source_task: :class:`django.db.models.CharField`

    :keyword jobs_total: The total count of all jobs within this recipe
    :type jobs_total: :class:`django.db.models.IntegerField`
    :keyword jobs_pending: The count of all PENDING jobs within this recipe
    :type jobs_pending: :class:`django.db.models.IntegerField`
    :keyword jobs_blocked: The count of all BLOCKED jobs within this recipe
    :type jobs_blocked: :class:`django.db.models.IntegerField`
    :keyword jobs_queued: The count of all QUEUED jobs within this recipe
    :type jobs_queued: :class:`django.db.models.IntegerField`
    :keyword jobs_running: The count of all RUNNING jobs within this recipe
    :type jobs_running: :class:`django.db.models.IntegerField`
    :keyword jobs_failed: The count of all FAILED jobs within this recipe
    :type jobs_failed: :class:`django.db.models.IntegerField`
    :keyword jobs_completed: The count of all COMPLETED within this recipe
    :type jobs_completed: :class:`django.db.models.IntegerField`
    :keyword jobs_canceled: The count of all CANCELED jobs within this recipe
    :type jobs_canceled: :class:`django.db.models.IntegerField`
    :keyword sub_recipes_total: The total count for all sub-recipes within this recipe
    :type sub_recipes_total: :class:`django.db.models.IntegerField`
    :keyword sub_recipes_completed: The count for all completed sub-recipes within this recipe
    :type sub_recipes_completed: :class:`django.db.models.IntegerField`
    :keyword is_completed: Whether this recipe has completed all of its jobs
    :type is_completed: :class:`django.db.models.BooleanField`

    :keyword created: When the recipe was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword completed: When every job in the recipe was completed successfully
    :type completed: :class:`django.db.models.DateTimeField`
    :keyword superseded: When this recipe was superseded
    :type superseded: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the recipe was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    recipe_type = models.ForeignKey('recipe.RecipeType', on_delete=models.PROTECT)
    recipe_type_rev = models.ForeignKey('recipe.RecipeTypeRevision', on_delete=models.PROTECT)
    # TODO remove when triggers are removed for v6
    event = models.ForeignKey('trigger.TriggerEvent', blank=True, null=True, on_delete=models.PROTECT)
    ingest_event = models.ForeignKey('ingest.IngestEvent', blank=True, null=True, on_delete=models.PROTECT)
    root_recipe = models.ForeignKey('recipe.Recipe', related_name='sub_recipes_for_root', blank=True, null=True,
                                    on_delete=models.PROTECT)
    recipe = models.ForeignKey('recipe.Recipe', related_name='sub_recipes', blank=True, null=True,
                               on_delete=models.PROTECT)
    batch = models.ForeignKey('batch.Batch', related_name='recipes_for_batch', blank=True, null=True,
                              on_delete=models.PROTECT)

    is_superseded = models.BooleanField(default=False)
    root_superseded_recipe = models.ForeignKey('recipe.Recipe', related_name='superseded_by_recipes', blank=True,
                                               null=True, on_delete=models.PROTECT)
    superseded_recipe = models.OneToOneField('recipe.Recipe', related_name='superseded_by_recipe', blank=True,
                                             null=True, on_delete=models.PROTECT)

    input = django.contrib.postgres.fields.JSONField(default=dict)
    input_file_size = models.FloatField(blank=True, null=True)
    configuration = django.contrib.postgres.fields.JSONField(blank=True, null=True)

    # Supplemental sensor metadata fields
    source_started = models.DateTimeField(blank=True, null=True, db_index=True)
    source_ended = models.DateTimeField(blank=True, null=True, db_index=True)
    source_sensor_class = models.TextField(blank=True, null=True, db_index=True)
    source_sensor = models.TextField(blank=True, null=True, db_index=True)
    source_collection = models.TextField(blank=True, null=True, db_index=True)
    source_task = models.TextField(blank=True, null=True, db_index=True)

    # Metrics fields
    jobs_total = models.IntegerField(default=0)
    jobs_pending = models.IntegerField(default=0)
    jobs_blocked = models.IntegerField(default=0)
    jobs_queued = models.IntegerField(default=0)
    jobs_running = models.IntegerField(default=0)
    jobs_failed = models.IntegerField(default=0)
    jobs_completed = models.IntegerField(default=0)
    jobs_canceled = models.IntegerField(default=0)
    sub_recipes_total = models.IntegerField(default=0)
    sub_recipes_completed = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(blank=True, null=True)
    superseded = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = RecipeManager()

    def get_input_data(self):
        """Returns the input data for this recipe

        :returns: The input data for this recipe
        :rtype: :class:`data.data.data.Data`
        """

        return DataV6(data=self.input, do_validate=False).get_data()

    # TODO: deprecated in favor of get_input_data(), remove this when all uses of it have been removed
    def get_recipe_data(self):
        """Returns the data for this recipe

        :returns: The input for this recipe
        :rtype: :class:`recipe.configuration.data.recipe_data.LegacyRecipeData`
        """

        return RecipeDataSunset.create(self.get_recipe_definition(), self.input)

    # TODO: deprecated, remove in Scale v6 once the trigger system is gone
    def get_recipe_definition(self):
        """Returns the definition for this recipe

        :returns: The definition for this recipe
        :rtype: :class:`recipe.configuration.definition.recipe_definition_1_0.RecipeDefinition` or
                :class:`recipe.seed.recipe_definition.RecipeDefinition`
        """

        return RecipeDefinitionSunset.create(self.recipe_type_rev.definition)

    def get_v6_input_data_json(self):
        """Returns the input data for this recipe as v6 json with the version stripped

        :returns: The v6 JSON input data dict for this recipe
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_data_to_v6_json(self.get_input_data()).get_dict())

    def get_v6_recipe_instance_json(self):
        """Returns the recipe instance details as json

        :returns: The v6 JSON instance details dict for this recipe
        :rtype: dict
        """

        instance = Recipe.objects.get_recipe_instance(self.id)
        return rest_utils.strip_schema_version(convert_recipe_to_v6_json(instance).get_dict())

    def has_input(self):
        """Indicates whether this recipe has its input

        :returns: True if the recipe has its input, false otherwise.
        :rtype: bool
        """

        return True if self.input else False

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe'
        index_together = ['last_modified', 'recipe_type']


class RecipeConditionManager(models.Manager):
    """Provides additional methods for handling recipe conditions
    """

    def create_condition(self, recipe_id, root_recipe_id=None, batch_id=None):
        """Creates a new condition for the given recipe and returns the (unsaved) condition model

        :param recipe_id: The ID of the original recipe that created this condition, possibly None
        :type recipe_id: int
        :param root_recipe_id: The ID of the root recipe that contains this condition, possibly None
        :type root_recipe_id: int
        :param batch_id: The ID of the batch that contains this condition, possibly None
        :type batch_id: int
        :returns: The new condition model
        :rtype: :class:`recipe.models.RecipeCondition`
        """

        condition = RecipeCondition()
        condition.root_recipe_id = root_recipe_id if root_recipe_id else recipe_id
        condition.recipe_id = recipe_id
        condition.batch_id = batch_id

        return condition

    def get_condition_with_interfaces(self, condition_id):
        """Gets the condition model for the given ID with related recipe__recipe_type_rev model

        :param condition_id: The condition ID
        :type condition_id: int
        :returns: The condition model with related recipe__recipe_type_rev model
        :rtype: :class:`job.models.Job`
        """

        return self.select_related('recipe__recipe_type_rev').get(id=condition_id)

    def set_processed(self, condition_id, is_accepted):
        """Sets the condition with the given ID as being processed

        :param condition_id: The condition ID
        :type condition_id: int
        :param is_accepted: Whether the condition was accepted
        :type is_accepted: bool
        """

        self.filter(id=condition_id).update(is_processed=True, is_accepted=is_accepted, processed=now())

    def set_condition_data_v6(self, condition, data, node_name):
        """Sets the given data as a v6 JSON for the given condition. The condition model must have its related
        recipe__recipe_type_rev model populated.

        :param condition: The condition model with related recipe__recipe_type_rev model
        :type condition: :class:`recipe.models.RecipeCondition`
        :param data: The data for the condition
        :type data: :class:`data.data.data.Data`
        :param node_name: The name of the condition node in the recipe
        :type node_name: string

        :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
        """

        recipe_definition = condition.recipe.recipe_type_rev.get_definition()
        condition_interface = recipe_definition.graph[node_name].input_interface
        data.validate(condition_interface)

        data_dict = convert_data_to_v6_json(data).get_dict()
        self.filter(id=condition.id).update(data=data_dict)


class RecipeCondition(models.Model):
    """Represents a conditional decision within a recipe. If the condition is accepted then the dependent nodes will be
    created and processed, while if the condition is not accepted the dependent nodes will never be created.

    :keyword root_recipe: The root recipe that contains this condition
    :type root_recipe: :class:`django.db.models.ForeignKey`
    :keyword recipe: The original recipe that created this condition
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword batch: The batch that contains this condition
    :type batch: :class:`django.db.models.ForeignKey`

    :keyword data: JSON description defining the data processed by this condition
    :type data: :class:`django.contrib.postgres.fields.JSONField`
    :keyword is_processed: Whether the condition has been processed
    :type is_processed: :class:`django.db.models.BooleanField`
    :keyword is_accepted: Whether the condition has been accepted
    :type is_accepted: :class:`django.db.models.BooleanField`

    :keyword created: When this condition was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword processed: When this condition was processed
    :type processed: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the condition was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    root_recipe = models.ForeignKey('recipe.Recipe', related_name='conditions_for_root_recipe',
                                    on_delete=models.PROTECT)
    recipe = models.ForeignKey('recipe.Recipe', related_name='conditions_for_recipe', on_delete=models.PROTECT)
    batch = models.ForeignKey('batch.Batch', related_name='conditions_for_batch', blank=True, null=True,
                              on_delete=models.PROTECT)

    data = django.contrib.postgres.fields.JSONField(blank=True, null=True)
    is_processed = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    processed = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = RecipeConditionManager()

    def get_data(self):
        """Returns the data for this condition

        :returns: The data for this condition
        :rtype: :class:`data.data.data.Data`
        """

        return DataV6(data=self.data, do_validate=False).get_data()

    def has_data(self):
        """Indicates whether this condition has its data

        :returns: True if the condition has its data, false otherwise.
        :rtype: bool
        """

        return True if self.data else False

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_condition'


class RecipeInputFileManager(models.Manager):
    """Provides additional methods for handleing RecipeInputFiles"""

    # TODO: remove this when REST API v5 is removed
    def get_recipe_input_files(self, recipe_id, started=None, ended=None, time_field=None, file_name=None,
                               recipe_input=None):
        """Returns a query for Input Files filtered on the given fields.

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :param started: Query Scale files updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query Scale files updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :keyword time_field: The time field to use for filtering.
        :type time_field: string
        :param file_name: Query Scale files with the given file name.
        :type file_name: str
        :param recipe_input: The name of the recipe input that the file was passed into
        :type recipe_input: str
        :returns: The Scale file query
        :rtype: :class:`django.db.models.QuerySet`
        """

        files = ScaleFile.objects.filter_files_v5(started=started, ended=ended, time_field=time_field,
                                               file_name=file_name)

        files = files.filter(recipeinputfile__recipe=recipe_id).order_by('last_modified')

        if recipe_input:
            files = files.filter(recipeinputfile__recipe_input=recipe_input)

        # Reach back to the recipe_data to get input_file data for legacy recipes
        if not files:
            recipe_data = Recipe.objects.get(pk=recipe_id).get_recipe_data()
            recipe_input_files = recipe_data.get_input_file_info()

            if recipe_input:
                recipe_input_file_ids = [f_id for f_id, name in recipe_input_files if name == recipe_input]
            else:
                recipe_input_file_ids = [f_id for f_id, name in recipe_input_files]

            files = ScaleFile.objects.filter_files_v5(started=started, ended=ended, time_field=time_field,
                                                    file_name=file_name)

            files = files.filter(id__in=recipe_input_file_ids).order_by('last_modified')

        return files



class RecipeInputFile(models.Model):
    """Links a recipe and its input files together. A file can be used as input to multiple recipes and a recipe can
    accept multiple input files. This model is useful for determining relevant recipes to run during re-processing.

    :keyword recipe: The recipe that the input file is linked to
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword scale_file: The input file that the recipe is linked to
    :type scale_file: :class:`django.db.models.ForeignKey`
    :keyword recipe_input: The name of the recipe input parameter
    :type recipe_input: :class:`django.db.models.CharField`
    :keyword created: When the recipe was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    recipe = models.ForeignKey('recipe.Recipe', on_delete=models.PROTECT)
    input_file = models.ForeignKey('storage.ScaleFile', on_delete=models.PROTECT)
    recipe_input = models.CharField(blank=True, null=True, max_length=250)
    created = models.DateTimeField(auto_now_add=True)

    objects = RecipeInputFileManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_input_file'


class RecipeNodeManager(models.Manager):
    """Provides additional methods for handling jobs linked to a recipe
    """

    def copy_recipe_nodes(self, recipe_copies):
        """Copies the given nodes from the superseded recipes to the new recipes

        :param recipe_copies: A list of RecipeNodeCopy tuples
        :type recipe_copies: list
        """

        if not recipe_copies:
            return

        sub_queries = []
        for recipe_copy in recipe_copies:
            superseded_recipe_id = recipe_copy.superseded_recipe_id
            recipe_id = recipe_copy.recipe_id
            node_names = recipe_copy.node_names
            sub_qry = 'SELECT node_name, false, %d, condition_id, job_id, sub_recipe_id '
            sub_qry += 'FROM recipe_node WHERE recipe_id = %d'
            sub_qry = sub_qry % (recipe_id, superseded_recipe_id)
            if node_names:
                node_sub_qry = ', '.join('\'%s\'' % node_name for node_name in node_names)
                sub_qry = '%s AND node_name IN (%s)' % (sub_qry, node_sub_qry)
            sub_queries.append(sub_qry)
        union_sub_qry = ' UNION ALL '.join(sub_queries)
        qry = 'INSERT INTO recipe_node (node_name, is_original, recipe_id, condition_id, job_id, sub_recipe_id) %s'
        qry = qry % union_sub_qry

        with connection.cursor() as cursor:
            cursor.execute(qry)

    def create_recipe_condition_nodes(self, recipe_id, conditions):
        """Creates and returns the recipe node models (unsaved) for the given recipe and conditions

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :param conditions: A dict of condition models stored by node name
        :type conditions: dict
        :returns: The list of recipe_node models
        :rtype: list
        """

        node_models = []

        for node_name, condition in conditions.items():
            recipe_node = RecipeNode()
            recipe_node.recipe_id = recipe_id
            recipe_node.node_name = node_name
            recipe_node.condition = condition
            node_models.append(recipe_node)

        return node_models

    def create_recipe_job_nodes(self, recipe_id, recipe_jobs):
        """Creates and returns the recipe node models (unsaved) for the given recipe and jobs

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :param recipe_jobs: A dict of job models stored by node name
        :type recipe_jobs: dict
        :returns: The list of recipe_node models
        :rtype: list
        """

        node_models = []

        for node_name, job in recipe_jobs.items():
            recipe_node = RecipeNode()
            recipe_node.recipe_id = recipe_id
            recipe_node.node_name = node_name
            recipe_node.job = job
            node_models.append(recipe_node)

        return node_models

    def create_subrecipe_nodes(self, recipe_id, sub_recipes):
        """Creates and returns the recipe node models (unsaved) for the given recipe and sub-recipes

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :param sub_recipes: A dict of recipe models stored by node name
        :type sub_recipes: dict
        :returns: The list of recipe_node models
        :rtype: list
        """

        node_models = []

        for node_name, sub_recipe in sub_recipes.items():
            recipe_node = RecipeNode()
            recipe_node.recipe_id = recipe_id
            recipe_node.node_name = node_name
            recipe_node.sub_recipe = sub_recipe
            node_models.append(recipe_node)

        return node_models

    # TODO: remove this in Scale v6 when the deprecated message reprocess_recipes is removed
    def get_recipe_job_ids(self, recipe_ids):
        """Returns a dict where each given recipe ID maps to another dict that maps job_name for the recipe to a list of
        the job IDs

        :param recipe_ids: The recipe IDs
        :type recipe_ids: list
        :returns: Dict where each given recipe ID maps to another dict that maps job_name for the recipe to a list of
            the job IDs
        :rtype: dict
        """

        recipe_job_ids = {}  # {Recipe ID: {Job Name: [Job ID]}}

        for recipe_job in self.filter(recipe_id__in=recipe_ids).iterator():
            if recipe_job.recipe_id in recipe_job_ids:
                job_dict = recipe_job_ids[recipe_job.recipe_id]
            else:
                job_dict = {}
                recipe_job_ids[recipe_job.recipe_id] = job_dict
            if recipe_job.node_name in job_dict:
                job_dict[recipe_job.node_name].append(recipe_job.job_id)
            else:
                job_dict[recipe_job.node_name] = [recipe_job.job_id]

        return recipe_job_ids

    def get_recipe_jobs(self, recipe_id):
        """Returns the job models that belong to the given recipe

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :returns: A dict of job models stored by node name
        :rtype: dict
        """

        qry = self.select_related('job').filter(recipe_id=recipe_id, job__isnull=False)
        return {rn.node_name: rn.job for rn in qry}

    def get_recipe_nodes(self, recipe_id):
        """Returns the recipe_node models with related condition, job, and sub_recipe models for the given recipe ID

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :returns: The recipe_node models for the recipe
        :rtype: list
        """

        return self.filter(recipe_id=recipe_id).select_related('sub_recipe', 'job', 'condition')

    def get_recipe_node_outputs(self, recipe_id):
        """Returns the output data for each recipe node for the given recipe ID

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :returns: The RecipeNodeOutput tuples stored in a dict by node name
        :rtype: dict
        """

        node_outputs = {}

        qry = self.filter(recipe_id=recipe_id).select_related('sub_recipe', 'job', 'condition')
        for node in qry.only('node_name', 'condition', 'job', 'sub_recipe', 'condition__data', 'job__output'):
            node_type = None
            if node.condition:
                node_type = 'condition'
                node_id = node.condition_id
                output_data = node.condition.get_data()
            if node.job:
                node_type = 'job'
                node_id = node.job_id
                output_data = node.job.get_output_data()
            if node.sub_recipe:
                node_type = 'recipe'
                node_id = node.sub_recipe_id
                output_data = Data()  # Recipe output is currently not supported
            if node_type:
                node_outputs[node.node_name] = RecipeNodeOutput(node.node_name, node_type, node_id, output_data)

        return node_outputs

    def get_subrecipes(self, recipe_id):
        """Returns the sub-recipe models that belong to the given recipe

        :param recipe_id: The recipe ID
        :type recipe_id: int
        :returns: A dict of recipe models stored by node name
        :rtype: dict
        """

        qry = self.select_related('sub_recipe').filter(recipe_id=recipe_id, sub_recipe__isnull=False)
        return {rn.node_name: rn.sub_recipe for rn in qry}

    def supersede_recipe_jobs(self, recipe_ids, when, node_names, all_nodes=False):
        """Supersedes the jobs for the given recipe IDs and node names

        :param recipe_ids: The recipe IDs
        :type recipe_ids: list
        :param when: The time that the jobs were superseded
        :type when: :class:`datetime.datetime`
        :param node_names: The node names of the jobs to supersede
        :type node_names: list
        :param all_nodes: Whether all nodes should be superseded
        :type all_nodes: bool
        """

        if all_nodes:
            qry = Job.objects.filter(recipenode__recipe_id__in=recipe_ids)
        else:
            qry = Job.objects.filter(recipenode__recipe_id__in=recipe_ids, recipenode__node_name__in=node_names)
        qry.filter(is_superseded=False).update(is_superseded=True, superseded=when, last_modified=now())

    def supersede_subrecipes(self, recipe_ids, when, node_names, all_nodes=False):
        """Supersedes the sub-recipes for the given recipe IDs and node names

        :param recipe_ids: The recipe IDs
        :type recipe_ids: list
        :param when: The time that the sub-recipes were superseded
        :type when: :class:`datetime.datetime`
        :param node_names: The node names of the sub-recipes to supersede
        :type node_names: list
        :param all_nodes: Whether all nodes should be superseded
        :type all_nodes: bool
        """

        if all_nodes:
            qry = Recipe.objects.filter(contained_by__recipe_id__in=recipe_ids)
        else:
            qry = Recipe.objects.filter(contained_by__recipe_id__in=recipe_ids, contained_by__node_name__in=node_names)
        qry.filter(is_superseded=False).update(is_superseded=True, superseded=when, last_modified=now())


class RecipeNode(models.Model):
    """Links a recipe with a node within that recipe. Nodes within a recipe may represent either a job or another
    recipe. The same node may exist in multiple recipes due to superseding. For an original node and recipe combination,
    the is_original flag is True. When recipe B supersedes recipe A, the non-superseded nodes from recipe A that are
    being copied to recipe B will have models with is_original set to False.

    :keyword recipe: The recipe that contains the node
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword node_name: The unique name of the node within the recipe
    :type node_name: :class:`django.db.models.CharField`
    :keyword is_original: Whether this is the original recipe for the node (True) or the node is copied from a
        superseded recipe (False)
    :type is_original: :class:`django.db.models.BooleanField`
    :keyword condition: If not null, this node is a condition node and this field is the condition within the recipe
    :type condition: :class:`django.db.models.ForeignKey`
    :keyword job: If not null, this node is a job node and this field is the job that the recipe contains
    :type job: :class:`django.db.models.ForeignKey`
    :keyword sub_recipe: If not null, this node is a recipe node and this field is the sub-recipe that the recipe
        contains
    :type sub_recipe: :class:`django.db.models.ForeignKey`
    """

    recipe = models.ForeignKey('recipe.Recipe', related_name='contains', on_delete=models.PROTECT)
    node_name = models.CharField(max_length=100)
    is_original = models.BooleanField(default=True)
    condition = models.ForeignKey('recipe.RecipeCondition', blank=True, null=True, on_delete=models.PROTECT)
    job = models.ForeignKey('job.Job', blank=True, null=True, on_delete=models.PROTECT)
    sub_recipe = models.ForeignKey('recipe.Recipe', related_name='contained_by', blank=True, null=True,
                                   on_delete=models.PROTECT)

    objects = RecipeNodeManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_node'


class RecipeTypeManager(models.Manager):
    """Provides additional methods for handling recipe types
    """

    @transaction.atomic
    def create_recipe_type_v5(self, name, version, title, description, definition, trigger_rule=None):
        """Creates a new recipe type and saves it in the database. All database changes occur in an atomic transaction.

        :param name: The system name of the recipe type
        :type name: str
        :param version: The version of the recipe type
        :type version: str
        :param title: The human-readable name of the recipe type
        :type title: str
        :param description: An optional description of the recipe type
        :type description: str
        :param definition: The definition for running a recipe of this type
        :type definition: :class:`recipe.configuration.definition.recipe_definition.RecipeDefinition`
        :param trigger_rule: The trigger rule that creates recipes of this type
        :type trigger_rule: :class:`trigger.models.TriggerRule`
        :returns: The new recipe type
        :rtype: :class:`recipe.models.RecipeType`

        :raises :class:`recipe.configuration.definition.exceptions.InvalidDefinition`: If any part of the recipe
            definition violates the specification
        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeConnection`: If the trigger rule connection to
            the recipe type definition is invalid
        """

        from recipe.configuration.definition.exceptions import InvalidDefinition
        # Must lock job type interfaces so the new recipe type definition can be validated
        if isinstance(definition, LegacyRecipeDefinition):
            _ = definition.get_job_types(lock=True)
            definition.validate_job_interfaces()
        else:
            raise InvalidDefinition('INVALID_DEFINITION', 'This version of the recipe definition is invalid to save')

        # Create the new recipe type
        recipe_type = RecipeType()
        recipe_type.name = name
        recipe_type.version = version
        recipe_type.title = title
        recipe_type.description = description
        if definition.get_dict()['version'] == '2.0':
            raise InvalidDefinition('INVALID_DEFINITION', 'This version of the recipe definition is invalid to save')
        recipe_type.definition = definition.get_dict()
        recipe_type.save()

        # Create first revision of the recipe type
        RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)

        RecipeTypeJobLink.objects.create_recipe_type_job_links_from_definition(recipe_type)
        RecipeTypeSubLink.objects.create_recipe_type_sub_links_from_definition(recipe_type)

        return recipe_type

    def create_recipe_type_v6(self, name, title, description, definition):
        """Creates a new recipe type and saves it in the database. All database changes occur in an atomic transaction.

        :param name: The system name of the recipe type
        :type name: str
        :param title: The human-readable name of the recipe type
        :type title: str
        :param description: An optional description of the recipe type
        :type description: str
        :param definition: The definition for running a recipe of this type
        :type definition: :class:`recipe.definition.definition.RecipeDefinition`
        :returns: The new recipe type
        :rtype: :class:`recipe.models.RecipeType`

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If any part of the recipe
            definition violates the specification
        """

        from recipe.definition.exceptions import InvalidDefinition
        if isinstance(definition, RecipeDefinition):
            inputs, outputs = self.get_interfaces(definition)
            definition.validate(inputs, outputs)
        else:
            raise InvalidDefinition('INVALID_DEFINITION', 'This version of the recipe definition is invalid to save')


        # Create the new recipe type
        recipe_type = RecipeType()
        recipe_type.name = name
        recipe_type.title = title
        recipe_type.description = description
        recipe_type.definition = convert_recipe_definition_to_v6_json(definition).get_dict()
        recipe_type.save()

        # Create first revision of the recipe type
        RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)

        RecipeTypeJobLink.objects.create_recipe_type_job_links_from_definition(recipe_type)
        RecipeTypeSubLink.objects.create_recipe_type_sub_links_from_definition(recipe_type)

        return recipe_type

    @transaction.atomic
    def edit_recipe_type_v5(self, recipe_type_id, title, description, definition, trigger_rule=None, remove_trigger_rule=False):
        """Edits the given recipe type and saves the changes in the database. The caller must provide the related
        trigger_rule model. All database changes occur in an atomic transaction. An argument of None for a field
        indicates that the field should not change. The remove_trigger_rule parameter indicates the difference between
        no change to the trigger rule (False) and removing the trigger rule (True) when trigger_rule is None.

        :param recipe_type_id: The unique identifier of the recipe type to edit
        :type recipe_type_id: int
        :param title: The human-readable name of the recipe type, possibly None
        :type title: str
        :param description: A description of the recipe type, possibly None
        :type description: str
        :param definition: The definition for running a recipe of this type, possibly None
        :type definition: :class:`recipe.configuration.definition.recipe_definition.RecipeDefinition`
        :param trigger_rule: The trigger rule that creates recipes of this type, possibly None
        :type trigger_rule: :class:`trigger.models.TriggerRule`
        :param remove_trigger_rule: Indicates whether the trigger rule should be unchanged (False) or removed (True)
            when trigger_rule is None
        :type remove_trigger_rule: bool

        :raises :class:`recipe.configuration.definition.exceptions.InvalidDefinition`: If any part of the recipe
            definition violates the specification
        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeConnection`: If the trigger rule connection to
            the recipe type definition is invalid
        """

        from recipe.configuration.definition.exceptions import InvalidDefinition

        # Acquire model lock
        recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type_id)

        if title is not None:
            recipe_type.title = title

        if description is not None:
            recipe_type.description = description

        if definition:
            # Must lock job type interfaces so the new recipe type definition can be validated
            _ = definition.get_job_types(lock=True)
            if isinstance(definition, LegacyRecipeDefinition):
                definition.validate_job_interfaces()
                if definition.get_dict()['version'] == '2.0':
                    raise InvalidDefinition('INVALID_DEFINITION', 'This version of the recipe definition is invalid to save')
                recipe_type.definition = definition.get_dict()
            else:
                raise InvalidDefinition('INVALID_DEFINITION', 'This version of the recipe definition is invalid to save')
            recipe_type.revision_num = recipe_type.revision_num + 1

        recipe_type.save()

        if definition:
            # Create new revision of the recipe type for new definition
            RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)
            RecipeTypeJobLink.objects.create_recipe_type_job_links_from_definition(recipe_type)
            RecipeTypeSubLink.objects.create_recipe_type_sub_links_from_definition(recipe_type)

    def edit_recipe_type_v6(self, recipe_type_id, title, description, definition, auto_update):
        """Edits the given recipe type and saves the changes in the database.  All database changes occur in an atomic
        transaction. An argument of None for a field indicates that the field should not change.

        :param recipe_type_id: The unique identifier of the recipe type to edit
        :type recipe_type_id: int
        :param title: The human-readable name of the recipe type, possibly None
        :type title: str
        :param description: A description of the recipe type, possibly None
        :type description: str
        :param definition: The definition for running a recipe of this type, possibly None
        :type definition: :class:`recipe.definition.definition.RecipeDefinition`
        :param auto_update: If true, recipes that contain this recipe type will automatically be updated
        :type auto_update: bool

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If any part of the recipe
            definition violates the specification
        """

        from recipe.definition.exceptions import InvalidDefinition
        from recipe.messages.update_recipe_definition import create_sub_update_recipe_definition_message

        # Acquire model lock
        recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type_id)

        if title is not None:
            recipe_type.title = title

        if description is not None:
            recipe_type.description = description

        if definition:
            if isinstance(definition, RecipeDefinition):
                inputs, outputs = self.get_interfaces(definition)
                definition.validate(inputs, outputs)
                recipe_type.definition = convert_recipe_definition_to_v6_json(definition).get_dict()
            else:
                raise InvalidDefinition('INVALID_DEFINITION', 'This version of the recipe definition is invalid to save')
            recipe_type.revision_num = recipe_type.revision_num + 1

        recipe_type.save()

        if definition:
            # Create new revision of the recipe type for new definition
            RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)

            RecipeTypeJobLink.objects.create_recipe_type_job_links_from_definition(recipe_type)
            RecipeTypeSubLink.objects.create_recipe_type_sub_links_from_definition(recipe_type)

            if auto_update:
                super_ids = RecipeTypeSubLink.objects.get_recipe_type_ids([recipe_type.id])
                msgs = [create_sub_update_recipe_definition_message(id, recipe_type.id) for id in super_ids]
                CommandMessageManager().send_messages(msgs)

    def get_by_natural_key(self, name, version):
        """Django method to retrieve a recipe type for the given natural key

        :param name: The human-readable name of the recipe type
        :type name: string
        :returns: The recipe type defined by the natural key
        :rtype: :class:`recipe.models.RecipeType`
        """

        return self.get(name=name, version=version)

    def get_details_v5(self, recipe_type_id):
        """Gets additional details for the given recipe type model based on related model attributes.

        The additional fields include: job_types.

        :param recipe_type_id: The unique identifier of the recipe type.
        :type recipe_type_id: int
        :returns: The recipe type with extra related attributes.
        :rtype: :class:`recipe.models.RecipeType`
        """

        # Attempt to fetch the requested recipe type
        recipe_type = RecipeType.objects.select_related('trigger_rule').get(pk=recipe_type_id)

        # Add associated job type information
        if RecipeDefinitionSunset.is_seed_dict(recipe_type.definition):
            # possible to have a v6 definition through a v5 call. Need to get the
            # job types differently since the v6 RecipeDefinition doesn't have a
            # get_job_types method
            job_types = []
            for job in recipe_type.get_recipe_definition().get_job_type_keys():
                job_types.append(JobType.objects.get_by_natural_key(name=job.name, version=job.version))
            recipe_type.job_types = set(job_types)
        else:
            recipe_type.job_types = recipe_type.get_recipe_definition().get_job_types()
        return recipe_type

    def get_details_v6(self, name):
        """Gets additional details for the given recipe type model based on related model attributes.

        The additional fields include: job_types, sub_recipe_types.

        :param name: The unique recipe type name.
        :type name: string
        :returns: The recipe type with extra related attributes.
        :rtype: :class:`recipe.models.RecipeType`
        """

        # Attempt to fetch the requested recipe type
        recipe_type = RecipeType.objects.all().get(name=name)

        # Add associated job type information
        jt_ids = RecipeTypeJobLink.objects.get_job_type_ids([recipe_type.id])
        recipe_type.job_types = JobType.objects.all().filter(id__in=jt_ids)
        sub_ids = RecipeTypeSubLink.objects.get_sub_recipe_type_ids([recipe_type.id])
        recipe_type.sub_recipe_types = RecipeType.objects.all().filter(id__in=sub_ids)

        return recipe_type

    def get_recipe_types_v5(self, started=None, ended=None, order=None):
        """Returns a list of recipe types within the given time range.

        :param started: Query recipe types updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query recipe types updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of recipe types that match the time range.
        :rtype: list[:class:`recipe.models.RecipeType`]
        """

        # Fetch a list of recipe types
        recipe_types = RecipeType.objects.all().defer('description')

        # Apply time range filtering
        if started:
            recipe_types = recipe_types.filter(last_modified__gte=started)
        if ended:
            recipe_types = recipe_types.filter(last_modified__lte=ended)

        # Apply sorting
        if order:
            recipe_types = recipe_types.order_by(*order)
        else:
            recipe_types = recipe_types.order_by('last_modified')
        return recipe_types

    def get_recipe_types_v6(self, keywords=None, is_active=None, is_system=None, order=None):
        """Returns a list of recipe types within the given time range.

        :param keywords: Query recipe types with name, title, description or tag matching a keyword
        :type keywords: list
        :param is_active: Query recipe types that are actively available for use.
        :type is_active: bool
        :param is_system: Query recipe types that are system recipe types.
        :type is_operational: bool
        :param order: A list of fields to control the sort order.
        :type order: list
        :returns: The list of recipe types that match the given parameters.
        :rtype: list
        """

        # Fetch a list of recipe types
        recipe_types = self.all()
        if keywords:
            key_query = Q()
            for keyword in keywords:
                key_query |= Q(name__icontains=keyword)
                key_query |= Q(title__icontains=keyword)
                key_query |= Q(description__icontains=keyword)
            recipe_types = recipe_types.filter(key_query)
        if is_active is not None:
            recipe_types = recipe_types.filter(is_active=is_active)
        if is_system is not None:
            recipe_types = recipe_types.filter(is_system=is_system)

        # Apply sorting
        if order:
            recipe_types = recipe_types.order_by(*order)
        else:
            recipe_types = recipe_types.order_by('last_modified')
        return recipe_types

    def validate_recipe_type_v5(self, name, title, version, description, definition, trigger_config):
        """Validates a new recipe type prior to attempting a save

        :param name: The system name of the recipe type
        :type name: str
        :param title: The human-readable name of the recipe type
        :type title: str
        :param version: The version of the recipe type
        :type version: str
        :param description: An optional description of the recipe type
        :type description: str
        :param definition: The definition for running a recipe of this type
        :type definition: :class:`recipe.configuration.definition.recipe_definition.RecipeDefinition`
        :param trigger_config: The trigger rule configuration
        :type trigger_config: :class:`trigger.configuration.trigger_rule.TriggerRuleConfiguration`
        :returns: A list of warnings discovered during validation.
        :rtype: list[:class:`job.configuration.data.job_data.ValidationWarning`]

        :raises :class:`recipe.configuration.definition.exceptions.InvalidDefinition`: If any part of the recipe
            definition violates the specification
        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeConnection`: If the trigger rule connection to
            the recipe type definition is invalid
        """

        warnings = definition.validate_job_interfaces()

        return warnings

    def validate_recipe_type_v6(self, name, definition_dict):
        """Validates a recipe type prior to attempting a save

        :param name: The optional system name of a recipe type being updated
        :type name: str
        :param definition_dict: The definition for running a recipe of this type
        :type definition_dict: dict
        :returns: The recipe type validation.
        :rtype: :class:`recipe.models.RecipeTypeValidation`
        """

        from recipe.definition.exceptions import InvalidDefinition

        is_valid = True
        errors = []
        warnings = []
        diff = {}

        definition = None

        try:
            definition = RecipeDefinitionV6(definition=definition_dict, do_validate=True).get_definition()
        except InvalidDefinition as ex:
            is_valid = False
            errors.append(ex.error)
            message = 'Recipe Type definition invalid: %s' % ex
            logger.info(message)
            pass

        if definition:
            try:
                inputs, outputs = self.get_interfaces(definition)
                warnings.extend(definition.validate(inputs, outputs))
            except (InvalidDefinition) as ex:
                is_valid = False
                errors.append(ex.error)
                message = 'Recipe type definition invalid: %s' % ex
                logger.info(message)
                pass


            try:
                recipe_type = RecipeType.objects.all().get(name=name)
                old_definition = recipe_type.get_definition()
                diff = RecipeDiff(old_definition, definition)
                if not diff.can_be_reprocessed:
                    msg = 'This recipe cannot be reprocessed after updating.'
                    warnings.append(ValidationWarning('REPROCESS_WARNING',msg))
                    is_valid = False
                json = convert_recipe_diff_to_v6_json(diff)
                diff = rest_utils.strip_schema_version(json.get_dict())

            except RecipeType.DoesNotExist as ex:
                if name:
                    msg = 'Unable to find an existing recipe type with name: %s' % name
                    warnings.append(ValidationWarning('RECIPE_TYPE_NOT_FOUND', msg))
                pass
            except Exception as ex:
                errors.append(ex.error)
                logger.exception('Unable to generate RecipeDiff: %s' % ex)
                pass

        return RecipeTypeValidation(is_valid, errors, warnings, diff)

    def get_interfaces(self, definition):
        """Gets the input and output interfaces for each node in this recipe

        :returns: A dict of input interfaces and a dict of output interfaces
        :rtype: dict, dict

        :raises :class:`recipe.definition.exceptions.InvalidDefinition`: If any part of the recipe
            definition violates the specification
        """

        from recipe.definition.exceptions import InvalidDefinition
        from job.models import JobTypeRevision
        inputs = {}
        outputs = {}

        try:
            for node_name in definition.get_topological_order():
                node = definition.graph[node_name]
                if node.node_type == JobNodeDefinition.NODE_TYPE:
                    inputs[node_name], outputs[node_name] = self._get_job_interfaces(node)
                elif node.node_type == RecipeNodeDefinition.NODE_TYPE:
                    inputs[node_name], outputs[node_name] = self._get_recipe_interfaces(node)
        except (JobType.DoesNotExist, JobTypeRevision.DoesNotExist) as ex:
            msg = 'Recipe definition contains a job type that does not exist: %s' % ex
            raise InvalidDefinition('JOB_TYPE_DOES_NOT_EXIST', msg)
        except RecipeType.DoesNotExist as ex:
            msg = 'Recipe definition contains a sub recipe type that does not exist: %s' % ex
            raise InvalidDefinition('RECIPE_TYPE_DOES_NOT_EXIST', msg)

        return inputs, outputs

    def _get_job_interfaces(self, node):
        """Gets the input/output interfaces for a job type node
        """

        from job.models import JobTypeRevision
        input = Interface()
        output = Interface()
        jtr = JobTypeRevision.objects.get_details_v6(node.job_type_name, node.job_type_version, node.revision_num)
        if jtr:
            input = jtr.get_input_interface()
            output = jtr.get_output_interface()

        return input, output

    def _get_recipe_interfaces(self, node):
        """Gets the input/output interfaces for a recipe type node
        """

        from recipe.models import RecipeTypeRevision
        input = Interface()
        output = Interface()
        rtr = RecipeTypeRevision.objects.get_revision(node.recipe_type_name, node.revision_num)
        if rtr:
            input = rtr.get_input_interface()  # no output interface

        return input, output


class RecipeType(models.Model):
    """Represents a type of recipe that can be run on the cluster. Any updates to a recipe type model requires obtaining
    a lock on the model using select_for_update().

    :keyword name: The identifying name of the recipe type used by clients for queries
    :type name: :class:`django.db.models.CharField`
    :keyword version: The version of the recipe type
    :type version: :class:`django.db.models.CharField`
    :keyword title: The human-readable name of the recipe type
    :type title: :class:`django.db.models.CharField`
    :keyword description: An optional description of the recipe type
    :type description: :class:`django.db.models.CharField`

    :keyword is_system: Whether this is a system recipe type
    :type is_system: :class:`django.db.models.BooleanField`
    :keyword is_active: Whether the recipe type is active (false once recipe type is archived)
    :type is_active: :class:`django.db.models.BooleanField`
    :keyword definition: JSON definition for running a recipe of this type
    :type definition: :class:`django.contrib.postgres.fields.JSONField`
    :keyword revision_num: The current revision number of the definition, starts at one
    :type revision_num: :class:`django.db.models.IntegerField`
    :keyword trigger_rule: The rule to trigger new recipes of this type
    :type trigger_rule: :class:`django.db.models.ForeignKey`

    :keyword created: When the recipe type was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword deprecated: When the recipe type was deprecated (no longer active)
    :type deprecated: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the recipe type was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    name = models.CharField(unique=True, max_length=50)
    version = models.CharField(db_index=True, max_length=50)
    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.CharField(blank=True, max_length=500, null=True)

    is_system = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    definition = django.contrib.postgres.fields.JSONField(default=dict)
    revision_num = models.IntegerField(default=1)

    # TODO: remove this when going to Scale v6
    trigger_rule = models.ForeignKey('trigger.TriggerRule', blank=True, null=True, on_delete=models.PROTECT)

    created = models.DateTimeField(auto_now_add=True)
    deprecated = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = RecipeTypeManager()

    def get_definition(self):
        """Returns the definition for this recipe type

        :returns: The definition for this recipe type
        :rtype: :class:`recipe.definition.definition.RecipeDefinition`
        """

        return RecipeDefinitionV6(definition=self.definition, do_validate=False).get_definition()

    # TODO: deprecated, remove in Scale v6 once the trigger system is gone, use get_definition() instead
    def get_recipe_definition(self):
        """Returns the definition for running recipes of this type

        :returns: The recipe definition for this type
        :rtype: :class:`recipe.configuration.definition.recipe_definition.RecipeDefinition`
        """

        return RecipeDefinitionSunset.create(self.definition)

    def get_v6_definition_json(self):
        """Returns the recipe type definition in v6 of the JSON schema

        :returns: The recipe type definition in v6 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_recipe_definition_to_v6_json(self.get_definition()).get_dict())

    def natural_key(self):
        """Django method to define the natural key for a recipe type as the combination of name and version

        :returns: A tuple representing the natural key
        :rtype: tuple(string, string)
        """

        return self.name, self.version

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_type'


class RecipeTypeRevisionManager(models.Manager):
    """Provides additional methods for handling recipe type revisions
    """

    def create_recipe_type_revision(self, recipe_type):
        """Creates a new revision for the given recipe type. The recipe type's definition and revision number must
        already be updated. The caller must have obtained a lock using select_for_update() on the given recipe type
        model.

        :param recipe_type: The recipe type
        :type recipe_type: :class:`recipe.models.RecipeType`
        """

        new_rev = RecipeTypeRevision()
        new_rev.recipe_type = recipe_type
        new_rev.revision_num = recipe_type.revision_num
        new_rev.definition = recipe_type.definition
        new_rev.save()

    def get_by_natural_key(self, recipe_type, revision_num):
        """Django method to retrieve a recipe type revision for the given natural key

        :param recipe_type: The recipe type
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param revision_num: The revision number
        :type revision_num: int
        :returns: The recipe type revision defined by the natural key
        :rtype: :class:`recipe.models.RecipeTypeRevision`
        """

        return self.get(recipe_type_id=recipe_type.id, revision_num=revision_num)

    def get_revision(self, name, revision_num):
        """Returns the revision (with populated recipe_type model) for the given recipe type and revision number

        :param name: The name of the recipe type
        :type name: string
        :param revision_num: The revision number
        :type revision_num: int
        :returns: The revision
        :rtype: :class:`recipe.models.RecipeTypeRevision`
        """

        return self.select_related('recipe_type').get(recipe_type__name=name, revision_num=revision_num)

    def get_revisions(self, name):
        """Returns the revision (with populated recipe_type model) for the given recipe type and revision number

        :param name: The name of the recipe type
        :type name: string
        :returns: The recipe type revisions for the given recipe type name
        :rtype: [:class:`recipe.models.RecipeTypeRevision`]
        """

        revs = self.select_related('recipe_type').filter(recipe_type__name=name)

        revs = revs.order_by('-revision_num')

        return revs

    def get_revision_map(self, revision_ids, revision_tuples):
        """Returns a dict that maps revision ID to recipe type revision for the recipe type revisions that match the
        given values. Each revision model will have its related recipe type model populated.

        :param revision_ids: A list of revision IDs to return
        :type revision_ids: list
        :param revision_tuples: A list of tuples (recipe type name, revision num) for additional revisions to return
        :type revision_tuples: list
        :returns: The revisions stored by revision ID
        :rtype: dict
        """

        revisions = {}
        qry_filter = Q(id__in=revision_ids)
        for revision_tuple in revision_tuples:
            qry_filter = qry_filter | Q(recipe_type__name=revision_tuple[0], revision_num=revision_tuple[1])
        for rev in self.select_related('recipe_type').filter(qry_filter):
            revisions[rev.id] = rev
        return revisions

    # TODO: remove this in Scale v6 when the deprecated message reprocess_recipes is removed
    def get_revisions_for_reprocess_old(self, recipes_to_reprocess, new_rev_id):
        """Returns a dict that maps revision ID to recipe type revision for the given recipes to reprocess and for the
        given new revision ID. Each revision model will have its related recipe type model populated.

        :param recipes_to_reprocess: The recipe models to reprocess
        :type recipes_to_reprocess: list
        :param new_rev_id: The revision ID for the new recipes
        :type new_rev_id: int
        :returns: The revisions stored by revision ID
        :rtype: dict
        """

        rev_ids = {recipe.recipe_type_rev_id for recipe in recipes_to_reprocess}
        rev_ids.add(new_rev_id)

        revisions = {}
        for rev in self.select_related('recipe_type').filter(id__in=rev_ids):
            revisions[rev.id] = rev
        return revisions


class RecipeTypeRevision(models.Model):
    """Represents a revision of a recipe type. New revisions are created when the definition of a recipe type changes.
    Any inserts of a recipe type revision model requires obtaining a lock using select_for_update() on the corresponding
    recipe type model.

    :keyword recipe_type: The recipe type for this revision
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword revision_num: The number for this revision, starting at one
    :type revision_num: :class:`django.db.models.IntegerField`
    :keyword definition: The JSON definition for this revision of the recipe type
    :type definition: :class:`django.contrib.postgres.fields.JSONField`
    :keyword created: When this revision was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    recipe_type = models.ForeignKey('recipe.RecipeType', on_delete=models.PROTECT)
    revision_num = models.IntegerField()
    definition = django.contrib.postgres.fields.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    objects = RecipeTypeRevisionManager()

    def get_definition(self):
        """Returns the definition for this recipe type revision

        :returns: The definition for this revision
        :rtype: :class:`recipe.definition.definition.RecipeDefinition`
        """

        return RecipeDefinitionV6(definition=self.definition, do_validate=False).get_definition()

    def get_input_interface(self):
        """Returns the input interface for this revision

        :returns: The input interface for this revision
        :rtype: :class:`data.interface.interface.Interface`
        """

        return self.get_definition().input_interface

    # TODO: deprecated, remove in Scale v6 once the trigger system is gone, use get_definition() instead
    def get_recipe_definition(self):
        """Returns the recipe type definition for this revision

        :returns: The recipe type definition for this revision
        :rtype: :class:`recipe.configuration.definition.recipe_definition.RecipeDefinition`
        """

        return RecipeDefinitionSunset.create(self.definition)

    def get_v6_definition_json(self):
        """Returns the revision definition in v6 of the JSON schema

        :returns: The revision definition in v6 of the JSON schema
        :rtype: dict
        """

        return rest_utils.strip_schema_version(convert_recipe_definition_to_v6_json(self.get_definition()).get_dict())

    def validate_forced_nodes(self, forced_nodes_json):
        """Validates a forced nodes object against the definition for this recipe type revision

        :param forced_nodes_json: The definition of nodes to be forced to reprocess
        :type forced_nodes_json: dict
        :returns: The ForcedNodes validation.
        :rtype: :class:`recipe.models.ForcedNodesValidation`
        """

        from recipe.diff.exceptions import InvalidDiff
        from recipe.diff.json.forced_nodes_v6 import ForcedNodesV6, convert_forced_nodes_to_v6

        is_valid = True
        errors = []
        warnings = []
        diff = {}

        definition = None

        try:
            forced_nodes_v6 = ForcedNodesV6(forced_nodes_json, do_validate=True)
        except InvalidDiff as ex:
            is_valid = False
            errors.append(ex.error)
            message = 'Invalid forced nodes definition: %s' % ex
            logger.info(message)
            pass

        if forced_nodes_v6:
            forced_nodes = forced_nodes_v6.get_forced_nodes()
            node_names = forced_nodes.get_forced_node_names()
            sub_names = forced_nodes.get_sub_recipe_names()
            if forced_nodes.all_nodes and node_names:
                warnings.append('nodes defined with all field set to True')
            definition = self.get_definition()
            top_level_names = definition.get_topological_order()
            for name in forced_nodes.get_forced_node_names():
                if name not in top_level_names:
                    errors.append('Recipe definition does not have a top level node with name: %s' % name)
                    is_valid = False
                    continue
                node = definition.graph[name]
                if node.node_type == RecipeNodeDefinition.NODE_TYPE:
                    if name not in sub_names:
                        warnings.append('Node %s is a recipe node but is not defined in sub_recipes' % name)

            if forced_nodes.all_nodes and sub_names:
                warnings.append('sub_recipes defined with all field set to True')
            for name in sub_names:
                if name not in forced_nodes.get_forced_node_names():
                    warnings.append('Sub-recipe %s defined but not listed in nodes' % name)
                if name not in top_level_names:
                    errors.append('Recipe definition does not have a top level node with name: %s' % name)
                    is_valid = False
                    continue
                node = definition.graph[name]
                if node.node_type != RecipeNodeDefinition.NODE_TYPE:
                    errors.append('Sub-recipe node %s is not a recipe node' % name)
                    is_valid = False
                    continue
                try:
                    sub = RecipeTypeRevision.objects.get_revision(node.recipe_type_name, node.revision_num)
                except RecipeTypeRevision.DoesNotExist as ex:
                    msg = 'Unable to get recipe type revision for sub-recipe %s with name %s and revision %d'
                    errors.append(msg % (name, node.recipe_type_name, node.revision_num))
                    is_valid = False
                    continue
                sub_nodes = forced_nodes.get_forced_nodes_for_subrecipe(name)
                validate = sub.validate_forced_nodes(convert_forced_nodes_to_v6(sub_nodes).get_dict())
                is_valid &= validate.is_valid
                errors.extend(validate.errors)
                warnings.extend(validate.warnings)

        return ForcedNodesValidation(is_valid, errors, warnings, forced_nodes)

    def natural_key(self):
        """Django method to define the natural key for a recipe type revision as the combination of job type and
        revision number

        :returns: A tuple representing the natural key
        :rtype: tuple(string, int)
        """

        return self.recipe_type, self.revision_num

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_type_revision'
        unique_together = ('recipe_type', 'revision_num')

class RecipeTypeSubLinkManager(models.Manager):
    """Provides additional methods for handling recipe type sub links
    """

    def create_recipe_type_sub_links_from_definition(self, recipe_type):
        """Goes through a recipe type definition, gets all the recipe types it contains and creates the appropriate links

        :param recipe_type: New/updated recipe type
        :type recipe_type: :class:`recipe.models.RecipeType`

        :raises :class:`recipe.models.RecipeType.DoesNotExist`: If it contains a sub recipe type that does not exist
        """

        # Delete any previous links for the given recipe
        RecipeTypeSubLink.objects.filter(recipe_type_id=recipe_type.id).delete()

        definition = recipe_type.get_definition()

        sub_type_names = definition.get_recipe_type_names()

        sub_type_ids = RecipeType.objects.all().filter(name__in=sub_type_names).values_list('pk', flat=True)

        if len(sub_type_ids) > 0:
            recipe_type_ids = [recipe_type.id] * len(sub_type_ids)
            self.create_recipe_type_sub_links(recipe_type_ids, sub_type_ids)

    @transaction.atomic
    def create_recipe_type_sub_links(self, recipe_type_ids, sub_recipe_type_ids):
        """Creates the appropriate links for the given parent and child recipe types. All database changes are
        made in an atomic transaction.

        :param recipe_type_ids: List of parent recipe type IDs
        :type recipe_type_ids: list of int
        :param sub_recipe_type_ids: List of child recipe type IDs.
        :type sub_recipe_type_ids: list of int
        """

        if len(recipe_type_ids) != len(sub_recipe_type_ids):
            raise Exception('Recipe Type and Sub recipe type lists must be equal length!')

        new_links = []

        for id, sub in zip(recipe_type_ids, sub_recipe_type_ids):
            link = RecipeTypeSubLink(recipe_type_id=id, sub_recipe_type_id=sub)
            link.save()

    @transaction.atomic
    def create_recipe_type_sub_link(self, recipe_type_id, sub_recipe_type_id):
        """Creates the appropriate link for the given recipe and job type. All database changes are
        made in an atomic transaction.

        :param recipe_type_id: recipe type ID
        :type recipe_type_id: int
        :param sub_recipe_type_id: sub recipe type ID.
        :type sub_recipe_type_id: int
        """

        # Delete any previous links for the given recipe
        RecipeTypeSubLink.objects.filter(recipe_type_id=recipe_type_id).delete()

        link = RecipeTypeSubLink(recipe_type_id=recipe_type_id, sub_recipe_type_id=sub_recipe_type_id)
        link.save()

    def get_recipe_type_ids(self, sub_recipe_type_ids):
        """Returns a list of the parent recipe_type IDs for the given sub recipe type IDs.

        :param sub_recipe_type_ids: The sub recipe type IDs
        :type sub_recipe_type_ids: list
        :returns: The list of parent recipe type IDs
        :rtype: list
        """

        query = RecipeTypeSubLink.objects.filter(sub_recipe_type_id__in=list(sub_recipe_type_ids)).only('recipe_type_id')
        return [result.recipe_type_id for result in query]

    def get_sub_recipe_type_ids(self, recipe_type_ids):
        """Returns a list of the sub recipe type IDs for the given recipe type IDs.

        :param recipe_type_ids: The recipe type IDs
        :type recipe_type_ids: list
        :returns: The list of sub recipe type IDs
        :rtype: list
        """

        query = RecipeTypeSubLink.objects.filter(recipe_type_id__in=list(recipe_type_ids)).only('sub_recipe_type_id')
        return [result.sub_recipe_type_id for result in query]

class RecipeTypeSubLink(models.Model):
    """Represents a link between a recipe type and a sub-recipe type.

    :keyword recipe_type: The related recipe type
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword sub_recipe_type: The related sub recipe type
    :type sub_recipe_type: :class:`django.db.models.ForeignKey`
    """

    recipe_type = models.ForeignKey('recipe.RecipeType', on_delete=models.PROTECT, related_name='parent_recipe_type')
    sub_recipe_type = models.ForeignKey('recipe.RecipeType', on_delete=models.PROTECT, related_name='sub_recipe_type')

    objects = RecipeTypeSubLinkManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_type_sub_link'
        unique_together = ('recipe_type', 'sub_recipe_type')

class RecipeTypeJobLinkManager(models.Manager):
    """Provides additional methods for handling recipe type to job type links
    """

    def create_recipe_type_job_links_from_definition(self, recipe_type):
        """Goes through a recipe type definition and gets all the job types it contains and creates the appropriate links

        :param recipe_type: New/updated recipe type
        :type recipe_type: :class:`recipe.models.RecipeType`

        :raises :class:`recipe.models.JobType.DoesNotExist`: If it contains a job type that does not exist
        """

        # Delete any previous links for the given recipe
        RecipeTypeJobLink.objects.filter(recipe_type_id=recipe_type.id).delete()

        definition = recipe_type.get_definition()

        job_type_ids = JobType.objects.get_recipe_job_type_ids(definition)

        if len(job_type_ids) > 0:
            recipe_type_ids = [recipe_type.id] * len(job_type_ids)
            self.create_recipe_type_job_links(recipe_type_ids, job_type_ids)


    @transaction.atomic
    def create_recipe_type_job_links(self, recipe_type_ids, job_type_ids):
        """Creates the appropriate links for the given recipe and job types. All database changes are
        made in an atomic transaction.

        :param recipe_type_ids: List of recipe type IDs
        :type recipe_type_ids: list of int
        :param job_type_ids: List of job type IDs.
        :type job_type_ids: list of int
        """

        if len(recipe_type_ids) != len(job_type_ids):
            raise Exception('Recipe Type and Job Type lists must be equal length!')

        new_links = []

        for id, job in zip(recipe_type_ids, job_type_ids):
            link = RecipeTypeJobLink(recipe_type_id=id, job_type_id=job)
            link.save()

    @transaction.atomic
    def create_recipe_type_job_link(self, recipe_type_id, job_type_id):
        """Creates the appropriate link for the given recipe and job type. All database changes are
        made in an atomic transaction.

        :param recipe_type_id: recipe type ID
        :type recipe_type_id: int
        :param job_type_id: job type ID.
        :type job_type_id: int
        """

        # Delete any previous links for the given recipe
        RecipeTypeJobLink.objects.filter(recipe_type_id=recipe_type_id).delete()

        link = RecipeTypeJobLink(recipe_type_id=recipe_type_id, job_type_id=job_type_id)
        link.save()

    def get_recipe_type_ids(self, job_type_ids):
        """Returns a list of recipe_type IDs for the given job type IDs.

        :param job_type_ids: The sub recipe type IDs
        :type job_type_ids: list
        :returns: The list of recipe type IDs
        :rtype: list
        """

        query = RecipeTypeJobLink.objects.filter(job_type_id__in=list(job_type_ids)).only('recipe_type_id')
        return [result.recipe_type_id for result in query]

    def get_job_type_ids(self, recipe_type_ids):
        """Returns a list of the job type IDs for the given recipe type IDs.

        :param recipe_type_ids: The recipe type IDs
        :type recipe_type_ids: list
        :returns: The list of job type IDs
        :rtype: list
        """

        query = RecipeTypeJobLink.objects.filter(recipe_type_id__in=list(recipe_type_ids)).only('job_type_id')
        return [result.job_type_id for result in query]

class RecipeTypeJobLink(models.Model):
    """Represents a link between a recipe type and a job type.

    :keyword recipe_type: The related recipe type
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword job_type: The related job type
    :type job_type: :class:`django.db.models.ForeignKey`
    """

    recipe_type = models.ForeignKey('recipe.RecipeType', on_delete=models.PROTECT, related_name='recipe_types_for_job_type')
    job_type = models.ForeignKey('job.JobType', on_delete=models.PROTECT, related_name='job_types_for_recipe_type')

    objects = RecipeTypeJobLinkManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_type_job_link'
        unique_together = ('recipe_type', 'job_type')