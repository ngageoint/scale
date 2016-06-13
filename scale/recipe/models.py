"""Defines the database models for recipes and recipe types"""
from __future__ import unicode_literals

import django.utils.timezone as timezone
import djorm_pgjson.fields
from django.db import models, transaction

from job.models import Job, JobType
from recipe.configuration.data.recipe_data import RecipeData
from recipe.configuration.definition.recipe_definition import RecipeDefinition
from recipe.handlers.handler import RecipeHandler
from recipe.triggers.configuration.trigger_rule import RecipeTriggerRuleConfiguration
from storage.models import ScaleFile
from trigger.configuration.exceptions import InvalidTriggerType
from trigger.models import TriggerRule


# IMPORTANT NOTE: Locking order
# Always adhere to the following model order for obtaining row locks via select_for_update() in order to prevent
# deadlocks and ensure query efficiency
# When applying status updates to jobs: JobExecution, Queue, Job, Recipe
# When editing a job/recipe type: RecipeType, JobType, TriggerRule


class RecipeManager(models.Manager):
    """Provides additional methods for handling recipes
    """

    def complete(self, recipe_id, when):
        """Marks the recipe with the given ID as being completed

        :param recipe_id: The recipe ID
        :type recipe_id: :int
        :param when: The time that the recipe was completed
        :type when: :class:`datetime.datetime`
        """

        modified = timezone.now()
        self.filter(id=recipe_id).update(completed=when, last_modified=modified)

    @transaction.atomic
    def create_recipe(self, recipe_type, event, data, superseded_recipe=None, delta=None, superseded_jobs=None):
        """Creates a new recipe for the given type and returns a recipe handler for it. All jobs for the recipe will
        also be created. If the new recipe is superseding an old recipe, superseded_recipe, delta, and superseded_jobs
        must be provided and the caller must have obtained a model lock on all job models in superseded_jobs and on the
        superseded_recipe model. All database changes occur in an atomic transaction.

        :param recipe_type: The type of the recipe to create
        :type recipe_type: :class:`recipe.models.RecipeType`
        :param event: The event that triggered the creation of this recipe
        :type event: :class:`trigger.models.TriggerEvent`
        :param data: JSON description defining the recipe data to run on
        :type data: dict
        :param superseded_recipe: The recipe that the created recipe is superseding, possibly None
        :type superseded_recipe: :class:`recipe.models.Recipe`
        :param delta: If not None, represents the changes between the old recipe to supersede and the new recipe
        :type delta: :class:`recipe.handlers.graph_delta.RecipeGraphDelta`
        :param superseded_jobs: If not None, represents the job models (stored by job name) of the old recipe to
            supersede
        :type superseded_jobs: {string: :class:`job.models.Job`}
        :returns: A handler for the new recipe
        :rtype: :class:`recipe.handlers.handler.RecipeHandler`

        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeData`: If the recipe data is invalid
        """

        if not recipe_type.is_active:
            raise Exception('Recipe type is no longer active')
        if event is None:
            raise Exception('Event that triggered recipe creation is required')

        recipe = Recipe()
        recipe.recipe_type = recipe_type
        recipe.recipe_type_rev = RecipeTypeRevision.objects.get_revision(recipe_type.id, recipe_type.revision_num)
        recipe.event = event
        recipe_definition = recipe.get_recipe_definition()

        # Validate recipe data and save recipe
        recipe_data = RecipeData(data)
        recipe_definition.validate_data(recipe_data)
        recipe.data = data
        recipe.save()
        when = timezone.now()

        # Supersede recipe
        if superseded_recipe:
            superseded_recipe.is_superseded = True
            superseded_recipe.superseded = when

        # Create recipe jobs and link them to the recipe
        recipe_jobs = self._create_recipe_jobs(recipe, event, when, delta, superseded_jobs)
        return RecipeHandler(recipe, recipe_jobs)

    def _create_recipe_jobs(self, recipe, event, when, delta, superseded_jobs):
        """Creates and returns the job and recipe_job models for the given new recipe. If the new recipe is superseding
        an old recipe, both delta and superseded_jobs must be provided and the caller must have obtained a model lock on
        all job models in superseded_jobs.

        :param recipe: The new recipe
        :type recipe: :class:`recipe.models.Recipe`
        :param event: The event that triggered the creation of this recipe
        :type event: :class:`trigger.models.TriggerEvent`
        :param when: The time that the recipe was created
        :type when: :class:`datetime.datetime`
        :param delta: If not None, represents the changes between the old recipe to supersede and the new recipe
        :type delta: :class:`recipe.handlers.graph_delta.RecipeGraphDelta`
        :param superseded_jobs: If not None, represents the job models (stored by job name) of the old recipe to
            supersede
        :type superseded_jobs: {string: :class:`job.models.Job`}
        :returns: The list of newly created recipe_job models (without id field populated)
        :rtype: [:class:`recipe.models.RecipeJob`]
        """

        recipe_jobs_to_create = []
        jobs_to_supersede = []
        for job_tuple in recipe.get_recipe_definition().get_jobs_to_create():
            job_name = job_tuple[0]
            job_type = job_tuple[1]
            superseded_job = None

            if delta:  # Look at changes from recipe we are superseding
                if job_name in delta.get_identical_nodes():  # Identical jobs should be copied
                    copied_job = superseded_jobs[delta.get_identical_nodes[job_name]]
                    recipe_job = RecipeJob()
                    recipe_job.job = copied_job
                    recipe_job.job_name = job_name
                    recipe_job.recipe = recipe
                    recipe_job.is_original = False
                    recipe_jobs_to_create.append(recipe_job)
                    break  # Don't create a new job, just copy old one
                elif job_name in delta.get_changed_nodes():  # Changed jobs should be superseded
                    superseded_job = superseded_jobs[delta.get_changed_nodes[job_name]]
                    jobs_to_supersede.append(superseded_job)

            job = Job.objects.create_job(job_type, event, superseded_job)
            job.save()
            recipe_job = RecipeJob()
            recipe_job.job = job
            recipe_job.job_name = job_name
            recipe_job.recipe = recipe
            recipe_jobs_to_create.append(recipe_job)

        # Supersede any jobs that were changed or deleted in new recipe
        if delta:
            for superseded_job_name in delta.get_deleted_nodes():
                jobs_to_supersede.append(superseded_jobs[superseded_job_name])
        if jobs_to_supersede:
            Job.objects.supersede_jobs(jobs_to_supersede, when)

        RecipeJob.objects.bulk_create(recipe_jobs_to_create)
        return recipe_jobs_to_create

    def get_recipe_for_job(self, job_id):
        """Returns the original recipe for the job with the given ID (returns None if the job is not in a recipe). The
        returned model will have its related recipe_type and recipe_type_rev models populated. If the job exists in
        multiple recipes due to superseding, the original (first) recipe is returned.

        :param job_id: The job ID
        :type job_id: int
        :returns: The recipe model with related recipe_type and recipe_type-rev, possibly None
        :rtype: :class:`recipe.models.Recipe`
        """

        recipe_job_qry = RecipeJob.objects.select_related('recipe__recipe_type', 'recipe__recipe_type_rev')
        try:
            recipe_job = recipe_job_qry.get(job_id=job_id, is_original=True)
        except RecipeJob.DoesNotExist:
            return None
        return recipe_job.recipe

    def get_recipe_handler_for_job(self, job_id):
        """Returns the recipe handler (possibly None) for the recipe containing the job with the given ID. The caller
        must first have obtained a model lock on the job model for the given ID. This method will acquire model locks on
        all jobs models that depend upon the given job, allowing update queries to be made on the dependent jobs. No
        handler will be returned for a job that is not in a non-superseded recipe.

        :param job_id: The job ID
        :type job_id: int
        :returns: The recipe handler, possibly None
        :rtype: :class:`recipe.handlers.handler.RecipeHandler`
        """

        handlers = self.get_recipe_handlers_for_jobs([job_id])
        if handlers:
            return handlers[0]
        return None

    def get_recipe_handlers_for_jobs(self, job_ids):
        """Returns recipe handlers for all of the recipes containing the jobs with the given IDs. The caller must first
        have obtained model locks on all of the job models for the given IDs. This method will acquire model locks on
        all jobs models that depend upon the given jobs, allowing update queries to be made on the dependent jobs.
        Handlers will not be returned for jobs that are not in a recipe or for recipes that are superseded.

        :param job_ids: The job IDs
        :type job_ids: [int]
        :returns: The recipe handlers
        :rtype: :class:`recipe.handlers.handler.RecipeHandler`
        """

        # Figure out the non-superseded recipe ID (if applicable) for each job ID
        recipe_id_per_job_id = {}  # {Job ID: Recipe ID}
        for recipe_job in RecipeJob.objects.filter(job_id__in=job_ids, recipe__is_superseded=False).iterator():
            # A job should match at most one non-superseded recipe
            recipe_id_per_job_id[recipe_job.job_id] = recipe_job.recipe_id
        if not recipe_id_per_job_id:
            return {}

        # Get handlers for all recipes and figure out dependent jobs to lock
        recipe_ids = recipe_id_per_job_id.values()
        handlers = self._get_recipe_handlers(recipe_ids)
        job_ids_to_lock = set()
        for job_id in recipe_id_per_job_id:
            recipe_id = recipe_id_per_job_id[job_id]
            if recipe_id in handlers:
                handler = handlers[recipe_id]
                job_ids_to_lock |= handler.get_dependent_job_ids(job_id)  # Add dependent IDs by doing set union

        if not job_ids_to_lock:
            # No dependent jobs, just return handlers
            return handlers.values()

        # Lock dependent recipe jobs
        Job.objects.lock_jobs(job_ids_to_lock)

        # Return handlers with updated data after all dependent jobs have been locked
        return self._get_recipe_handlers(recipe_ids).values()

    def get_recipes(self, started=None, ended=None, type_ids=None, type_names=None, order=None):
        """Returns a list of recipes within the given time range.

        :param started: Query recipes updated after this amount of time.
        :type started: :class:`datetime.datetime`
        :param ended: Query recipes updated before this amount of time.
        :type ended: :class:`datetime.datetime`
        :param type_ids: Query recipes of the type associated with the identifier.
        :type type_ids: list[int]
        :param type_names: Query recipes of the type associated with the name.
        :type type_names: list[str]
        :param order: A list of fields to control the sort order.
        :type order: list[str]
        :returns: The list of recipes that match the time range.
        :rtype: list[:class:`recipe.models.Recipe`]
        """

        # Fetch a list of recipes
        recipes = Recipe.objects.all()
        recipes = recipes.select_related('recipe_type', 'recipe_type_rev', 'event')
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
        recipe = Recipe.objects.all()
        recipe = recipe.select_related('recipe_type', 'recipe_type_rev', 'event', 'event__rule')
        recipe = recipe.get(pk=recipe_id)

        # Update the recipe with source file models
        input_file_ids = recipe.get_recipe_data().get_input_file_ids()
        input_files = ScaleFile.objects.filter(id__in=input_file_ids)
        input_files = input_files.select_related('workspace').defer('workspace__json_config')
        input_files = input_files.order_by('id').distinct('id')
        recipe.input_files = [input_file for input_file in input_files]

        # Update the recipe with job models
        jobs = RecipeJob.objects.filter(recipe_id=recipe.id)
        jobs = jobs.select_related('job', 'job__job_type', 'job__event', 'job__error')
        recipe.jobs = jobs
        return recipe

    def _get_recipe_handlers(self, recipe_ids):
        """Returns the handlers for the given recipe IDs. If a given recipe ID is not valid it will not be included in
        the results.

        :param recipe_ids: The recipe IDs
        :type recipe_ids: [int]
        :returns: The recipe handlers by recipe ID
        :rtype: {int: :class:`recipe.handler.RecipeHandler`}
        """

        handlers = {}  # {Recipe ID: Recipe handler}
        recipe_jobs_dict = RecipeJob.objects.get_recipe_jobs(recipe_ids)
        for recipe_id in recipe_ids:
            if recipe_id in recipe_jobs_dict:
                recipe_jobs = recipe_jobs_dict[recipe_id]
                if recipe_jobs:
                    recipe = recipe_jobs[0].recipe
                    handler = RecipeHandler(recipe, recipe_jobs)
                    handlers[recipe.id] = handler
        return handlers


