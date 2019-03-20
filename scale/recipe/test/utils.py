"""Defines utility methods for testing jobs and job types"""
from __future__ import unicode_literals

from django.db import transaction
import django.utils.timezone as timezone

import job.test.utils as job_test_utils
import trigger.test.utils as trigger_test_utils
from batch.models import Batch
from data.data.exceptions import InvalidData
from job.messages.create_jobs import RecipeJob
from job.models import Job, JobTypeRevision
from queue.messages.queued_jobs import QueuedJob
from queue.models import Queue
from recipe.configuration.definition.recipe_definition import LegacyRecipeDefinition as RecipeDefinition
from recipe.configuration.data.recipe_data import LegacyRecipeData
from recipe.configuration.data.exceptions import InvalidRecipeConnection
from recipe.definition.json.definition_v6 import RecipeDefinitionV6
from recipe.definition.node import ConditionNodeDefinition, JobNodeDefinition, RecipeNodeDefinition
from recipe.handlers.graph import RecipeGraph
from recipe.handlers.graph_delta import RecipeGraphDelta
from recipe.messages.create_conditions import Condition
from recipe.messages.create_recipes import SubRecipe
from recipe.models import Recipe, RecipeCondition, RecipeInputFile, RecipeNode, RecipeType, RecipeTypeRevision
from recipe.models import RecipeTypeSubLink, RecipeTypeJobLink
import storage.test.utils as storage_test_utils
from trigger.handler import TriggerRuleHandler, register_trigger_rule_handler


NAME_COUNTER = 1
VERSION_COUNTER = 1
TITLE_COUNTER = 1
DESCRIPTION_COUNTER = 1

SUB_RECIPE_DEFINITION = {'version': '6',
                   'input': {'files': [],
                             'json': []},
                   'nodes': {'node_a': {'dependencies': [],
                                        'input': {},
                                        'node_type': {'node_type': 'job', 'job_type_name': 'my-job-type',
                                                      'job_type_version': '1.0.0',
                                                      'job_type_revision': 1}}}}