class Recipe(models.Model):
    """Represents a recipe to be run on the cluster

    :keyword recipe_type: The type of this recipe
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword recipe_type_rev: The revision of the recipe type when this recipe was created
    :type recipe_type_rev: :class:`django.db.models.ForeignKey`
    :keyword event: The event that triggered the creation of this recipe
    :type event: :class:`django.db.models.ForeignKey`

    :keyword data: JSON description defining the data for this recipe
    :type data: :class:`djorm_pgjson.fields.JSONField`

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
    event = models.ForeignKey('trigger.TriggerEvent', on_delete=models.PROTECT)

    data = djorm_pgjson.fields.JSONField()

    is_superseded = models.BooleanField(default=False)
    root_superseded_recipe = models.ForeignKey('recipe.Recipe', related_name='superseded_by_recipes', blank=True,
                                               null=True, on_delete=models.PROTECT)
    superseded_recipe = models.OneToOneField('recipe.Recipe', related_name='superseded_by_recipe', blank=True,
                                             null=True, on_delete=models.PROTECT)

    created = models.DateTimeField(auto_now_add=True)
    completed = models.DateTimeField(blank=True, null=True)
    superseded = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = RecipeManager()

    def get_recipe_data(self):
        """Returns the data for this recipe

        :returns: The data for this recipe
        :rtype: :class:`recipe.configuration.data.recipe_data.RecipeData`
        """

        return RecipeData(self.data)

    def get_recipe_definition(self):
        """Returns the definition for this recipe

        :returns: The definition for this recipe
        :rtype: :class:`recipe.configuration.definition.recipe_definition.RecipeDefinition`
        """

        return RecipeDefinition(self.recipe_type_rev.definition)

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe'
        index_together = ['last_modified', 'recipe_type']


class RecipeJobManager(models.Manager):
    """Provides additional methods for handling jobs linked to a recipe
    """

    def get_recipe_jobs(self, recipe_ids):
        """Returns the recipe_job models with related recipe, recipe_type, recipe_type_rev, job, job_type, and
        job_type_rev models for the given recipe IDs

        :param recipe_ids: The recipe IDs
        :type recipe_ids: [int]
        :returns: Dict where each recipe ID maps to its corresponding recipe_job models
        :rtype: {int: [:class:`recipe.models.RecipeJob`]}
        """

        recipes = {}  # {Recipe ID: [Recipe job]}

        recipe_qry = self.select_related('recipe__recipe_type', 'recipe__recipe_type_rev')
        recipe_qry = recipe_qry.select_related('job__job_type', 'job__job_type_rev')
        recipe_qry = recipe_qry.filter(recipe_id__in=recipe_ids)

        for recipe_job in recipe_qry.iterator():
            if recipe_job.recipe_id not in recipes:
                recipes[recipe_job.recipe_id] = []
            recipes[recipe_job.recipe_id].append(recipe_job)

        return recipes


class RecipeJob(models.Model):
    """Links a job and a recipe together. Jobs may exist in multiple recipes due to superseding. For an original job and
    recipe combination, the is_original flag is True. When recipe B supersedes recipe A, the non-superseded jobs from
    recipe A that are being copied to recipe B will have models with is_original set to False.

    :keyword recipe: The recipe that the job is linked to
    :type recipe: :class:`django.db.models.ForeignKey`
    :keyword job: The job that the recipe is linked to
    :type job: :class:`django.db.models.OneToOneField`
    :keyword job_name: The unique name of the job within the recipe
    :type job_name: :class:`django.db.models.CharField`
    :keyword is_original: Whether this is the original recipe for the job (True) or the job is copied from a superseded
        recipe (False)
    :type is_original: :class:`django.db.models.BooleanField`
    """

    recipe = models.ForeignKey('recipe.Recipe', on_delete=models.PROTECT)
    job = models.ForeignKey('job.Job', on_delete=models.PROTECT)
    job_name = models.CharField(max_length=100)
    is_original = models.BooleanField(default=True)

    objects = RecipeJobManager()

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_job'


class RecipeTypeManager(models.Manager):
    """Provides additional methods for handling recipe types
    """

    @transaction.atomic
    def create_recipe_type(self, name, version, title, description, definition, trigger_rule):
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
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerType`: If the given trigger rule is an invalid
            type for creating recipes
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerRule`: If the given trigger rule configuration is
            invalid
        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeConnection`: If the trigger rule connection to
            the recipe type definition is invalid
        """

        # Must lock job type interfaces so the new recipe type definition can be validated
        _ = definition.get_job_types(lock=True)
        definition.validate_job_interfaces()

        # Validate the trigger rule
        if trigger_rule:
            trigger_config = trigger_rule.get_configuration()
            if not isinstance(trigger_config, RecipeTriggerRuleConfiguration):
                raise InvalidTriggerType('%s is an invalid trigger rule type for creating recipes' % trigger_rule.type)
            trigger_config.validate_trigger_for_recipe(definition)

        # Create the new recipe type
        recipe_type = RecipeType()
        recipe_type.name = name
        recipe_type.version = version
        recipe_type.title = title
        recipe_type.description = description
        recipe_type.definition = definition.get_dict()
        recipe_type.trigger_rule = trigger_rule
        recipe_type.save()

        # Create first revision of the recipe type
        RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)

        return recipe_type

    @transaction.atomic
    def edit_recipe_type(self, recipe_type_id, title, description, definition, trigger_rule, remove_trigger_rule):
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
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerType`: If the given trigger rule is an invalid
            type for creating recipes
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerRule`: If the given trigger rule configuration is
            invalid
        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeConnection`: If the trigger rule connection to
            the recipe type definition is invalid
        """

        # Acquire model lock
        recipe_type = RecipeType.objects.select_for_update().get(pk=recipe_type_id)

        if title is not None:
            recipe_type.title = title

        if description is not None:
            recipe_type.description = description

        if definition:
            # Must lock job type interfaces so the new recipe type definition can be validated
            _ = definition.get_job_types(lock=True)
            definition.validate_job_interfaces()
            recipe_type.definition = definition.get_dict()
            recipe_type.revision_num = recipe_type.revision_num + 1

        if trigger_rule or remove_trigger_rule:
            if recipe_type.trigger_rule:
                # Archive old trigger rule since we are changing to a new one
                TriggerRule.objects.archive_trigger_rule(recipe_type.trigger_rule_id)
            recipe_type.trigger_rule = trigger_rule

        # Validate updated trigger rule against updated definition
        if recipe_type.trigger_rule:
            trigger_config = recipe_type.trigger_rule.get_configuration()
            if not isinstance(trigger_config, RecipeTriggerRuleConfiguration):
                msg = '%s is an invalid trigger rule type for creating recipes'
                raise InvalidTriggerType(msg % recipe_type.trigger_rule.type)
            trigger_config.validate_trigger_for_recipe(recipe_type.get_recipe_definition())

        recipe_type.save()

        if definition:
            # Create new revision of the recipe type for new definition
            RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)

    def get_active_trigger_rules(self, trigger_type):
        """Returns the active trigger rules with the given trigger type that create jobs and recipes

        :param trigger_type: The trigger rule type
        :type trigger_type: str
        :returns: The active trigger rules for the given type and their associated job/recipe types
        :rtype: list[(:class:`trigger.models.TriggerRule`, :class:`job.models.JobType`
            or :class:`recipe.models.RecipeType`)]
        """

        trigger_rules = []

        # Get trigger rules that create jobs
        job_type_qry = JobType.objects.select_related('trigger_rule')
        for job_type in job_type_qry.filter(trigger_rule__is_active=True, trigger_rule__type=trigger_type):
            trigger_rules.append((job_type.trigger_rule, job_type))

        # Get trigger rules that create recipes
        recipe_type_qry = RecipeType.objects.select_related('trigger_rule')
        for recipe_type in recipe_type_qry.filter(trigger_rule__is_active=True, trigger_rule__type=trigger_type):
            trigger_rules.append((recipe_type.trigger_rule, recipe_type))

        return trigger_rules

    def get_details(self, recipe_type_id):
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
        recipe_type.job_types = recipe_type.get_recipe_definition().get_job_types()

        return recipe_type

    def get_recipe_types(self, started=None, ended=None, order=None):
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

    def validate_recipe_type(self, name, title, version, description, definition, trigger_config):
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
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerType`: If the given trigger rule is an invalid
            type for creating recipes
        :raises :class:`trigger.configuration.exceptions.InvalidTriggerRule`: If the given trigger rule configuration is
            invalid
        :raises :class:`recipe.configuration.data.exceptions.InvalidRecipeConnection`: If the trigger rule connection to
            the recipe type definition is invalid
        """

        warnings = definition.validate_job_interfaces()

        if trigger_config:
            trigger_config.validate()
            if not isinstance(trigger_config, RecipeTriggerRuleConfiguration):
                msg = '%s is an invalid trigger rule type for creating recipes'
                raise InvalidTriggerType(msg % trigger_config.trigger_rule_type)
            warnings.extend(trigger_config.validate_trigger_for_recipe(definition))

        return warnings


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

    :keyword is_active: Whether the recipe type is active (false once recipe type is archived)
    :type is_active: :class:`django.db.models.BooleanField`
    :keyword definition: JSON definition for running a recipe of this type
    :type definition: :class:`djorm_pgjson.fields.JSONField`
    :keyword revision_num: The current revision number of the definition, starts at one
    :type revision_num: :class:`django.db.models.IntegerField`
    :keyword trigger_rule: The rule to trigger new recipes of this type
    :type trigger_rule: :class:`django.db.models.ForeignKey`

    :keyword created: When the recipe type was created
    :type created: :class:`django.db.models.DateTimeField`
    :keyword archived: When the recipe type was archived (no longer active)
    :type archived: :class:`django.db.models.DateTimeField`
    :keyword last_modified: When the recipe type was last modified
    :type last_modified: :class:`django.db.models.DateTimeField`
    """

    name = models.CharField(db_index=True, max_length=50)
    version = models.CharField(db_index=True, max_length=50)
    title = models.CharField(blank=True, max_length=50, null=True)
    description = models.CharField(blank=True, max_length=500, null=True)

    is_active = models.BooleanField(default=True)
    definition = djorm_pgjson.fields.JSONField()
    revision_num = models.IntegerField(default=1)
    trigger_rule = models.ForeignKey('trigger.TriggerRule', blank=True, null=True, on_delete=models.PROTECT)

    created = models.DateTimeField(auto_now_add=True)
    archived = models.DateTimeField(blank=True, null=True)
    last_modified = models.DateTimeField(auto_now=True)

    objects = RecipeTypeManager()

    def get_recipe_definition(self):
        """Returns the definition for running recipes of this type

        :returns: The recipe definition for this type
        :rtype: :class:`recipe.configuration.definition.recipe_definition.RecipeDefinition`
        """

        return RecipeDefinition(self.definition)

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_type'
        unique_together = ('name', 'version')


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

    def get_revision(self, recipe_type_id, revision_num):
        """Returns the revision for the given recipe type and revision number

        :param recipe_type_id: The ID of the recipe type
        :type recipe_type_id: int
        :param revision_num: The revision number
        :type revision_num: int
        :returns: The revision
        :rtype: :class:`recipe.models.RecipeTypeRevision`
        """

        return RecipeTypeRevision.objects.get(recipe_type_id=recipe_type_id, revision_num=revision_num)