RECIPE_DEFINITION = {'version': '6',
                            'input': {'files': [{'name': 'INPUT_IMAGE', 'media_types': ['image/png'], 'required': True,
                                                 'multiple': False}],
                                      'json': [{'name': 'bar', 'type': 'string', 'required': False}]},
                            'nodes': {'node_a': {'dependencies': [],
                                                 'input': {'INPUT_IMAGE': {'type': 'recipe', 'input': 'INPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 'job_type_name': 'my-job-type',
                                                               'job_type_version': '1.0.0',
                                                               'job_type_revision': 1}},
                                      'node_b': {'dependencies': [{'name': 'node_a', 'acceptance': True}],
                                                 'input': {'INPUT_IMAGE': {'type': 'dependency', 'node': 'node_a',
                                                                           'output': 'OUTPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'job', 'job_type_name': 'my-job-type',
                                                               'job_type_version': '1.0.0',
                                                               'job_type_revision': 1}},
                                      'node_c': {'dependencies': [{'name': 'node_b', 'acceptance': True}],
                                                 'input': {'input_a': {'type': 'recipe', 'input': 'bar'},
                                                           'input_b': {'type': 'dependency', 'node': 'node_b',
                                                                       'output': 'OUTPUT_IMAGE'}},
                                                 'node_type': {'node_type': 'recipe', 'recipe_type_name': 'sub-recipe',
                                                               'recipe_type_revision': 1}}}}

def create_recipe_type_v5(name=None, version=None, title=None, description=None, definition=None, trigger_rule=None):
    """Creates a recipe type for unit testing

    :returns: The RecipeType model
    :rtype: :class:`recipe.models.RecipeType`
    """

    if not name:
        global NAME_COUNTER
        name = 'test-recipe-type-%i' % NAME_COUNTER
        NAME_COUNTER += 1

    if not version:
        global VERSION_COUNTER
        version = '%i.0.0' % VERSION_COUNTER
        VERSION_COUNTER += 1

    if not title:
        global TITLE_COUNTER
        title = 'Test Recipe Type %i' % TITLE_COUNTER
        TITLE_COUNTER += 1

    if not description:
        global DESCRIPTION_COUNTER
        description = 'Test Description %i' % DESCRIPTION_COUNTER
        DESCRIPTION_COUNTER += 1

    if not definition:
        definition = {
            'version': '1.0',
            'input_data': [],
            'jobs': [],
        }

    recipe_type = RecipeType()
    recipe_type.name = name
    recipe_type.version = version
    recipe_type.title = title
    recipe_type.description = description
    recipe_type.definition = definition
    recipe_type.save()

    RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)

    return recipe_type

def create_recipe_type_v6(name=None, version=None, title=None, description=None, definition=None, is_active=None,
                          is_system=None):
    """Creates a recipe type for unit testing

    :returns: The RecipeType model
    :rtype: :class:`recipe.models.RecipeType`
    """

    if not name:
        global NAME_COUNTER
        name = 'test-recipe-type-%i' % NAME_COUNTER
        NAME_COUNTER += 1

    if not version:
        global VERSION_COUNTER
        version = '%i.0.0' % VERSION_COUNTER
        VERSION_COUNTER += 1

    if not title:
        global TITLE_COUNTER
        title = 'Test Recipe Type %i' % TITLE_COUNTER
        TITLE_COUNTER += 1

    if not description:
        global DESCRIPTION_COUNTER
        description = 'Test Description %i' % DESCRIPTION_COUNTER
        DESCRIPTION_COUNTER += 1

    if not definition:
        definition = {
            'version': '6',
            'input': {},
            'nodes': {}}

    recipe_type = RecipeType()
    recipe_type.name = name
    recipe_type.version = version
    recipe_type.title = title
    recipe_type.description = description
    recipe_type.definition = definition
    if is_active is not None:
        recipe_type.is_active = is_active
    if is_system is not None:
        recipe_type.is_system = is_system
    recipe_type.save()

    RecipeTypeRevision.objects.create_recipe_type_revision(recipe_type)

    RecipeTypeJobLink.objects.create_recipe_type_job_links_from_definition(recipe_type)
    RecipeTypeSubLink.objects.create_recipe_type_sub_links_from_definition(recipe_type)

    return recipe_type


def edit_recipe_type_v5(recipe_type, definition):
    """Updates the definition of a recipe type, including creating a new revision for unit testing
    """
    with transaction.atomic():
        RecipeType.objects.edit_recipe_type_v5(recipe_type_id=recipe_type.id, title=None, description=None,
                                               definition=RecipeDefinition(definition), trigger_rule=None,
                                               remove_trigger_rule=False)

def edit_recipe_type_v6(recipe_type, title=None, description=None, definition=None, auto_update=None):
    """Updates the definition of a recipe type, including creating a new revision for unit testing
    """
    with transaction.atomic():
        RecipeType.objects.edit_recipe_type_v6(recipe_type.id, title=title, description=description,
                                               definition=RecipeDefinitionV6(definition).get_definition(),
                                               auto_update=auto_update)

def create_recipe(recipe_type=None, input=None, event=None, is_superseded=False, superseded=None,
                  superseded_recipe=None, batch=None, save=True):
    """Creates a recipe for unit testing

    :returns: The recipe model
    :rtype: :class:`recipe.models.Recipe`
    """

    if not recipe_type:
        recipe_type = create_recipe_type_v5()
    if not input:
        input = {}
    if not event:
        event = trigger_test_utils.create_trigger_event()
    if is_superseded and not superseded:
        superseded = timezone.now()

    recipe = Recipe()
    recipe.recipe_type = recipe_type
    recipe.recipe_type_rev = RecipeTypeRevision.objects.get_revision(recipe_type.name, recipe_type.revision_num)
    recipe.event = event
    recipe.input = input
    recipe.is_superseded = is_superseded
    recipe.superseded = superseded
    recipe.batch = batch
    if superseded_recipe:
        root_id = superseded_recipe.root_superseded_recipe_id
        if root_id is None:
            root_id = superseded_recipe.id
        recipe.root_superseded_recipe_id = root_id
        recipe.superseded_recipe = superseded_recipe

    if save:
        recipe.save()

    return recipe

def process_recipe_inputs(recipe_ids):
    """Mimics effect of process_recipe_input messages for unit testing """

    for recipe_id in recipe_ids:
        recipe = Recipe.objects.get_recipe_with_interfaces(recipe_id)
        if not recipe.has_input():
            if not recipe.recipe:
                #print 'Recipe %d has no input and is not in a recipe. Message will not re-run.' % recipe.id
                continue

            generate_input_data_from_recipe(recipe)

        # Lock recipe model and process recipe's input data
        with transaction.atomic():
            recipe = Recipe.objects.get_locked_recipe(recipe_id)
            root_recipe_id = recipe.root_superseded_recipe_id if recipe.root_superseded_recipe_id else recipe.id
            Recipe.objects.process_recipe_input(recipe)

        if root_recipe_id:
            update_recipe(root_recipe_id)

def generate_input_data_from_recipe(sub_recipe):
    """Generates the sub-recipe's input data from its recipe dependencies and validates and sets the input data on
    the sub-recipe

    :param sub_recipe: The sub-recipe with related recipe_type_rev and recipe__recipe_type_rev models
    :type sub_recipe: :class:`recipe.models.Recipe`

    :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
    """

    # TODO: this is a hack to work with old legacy recipe data with workspaces, remove when legacy job types go
    old_recipe_input_dict = dict(sub_recipe.recipe.input)

    # Get sub-recipe input from dependencies in the recipe
    recipe_input_data = sub_recipe.recipe.get_input_data()
    node_outputs = RecipeNode.objects.get_recipe_node_outputs(sub_recipe.recipe_id)
    for node_output in node_outputs.values():
        if node_output.node_type == 'recipe' and node_output.id == sub_recipe.id:
            node_name = node_output.node_name
            break

    # TODO: this is a hack to work with old legacy recipe data with workspaces, remove when legacy job types go
    sub_recipe.recipe.input = old_recipe_input_dict

    definition = sub_recipe.recipe.recipe_type_rev.get_definition()
    input_data = definition.generate_node_input_data(node_name, recipe_input_data, node_outputs)
    Recipe.objects.set_recipe_input_data_v6(sub_recipe, input_data)

def update_recipe(root_recipe_id):
    """Mimics effect of update recipe messages for unit testing """

    recipe = Recipe.objects.get_recipe_instance_from_root(root_recipe_id)
    recipe_model = recipe.recipe_model
    when = timezone.now()

    jobs_to_update = recipe.get_jobs_to_update()
    blocked_job_ids = jobs_to_update['BLOCKED']
    pending_job_ids = jobs_to_update['PENDING']

    nodes_to_create = recipe.get_nodes_to_create()
    nodes_to_process_input = recipe.get_nodes_to_process_input()

    if not recipe_model.is_completed and recipe.has_completed():
        Recipe.objects.complete_recipes([recipe_model.id], when)

    # Create new messages for changing job statuses
    if len(blocked_job_ids):
        update_jobs_status(blocked_job_ids, when, status='BLOCKED')
    if len(pending_job_ids):
        update_jobs_status(pending_job_ids, when, status='PENDING')

    # Create recipe nodes
    conditions = []
    recipe_jobs = []
    subrecipes = []
    for node_name, node_def in nodes_to_create.items():
        process_input = False
        if node_name in nodes_to_process_input:
            process_input = True
            del nodes_to_process_input[node_name]
        if node_def.node_type == ConditionNodeDefinition.NODE_TYPE:
            condition = Condition(node_name, process_input)
            conditions.append(condition)
        elif node_def.node_type == JobNodeDefinition.NODE_TYPE:
            job = RecipeJob(node_def.job_type_name, node_def.job_type_version, node_def.revision_num, node_name,
                            process_input)
            recipe_jobs.append(job)
        elif node_def.node_type == RecipeNodeDefinition.NODE_TYPE:
            subrecipe = SubRecipe(node_def.recipe_type_name, node_def.revision_num, node_name, process_input)
            subrecipes.append(subrecipe)
    if len(conditions):
        create_conditions(recipe_model, conditions)
    if len(recipe_jobs):
        create_jobs_for_recipe(recipe_model, recipe_jobs)
    if len(subrecipes):
        create_subrecipes(recipe_model, subrecipes)

    # Create new messages for processing recipe node input
    process_condition_ids = []
    process_job_ids = []
    process_recipe_ids = []
    for node_name, node in nodes_to_process_input.items():
        if node.node_type == ConditionNodeDefinition.NODE_TYPE:
            process_condition_ids.append(node.condition.id)
        elif node.node_type == JobNodeDefinition.NODE_TYPE:
            process_job_ids.append(node.job.id)
        elif node.node_type == RecipeNodeDefinition.NODE_TYPE:
            process_recipe_ids.append(node.recipe.id)
    if len(process_condition_ids):
        process_conditions(process_condition_ids)
    if len(process_job_ids):
        process_job_inputs(process_job_ids)
    if len(process_recipe_ids):
        process_recipe_inputs(process_recipe_ids)

def update_jobs_status(job_ids, when=timezone.now(), status='BLOCKED'):
    """Mimics effect of create_blocked_jobs_messages and create_pending_jobs_messages for unit testing """

    with transaction.atomic():
        jobs = []
        # Retrieve locked job models
        for job_model in Job.objects.get_locked_jobs(job_ids):
            if not job_model.last_status_change or job_model.last_status_change < when:
                # Status update is not old, so perform the update
                jobs.append(job_model)

        # Update jobs that need status set to BLOCKED
        if jobs:
            if status == 'BLOCKED':
                job_ids = Job.objects.update_jobs_to_blocked(jobs, when)
            if status == 'PENDING':
                job_ids = Job.objects.update_jobs_to_pending(jobs, when)

    update_recipe_metrics(job_ids=job_ids)

def create_conditions(recipe_model, conditions):
    """Mimics effect of create_conditions_messages for unit testing"""

    condition_models = {}  # {Node name: condition model}

    # Create new condition models
    process_input_by_node = {}
    for condition in conditions:
        node_name = condition.node_name
        process_input_by_node[node_name] = condition.process_input
        condition = RecipeCondition.objects.create_condition(recipe_model.id, root_recipe_id=recipe_model.root_recipe_id,
                                                             batch_id=recipe_model.batch_id)
        condition_models[node_name] = condition

    RecipeCondition.objects.bulk_create(condition_models.values())

    # Create recipe nodes
    recipe_nodes = RecipeNode.objects.create_recipe_condition_nodes(recipe_model.id, condition_models)
    RecipeNode.objects.bulk_create(recipe_nodes)

    # Set up process input dict
    process_input_condition_ids = []
    for condition in conditions:
        condition_model = condition_models[condition.node_name]
        if condition.process_input:
            process_input_condition_ids.append(condition_model.id)
    process_conditions(process_input_condition_ids)

def process_conditions(process_input_condition_ids):
    """Mimics effect of create_process_condition_messages for unit testing"""

    for condition_id in process_input_condition_ids:
        condition = RecipeCondition.objects.get_condition_with_interfaces(condition_id)

        if not condition.is_processed:
            definition = condition.recipe.recipe_type_rev.get_definition()

            # Get condition data from dependencies in the recipe
            recipe_input_data = condition.recipe.get_input_data()
            node_outputs = RecipeNode.objects.get_recipe_node_outputs(condition.recipe_id)
            for node_output in node_outputs.values():
                if node_output.node_type == 'condition' and node_output.id == condition.id:
                    node_name = node_output.node_name
                    break

            # Set data on the condition model
            try:
                data = definition.generate_node_input_data(node_name, recipe_input_data, node_outputs)
                RecipeCondition.objects.set_condition_data_v6(condition, data, node_name)
            except InvalidData as ex:
                print 'Recipe created invalid input data for condition %d' % condition_id
                print ex
                continue

            # Process filter and set whether condition was accepted
            data_filter = definition.graph[node_name].data_filter
            is_accepted = data_filter.is_data_accepted(data)
            RecipeCondition.objects.set_processed(condition.id, is_accepted)

        # update the condition's recipe
        root_recipe_id = condition.recipe.root_recipe_id if condition.recipe.root_recipe_id else condition.recipe_id
        update_recipe(root_recipe_id)

def create_jobs_for_recipe(recipe_model, recipe_jobs):
    """Mimics effect of create_jobs_messages_for_recipe for unit testing"""

    recipe_jobs_map = {}  # {Node name: job model}

    superseded_jobs = {}
    # Get superseded jobs from superseded recipe
    if recipe_model.superseded_recipe_id:
        superseded_jobs = RecipeNode.objects.get_recipe_jobs(recipe_model.superseded_recipe_id)

    # Get job type revisions
    revision_tuples = [(j.job_type_name, j.job_type_version, j.job_type_rev_num) for j in recipe_jobs]
    revs_by_id = JobTypeRevision.objects.get_revisions(revision_tuples)
    revs_by_tuple = {(j.job_type.name, j.job_type.version, j.revision_num): j for j in revs_by_id.values()}

    # Create new job models
    process_input_by_node = {}
    for recipe_job in recipe_jobs:
        node_name = recipe_job.node_name
        process_input_by_node[node_name] = recipe_job.process_input
        tup = (recipe_job.job_type_name, recipe_job.job_type_version, recipe_job.job_type_rev_num)
        revision = revs_by_tuple[tup]
        superseded_job = superseded_jobs[node_name] if node_name in superseded_jobs else None
        job = Job.objects.create_job_v6(revision, event_id=recipe_model.event_id, root_recipe_id=recipe_model.root_recipe_id,
                                        recipe_id=recipe_model.id, batch_id=recipe_model.batch_id,
                                        superseded_job=superseded_job)
        recipe_jobs_map[node_name] = job

    Job.objects.bulk_create(recipe_jobs_map.values())

    # Create recipe nodes
    recipe_nodes = RecipeNode.objects.create_recipe_job_nodes(recipe_model.id, recipe_jobs_map)
    RecipeNode.objects.bulk_create(recipe_nodes)

    # Set up process input dict
    process_input_job_ids = []
    for recipe_job in recipe_jobs:
        job = recipe_jobs_map[recipe_job.node_name]
        process_input = recipe_model.id and recipe_job.process_input
        if job.has_input() or process_input:
            process_input_job_ids.append(job.id)

    process_job_inputs(process_input_job_ids)
    update_recipe_metrics([recipe_model.id])

def process_job_inputs(process_input_job_ids):
    """Mimics effect of create_process_job_input_messages for unit testing"""

    queued_jobs = []
    for job_id in process_input_job_ids:
        job = Job.objects.get_job_with_interfaces(job_id)

        if not job.has_input():
            if not job.recipe:
                #print ('Job %d has no input and is not in a recipe. Message will not re-run.', job_id)
                continue

            try:
                generate_job_input_data_from_recipe(job)
            except InvalidData as ex:
                print 'Recipe created invalid input data for job %d. Message will not re-run.' % job_id
                print ex
                continue

        # Lock job model and process job's input data
        with transaction.atomic():
            job = Job.objects.get_locked_job(job_id)
            Job.objects.process_job_input(job)

        # queue the job
        if job.num_exes == 0:
            queued_jobs.append(QueuedJob(job.id, 0))

    queue_jobs(queued_jobs)

def generate_job_input_data_from_recipe(job):
    """Generates the job's input data from its recipe dependencies and validates and sets the input data on the job

    :param job: The job with related job_type_rev and recipe__recipe_type_rev models
    :type job: :class:`job.models.Job`

    :raises :class:`data.data.exceptions.InvalidData`: If the data is invalid
    """

    from recipe.models import RecipeNode

    # TODO: this is a hack to work with old legacy recipe data with workspaces, remove when legacy job types go
    old_recipe_input_dict = dict(job.recipe.input)

    # Get job input from dependencies in the recipe
    recipe_input_data = job.recipe.get_input_data()
    node_outputs = RecipeNode.objects.get_recipe_node_outputs(job.recipe_id)
    for node_output in node_outputs.values():
        if node_output.node_type == 'job' and node_output.id == job.id:
            node_name = node_output.node_name
            break

    # TODO: this is a hack to work with old legacy recipe data with workspaces, remove when legacy job types go
    job.recipe.input = old_recipe_input_dict

    definition = job.recipe.recipe_type_rev.get_definition()
    input_data = definition.generate_node_input_data(node_name, recipe_input_data, node_outputs)
    Job.objects.set_job_input_data_v6(job, input_data)

def queue_jobs(queued_jobs, requeue=False, priority=None):
    """Mimics effect of create_queued_jobs_messages for unit testing"""

    job_ids = []
    for queued_job in queued_jobs:
        job_ids.append(queued_job.job_id)

    with transaction.atomic():
        # Retrieve locked job models
        job_models = {}
        for job in Job.objects.get_locked_jobs(job_ids):
            job_models[job.id] = job

        jobs_to_queue = []
        for queued_job in queued_jobs:
            job_model = job_models[queued_job.job_id]

            # If execution number does not match, then this update is obsolete
            if job_model.num_exes != queued_job.exe_num:
                # Ignore this job
                continue

            jobs_to_queue.append(job_model)

        # Queue jobs
        if jobs_to_queue:
            _ = Queue.objects.queue_jobs(jobs_to_queue, requeue=requeue, priority=priority)

def update_recipe_metrics(recipe_ids=[], job_ids=None):
    """Mimics effects of create_update_recipe_metrics_messages methods for unit testing"""

    if job_ids:
        recipe_ids.extend(Recipe.objects.get_recipe_ids_for_jobs(job_ids))
    if recipe_ids:
        sub_recipe_ids = Recipe.objects.get_recipe_ids_for_sub_recipes(recipe_ids)
        update_recipe_metrics(recipe_ids=sub_recipe_ids)

    Recipe.objects.update_recipe_metrics(recipe_ids)

    # If any of these recipes are sub-recipes, grab root recipe IDs and update those recipes
    root_recipe_ids = set()
    for recipe in Recipe.objects.filter(id__in=recipe_ids):
        if recipe.root_recipe_id:
            root_recipe_ids.add(recipe.root_recipe_id)
    if root_recipe_ids:
        for root_recipe_id in root_recipe_ids:
            update_recipe(root_recipe_id)

    # For any top-level recipes (not a sub-recipe) update any batches that these recipes belong to
    from batch.messages.update_batch_metrics import create_update_batch_metrics_messages
    batch_ids = set()
    qry = Recipe.objects.filter(id__in=recipe_ids, recipe__isnull=True, batch__isnull=False).only('batch_id')
    for recipe in qry:
        batch_ids.add(recipe.batch_id)
    if batch_ids:
        Batch.objects.update_batch_metrics(batch_ids)

def create_subrecipes(recipe_model, subrecipes):
    """Mimics effect of create_subrecipes_messages for unit testing"""

    sub_recipes_map = {}  # {Node name: recipe model}

    superseded_sub_recipes = {}
    revision_ids = []
    # Get superseded sub-recipes from superseded recipe
    if recipe_model.superseded_recipe_id:
        superseded_sub_recipes = RecipeNode.objects.get_subrecipes(recipe_model.superseded_recipe_id)
        revision_ids = [r.recipe_type_rev_id for r in superseded_sub_recipes.values()]

    # Get recipe type revisions
    revision_tuples = [(sub.recipe_type_name, sub.recipe_type_rev_num) for sub in subrecipes]
    revs_by_id = RecipeTypeRevision.objects.get_revision_map(revision_ids, revision_tuples)
    revs_by_tuple = {(rev.recipe_type.name, rev.revision_num): rev for rev in revs_by_id.values()}

    # Create new recipe models
    process_input_by_node = {}
    for sub_recipe in subrecipes:
        node_name = sub_recipe.node_name
        process_input_by_node[node_name] = sub_recipe.process_input
        revision = revs_by_tuple[(sub_recipe.recipe_type_name, sub_recipe.recipe_type_rev_num)]
        superseded_recipe = superseded_sub_recipes[node_name] if node_name in superseded_sub_recipes else None
        recipe = Recipe.objects.create_recipe_v6(revision, recipe_model.event_id, root_recipe_id=recipe_model.root_recipe_id,
                                                 recipe_id=recipe_model.id, batch_id=recipe_model.batch_id,
                                                 superseded_recipe=superseded_recipe)
        sub_recipes_map[node_name] = recipe

    Recipe.objects.bulk_create(sub_recipes_map.values())

    # Create recipe nodes
    recipe_nodes = RecipeNode.objects.create_subrecipe_nodes(recipe_model.id, sub_recipes_map)
    RecipeNode.objects.bulk_create(recipe_nodes)

    # Set up process input dict
    process_input_sub_ids = []
    for sub_recipe in subrecipes:
        recipe = sub_recipes_map[sub_recipe.node_name]
        if sub_recipe.process_input:
            process_input_sub_ids.append(recipe.id)

    # Set up recipe diffs
    # Uncomment and implement if needed to test superseding recipes
    """
    if self.superseded_recipe_id:
        for node_name, recipe in sub_recipes_map.items():
            pair = _RecipePair(recipe.superseded_recipe, recipe)
            rev_id = recipe.superseded_recipe.recipe_type_rev_id
            old_revision = revs_by_id[rev_id]
            new_revision = revs_by_tuple[(recipe.recipe_type.name, recipe.recipe_type_rev.revision_num)]
            diff = RecipeDiff(old_revision.get_definition(), new_revision.get_definition())
            if self.forced_nodes:
                sub_forced_nodes = self.forced_nodes.get_forced_nodes_for_subrecipe(node_name)
                if sub_forced_nodes:
                    diff.set_force_reprocess(sub_forced_nodes)
            self._recipe_diffs.append(_RecipeDiff(diff, [pair]))"""

    process_recipe_inputs(process_input_sub_ids)
    update_recipe_metrics([recipe_model.id])

def create_recipe_condition(root_recipe=None, recipe=None, batch=None, is_processed=None, is_accepted=None, save=False):
    """Creates a recipe_node model for unit testing

    :param root_recipe: The root recipe containing the condition
    :type root_recipe: :class:'recipe.models.Recipe'
    :param recipe: The recipe containing the condition
    :type recipe: :class:'recipe.models.Recipe'
    :param batch: The batch
    :type batch: :class:'batch.models.Batch'
    :param is_processed: Whether the condition has been processed
    :type is_processed: bool
    :param is_accepted: Whether the condition has been accepted
    :type is_accepted: bool
    :returns: The recipe_node model
    :rtype: :class:`recipe.models.RecipeNode`
    """

    if not recipe:
        recipe = create_recipe()

    condition = RecipeCondition()
    condition.root_recipe = root_recipe if root_recipe else recipe
    condition.recipe = recipe
    condition.batch = batch
    if is_processed is not None:
        condition.is_processed = is_processed
    if is_accepted is not None:
        condition.is_accepted = is_accepted

    if condition.is_processed:
        condition.processed = timezone.now()

    if save:
        condition.save()

    return condition


# TODO: this is deprecated and should be replaced with create_recipe_node()
def create_recipe_job(recipe=None, job_name=None, job=None):
    """Creates a job type model for unit testing

    :param recipe: The associated recipe
    :type recipe: :class:'recipe.models.Recipe'
    :param job_name: The associated name for the recipe job
    :type job_name: string
    :param job: The associated job
    :type job: :class:'job.models.Job'
    :returns: The recipe job model
    :rtype: :class:`recipe.models.RecipeNode`
    """
    if not recipe:
        recipe = create_recipe()

    if not job_name:
        job_name = 'Test Job Name'

    if not job:
        job = job_test_utils.create_job()

    recipe_job = RecipeNode()
    recipe_job.node_name = job_name
    recipe_job.job = job
    recipe_job.recipe = recipe
    recipe_job.save()
    return recipe_job


def create_recipe_node(recipe=None, node_name=None, condition=None, job=None, sub_recipe=None, save=False,
                       is_original=True):
    """Creates a recipe_node model for unit testing

    :param recipe: The recipe containing the node
    :type recipe: :class:'recipe.models.Recipe'
    :param node_name: The node name
    :type node_name: string
    :param condition: The condition in the node
    :type condition: :class:'recipe.models.RecipeCondition'
    :param job: The job in the node
    :type job: :class:'job.models.Job'
    :param sub_recipe: The recipe in the node
    :type sub_recipe: :class:'recipe.models.Recipe'
    :param save: Whether to save the model
    :type save: bool
    :param is_original: Whether the recipe node is original
    :type is_original: bool
    :returns: The recipe_node model
    :rtype: :class:`recipe.models.RecipeNode`
    """

    if not recipe:
        recipe = create_recipe()

    if not node_name:
        node_name = 'Test Node Name'

    if not job and not sub_recipe:
        job = job_test_utils.create_job()

    recipe_node = RecipeNode()
    recipe_node.recipe = recipe
    recipe_node.node_name = node_name
    recipe_node.is_original = is_original
    if condition:
        recipe_node.condition = condition
    elif job:
        recipe_node.job = job
    elif sub_recipe:
        recipe_node.sub_recipe = sub_recipe

    if save:
        recipe_node.save()

    return recipe_node


def create_recipe_handler(recipe_type=None, data=None, event=None, superseded_recipe=None, delta=None,
                          superseded_jobs=None):
    """Creates a recipe along with its declared jobs for unit testing

    :returns: The recipe handler with created recipe and jobs
    :rtype: :class:`recipe.handlers.handler.RecipeHandler`
    """

    if not recipe_type:
        recipe_type = create_recipe_type_v5()
    if not data:
        data = {}
    if not isinstance(data, LegacyRecipeData):
        data = LegacyRecipeData(data)
    if not event:
        event = trigger_test_utils.create_trigger_event()
    if superseded_recipe and not delta:
        delta = RecipeGraphDelta(RecipeGraph(), RecipeGraph())

    return Recipe.objects.create_recipe_old(recipe_type, data, event, superseded_recipe=superseded_recipe,
                                            delta=delta, superseded_jobs=superseded_jobs)


def create_input_file(recipe=None, input_file=None, recipe_input=None, file_name='my_test_file.txt', media_type='text/plain',
                      file_size=100, file_path=None, workspace=None, countries=None, is_deleted=False, data_type_tags=[],
                      last_modified=None, source_started=None, source_ended=None):
    """Creates a Scale file and recipe input file model for unit testing

    :returns: The file model
    :rtype: :class:`storage.models.ScaleFile`
    """

    if not recipe:
        recipe = create_recipe()
    if not recipe_input:
        recipe_input = 'test_input'
    if not input_file:
        input_file = storage_test_utils.create_file(file_name=file_name, media_type=media_type, file_size=file_size,
                                                    file_path=file_path, workspace=workspace, countries=countries,
                                                    is_deleted=is_deleted, data_type_tags=data_type_tags,
                                                    last_modified=last_modified, source_started=source_started,
                                                    source_ended=source_ended)

    RecipeInputFile.objects.create(recipe=recipe, input_file=input_file, recipe_input=recipe_input)

    return input_file