class RecipeTypeRevision(models.Model):
    """Represents a revision of a recipe type. New revisions are created when the definition of a recipe type changes.
    Any inserts of a recipe type revision model requires obtaining a lock using select_for_update() on the corresponding
    recipe type model.

    :keyword recipe_type: The recipe type for this revision
    :type recipe_type: :class:`django.db.models.ForeignKey`
    :keyword revision_num: The number for this revision, starting at one
    :type revision_num: :class:`django.db.models.IntegerField`
    :keyword definition: The JSON definition for this revision of the recipe type
    :type definition: :class:`djorm_pgjson.fields.JSONField`
    :keyword created: When this revision was created
    :type created: :class:`django.db.models.DateTimeField`
    """

    recipe_type = models.ForeignKey('recipe.RecipeType', on_delete=models.PROTECT)
    revision_num = models.IntegerField()
    definition = djorm_pgjson.fields.JSONField()
    created = models.DateTimeField(auto_now_add=True)

    objects = RecipeTypeRevisionManager()

    def get_recipe_definition(self):
        """Returns the recipe type definition for this revision

        :returns: The recipe type definition for this revision
        :rtype: :class:`recipe.configuration.definition.recipe_definition.RecipeDefinition`
        """

        return RecipeDefinition(self.definition)

    class Meta(object):
        """meta information for the db"""
        db_table = 'recipe_type_revision'
        unique_together = ('recipe_type', 'revision_num')
