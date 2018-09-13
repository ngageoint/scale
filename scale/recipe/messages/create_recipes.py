"""Defines a command message that creates recipe models"""
from __future__ import unicode_literals

import logging
from collections import namedtuple

from django.db import transaction
from django.utils.timezone import now

from data.data.exceptions import InvalidData
from messaging.messages.message import CommandMessage
from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition
from recipe.diff.diff import RecipeDiff
from recipe.messages.process_recipe_input import create_process_recipe_input_messages
from recipe.messages.supersede_recipe_nodes import create_supersede_recipe_nodes_messages
from recipe.messages.update_recipe_metrics import create_update_recipe_metrics_messages
from recipe.models import Recipe, RecipeNode, RecipeNodeCopy, RecipeTypeRevision


REPROCESS_TYPE = 'reprocess'  # Message type for creating recipes that are reprocessing another set of recipes
SUB_RECIPE_TYPE = 'sub-recipes'  # Message type for creating sub-recipes of another recipe
# TODO: when data sets have been implemented, create a message type for creating recipes from data set members

# This is the maximum number of recipe models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100


# Tuple for specifying each sub-recipe to create for SUB_RECIPE_TYPE messages
SubRecipe = namedtuple('SubRecipe', ['recipe_type_name', 'recipe_type_rev_num', 'node_name', 'process_input'])


# Private named tuples for this message's use only
_RecipeDiff = namedtuple('_RecipeDiff', ['diff', 'recipe_pairs'])
_RecipePair = namedtuple('_RecipePair', ['superseded_recipe', 'new_recipe'])


logger = logging.getLogger(__name__)


# TODO:
def create_jobs_message(job_type_name, job_type_version, job_type_rev_num, event_id, count=1, input_data_dict=None):
    """Creates a message to create job(s) of the given type

    :param job_type_name: The job type name
    :type job_type_name: string
    :param job_type_version: The job type version
    :type job_type_version: string
    :param job_type_rev_num: The job type revision number
    :type job_type_rev_num: string
    :param event_id: The event ID
    :type event_id: int
    :param count: The number of jobs to create
    :type count: int
    :param input_data_dict: The optional JSON dict of the input data for the job(s)
    :type input_data_dict: dict
    :return: The message for creating the job(s)
    :rtype: :class:`job.messages.create_jobs.CreateJobs`
    """

    message = CreateJobs()
    message.count = count
    message.job_type_name = job_type_name
    message.job_type_version = job_type_version
    message.job_type_rev_num = job_type_rev_num
    message.event_id = event_id
    message.input_data = input_data_dict

    return message


# TODO: have methods both for reprocessing (top-level) and for sub-recipes
def create_jobs_message_for_recipe(recipe, node_name, job_type_name, job_type_version, job_type_rev_num, count=1,
                                   process_input=False):
    """Creates a message to create job(s) of the given type for the given recipe

    :param recipe: The recipe
    :type recipe: :class:`recipe.models.Recipe`
    :param node_name: The node name for the job(s) within the recipe
    :type node_name: string
    :param job_type_name: The job type name
    :type job_type_name: string
    :param job_type_version: The job type version
    :type job_type_version: string
    :param job_type_rev_num: The job type revision number
    :type job_type_rev_num: string
    :param count: The number of jobs to create
    :type count: int
    :return: The message for creating the job(s)
    :rtype: :class:`job.messages.create_jobs.CreateJobs`
    """

    message = create_jobs_message(job_type_name, job_type_version, job_type_rev_num, recipe.event_id, count=count)

    message.root_recipe_id = recipe.root_superseded_recipe_id
    message.superseded_recipe_id = recipe.superseded_recipe_id
    message.recipe_id = recipe.id
    message.recipe_node_name = node_name
    message.batch_id = recipe.batch_id
    message.process_input = process_input

    return message


class CreateRecipes(CommandMessage):
    """Command message that creates recipe models
    """

    def __init__(self):
        """Constructor
        """

        super(CreateRecipes, self).__init__('create_recipes')

        # TODO: make a forced_nodes class:
        # {'node_name_a': {}, 'node_name_b': {'node_name_ba': {}}, 'node_name_c': '*'}

        # Fields applicable to all message types
        self.batch_id = None
        self.event_id = None
        self.forced_nodes = None

        # The message type for how to create the recipes
        self.create_recipes_type = None

        # Fields applicable for reprocessing
        self.recipe_type_name = None
        self.recipe_type_rev_num = None
        self.root_recipe_ids = []
        self._superseded_recipes = []

        # Fields applicable for sub-recipes
        self.recipe_id = None
        self.root_recipe_id = None
        self.superseded_recipe_id = None
        self.sub_recipes = []
        self._process_input = {}  # process_input flags stored by new recipe ID

        # Private work fields
        self._when = None
        self._recipe_diffs = []  # List of _RecipeDiff tuples if new recipes are superseding old recipes

    def add_recipe_to_reprocess(self, root_recipe_id):
        """Adds the given root recipe ID to this message to be reprocessed

        :param root_recipe_id: The root recipe ID
        :type root_recipe_id: int
        """

        if self.create_recipes_type == REPROCESS_TYPE:
            self.root_recipe_ids.append(root_recipe_id)

    def add_subrecipe(self, sub_recipe):
        """Adds the given sub-recipe to this message to be created

        :param sub_recipe: The sub-recipe
        :type sub_recipe: :class:`recipe.messages.create_recipes.SubRecipe`
        """

        if self.create_recipes_type == SUB_RECIPE_TYPE:
            self.sub_recipes.append(sub_recipe)

    def can_fit_more(self):
        """Indicates whether more recipes can fit in this message

        :return: True if more recipes can fit, False otherwise
        :rtype: bool
        """

        if self.create_recipes_type == REPROCESS_TYPE:
            return len(self.root_recipe_ids) < MAX_NUM
        elif self.create_recipes_type == SUB_RECIPE_TYPE:
            return len(self.sub_recipes) < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'event_id': self.event_id, 'create_recipes_type': self.create_recipes_type}

        if self.batch_id:
            json_dict['batch_id'] = self.batch_id
        if self.forced_nodes:
            json_dict['forced_nodes'] = self.forced_nodes

        if self.create_recipes_type == REPROCESS_TYPE:
            json_dict['recipe_type_name'] = self.recipe_type_name
            json_dict['recipe_type_rev_num'] = self.recipe_type_rev_num
            json_dict['root_recipe_ids'] = self.root_recipe_ids
        elif self.create_recipes_type == SUB_RECIPE_TYPE:
            json_dict['recipe_id'] = self.recipe_id
            if self.root_recipe_id:
                json_dict['root_recipe_id'] = self.root_recipe_id
            if self.superseded_recipe_id:
                json_dict['superseded_recipe_id'] = self.superseded_recipe_id
            sub_recipes = []
            for sub_recipe in self.sub_recipes:
                sub_recipes.append({'recipe_type_name': sub_recipe.recipe_type,
                                    'recipe_type_rev_num': sub_recipe.recipe_type_rev_num,
                                    'node_name': sub_recipe.node_name, 'process_input': sub_recipe.process_input})
            json_dict['sub_recipes'] = sub_recipes

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CreateRecipes()
        message.event_id = json_dict['event_id']
        message.create_recipes_type = json_dict['create_recipes_type']
        if 'batch_id' in json_dict:
            message.batch_id = json_dict['batch_id']
        if 'forced_nodes' in json_dict:
            message.forced_nodes = json_dict['forced_nodes']

        if message.create_recipes_type == REPROCESS_TYPE:
            message.recipe_type_name = json_dict['recipe_type_name']
            message.recipe_type_rev_num = json_dict['recipe_type_rev_num']
            message.root_recipe_ids = json_dict['root_recipe_ids']
        elif message.create_recipes_type == SUB_RECIPE_TYPE:
            message.recipe_id = json_dict['recipe_id']
            if 'root_recipe_id' in json_dict:
                message.root_recipe_id = json_dict['root_recipe_id']
            if 'superseded_recipe_id' in json_dict:
                message.superseded_recipe_id = json_dict['superseded_recipe_id']
            for sub_dict in json_dict['sub_recipes']:
                sub_recipe = SubRecipe(sub_dict['recipe_type_name'], sub_dict['recipe_type_rev_num'],
                                       sub_dict['node_name'], sub_dict['process_input'])
                message.sub_recipes.append(sub_recipe)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        self._when = now()

        # TODO: move this snippet into the unit tests for this message as a placeholder until node copying is tested
        # INSERT INTO recipe_node (node_name, is_original, recipe_id, job_id, sub_recipe_id)
        # SELECT node_name, false, %new_recipe_id%, job_id, sub_recipe_id FROM recipe_node
        #   WHERE recipe_id = %old_recipe_id% AND node_name IN ('%node_name')
        # UNION ALL SELECT node_name, false, %new_recipe_id%, job_id, sub_recipe_id FROM recipe_node
        #   WHERE recipe_id = %old_recipe_id% AND node_name IN ('%node_name')

        with transaction.atomic():
            self._perform_locking()
            recipes = self._find_existing_recipes()
            if not recipes:
                recipes = self._create_recipes()

        self._create_messages(recipes)

        return True

    def _copy_recipe_nodes(self):
        """Copies recipe nodes from the superseded recipes to the new recipes that are identical
        """

        recipe_node_copies = []

        for recipe_diff in self._recipe_diffs:
            node_names = set(recipe_diff.diff.get_nodes_to_copy().keys())
            for recipe_pair in recipe_diff.recipe_pairs:
                superseded_recipe = recipe_pair.superseded_recipe
                new_recipe = recipe_pair.new_recipe
                recipe_node_copy = RecipeNodeCopy(superseded_recipe.id, new_recipe.id, node_names)
                recipe_node_copies.append(recipe_node_copy)

        RecipeNode.objects.copy_recipe_nodes(recipe_node_copies)

    def _create_messages(self, new_recipes):
        """Creates any messages resulting from the new recipes

        :param new_recipes: The list of new recipe models
        :type new_recipes: list
        """

        # Send supersede_recipe_nodes messages if new recipes are superseding old ones
        for recipe_diff in self._recipe_diffs:
            recipe_ids = []
            supersede_jobs = set()
            supersede_subrecipes = set()
            unpublish_jobs = set()
            supersede_recursive = set()
            unpublish_recursive = set()
            # Gather up superseded recipe IDs for this diff
            for recipe_pair in recipe_diff.recipe_pairs:
                recipe_ids.append(recipe_pair.superseded_recipe.id)
            # Supersede applicable jobs and sub-recipes
            for node_diff in recipe_diff.diff.get_nodes_to_supersede().values():
                if node_diff.node_type == JobNodeDefinition.NODE_TYPE:
                    supersede_jobs.add(node_diff.name)
                elif node_diff.node_type == RecipeNodeDefinition.NODE_TYPE:
                    supersede_subrecipes.add(node_diff.name)
            # Recursively supersede applicable sub-recipes
            for node_diff in recipe_diff.diff.get_nodes_to_recursively_supersede().values():
                if node_diff.node_type == RecipeNodeDefinition.NODE_TYPE:
                    supersede_recursive.add(node_diff.name)
            # Unpublish applicable jobs and recursively unpublish applicable sub-recipes
            for node_diff in recipe_diff.diff.get_nodes_to_unpublish().values():
                if node_diff.node_type == JobNodeDefinition.NODE_TYPE:
                    unpublish_jobs.add(node_diff.name)
                elif node_diff.node_type == RecipeNodeDefinition.NODE_TYPE:
                    unpublish_recursive.add(node_diff.name)
            msgs = create_supersede_recipe_nodes_messages(recipe_ids, self._when, supersede_jobs, supersede_subrecipes,
                                                          unpublish_jobs, supersede_recursive, unpublish_recursive)
            self.new_messages.extend(msgs)

        process_input_recipe_ids = []
        update_recipe_ids = []
        for new_recipe in new_recipes:
            # process_input indicates if new_recipe is a sub-recipe and ready to get its input from its dependencies
            process_input = self.recipe_id and self._process_input.get(new_recipe.id, False)
            if new_recipe.has_input() or process_input:
                # This new recipe is all ready to have its input processed
                process_input_recipe_ids.append(new_recipe.id)
            else:
                # Recipe not ready for its input yet, but send update_recipe for it to create its nodes awhile
                update_recipe_ids.append(new_recipe.id)
        self.new_messages.extend(create_process_recipe_input_messages(process_input_recipe_ids))
        # TODO: create messages to update recipes after new update_recipe message is created

        if self.recipe_id:
            # Update the metrics for the recipe containing the new sub-recipes we just created
            self.new_messages.extend(create_update_recipe_metrics_messages([self.recipe_id]))

    def _create_recipes(self):
        """Creates the recipe models for the message

        :returns: The list of recipe models created
        :rtype: list
        """

        if self.create_recipes_type == REPROCESS_TYPE:
            recipes = self._create_recipes_for_reprocess()
        elif self.create_recipes_type == SUB_RECIPE_TYPE:
            recipes = self._create_subrecipes()

        if self._recipe_diffs:
            # If new recipes are superseding old recipes, compare revisions and copy nodes from old to new
            self._copy_recipe_nodes()

        return recipes

    def _create_recipes_for_reprocess(self):
        """Creates the recipe models for a reprocess

        :returns: The list of recipe models created
        :rtype: list
        """

        recipes = []

        # Supersede recipes that are being reprocessed
        superseded_recipe_ids = [r.id for r in self._superseded_recipes]
        Recipe.objects.supersede_recipes(superseded_recipe_ids, self._when)

        # Get superseded recipe definitions and calculate diffs
        revision_tuples = [(self.recipe_type_name, self.recipe_type_rev_num)]
        revs = RecipeTypeRevision.objects.get_revisions(superseded_recipe_ids, revision_tuples)
        for rev in revs.values():
            if rev.recipe_type.name == self.recipe_type_name:
                if rev.revision_num == self.recipe_type_rev_num:
                    new_rev = rev
                    break
        diffs = {rev_id: RecipeDiff(rev.get_definition(), new_rev.get_definition()) for rev_id, rev in revs.items()}

        # Create new recipe models
        cannot_reprocess_count = 0
        for superseded_recipe in self._superseded_recipes:
            if diffs[superseded_recipe].can_be_reprocessed:
                try:
                    recipe = Recipe.objects.create_recipe_v6(new_rev, self.event_id, batch_id=self.batch_id,
                                                             superseded_recipe=superseded_recipe,
                                                             copy_superseded_input=True)
                    recipes.append(recipe)
                except InvalidData:
                    cannot_reprocess_count += 1
            else:
                cannot_reprocess_count += 1

        Recipe.objects.bulk_create(recipes)
        logger.info('Created %d recipe(s)', len(recipes))
        logger.error('Could not reprocess %d recipe(s) due to interface changes', cannot_reprocess_count)

        # Set up recipe diffs
        pairs_by_rev_id = {}
        for recipe in recipes:
            pair = _RecipePair(recipe.superseded_recipe, recipe)
            rev_id = recipe.superseded_recipe.recipe_type_rev_id
            if rev_id not in pairs_by_rev_id:
                pairs_by_rev_id[rev_id] = []
            pairs_by_rev_id[rev_id].append(pair)
        for rev_id, diff in diffs.items():
            self._recipe_diffs.append(_RecipeDiff(diff, pairs_by_rev_id[rev_id]))

        return recipes

    def _create_subrecipes(self):
        """Creates the recipe models for a sub-recipe message

        :returns: The list of recipe models created
        :rtype: list
        """

        sub_recipes = {}  # {Node name: recipe model}

        superseded_recipe_ids = []
        # Get superseded sub-recipes from superseded recipe
        if self.superseded_recipe_id:
            superseded_sub_recipes = RecipeNode.objects.get_subrecipes(self.superseded_recipe_id)
            superseded_recipe_ids = [r.id for r in superseded_sub_recipes.values()]

        # Get recipe type revisions
        revision_tuples = [(sub.recipe_type_name, sub.recipe_type_rev_num) for sub in self.sub_recipes]
        revs_by_id = RecipeTypeRevision.objects.get_revisions(superseded_recipe_ids, revision_tuples)
        revs_by_tuple = {(rev.recipe_type.name, rev.revision_num): rev for rev in revs_by_id.values()}

        # Create new recipe models
        process_input_by_node = {}
        for sub_recipe in self.sub_recipes:
            node_name = sub_recipe.node_name
            process_input_by_node[node_name] = sub_recipe.process_input
            revision = revs_by_tuple[(sub_recipe.recipe_type_name, sub_recipe.recipe_type_rev_num)]
            superseded_recipe = superseded_sub_recipes[node_name] if node_name in superseded_sub_recipes else None
            recipe = Recipe.objects.create_recipe_v6(revision, self.event_id, root_recipe_id=self.root_recipe_id,
                                                     recipe_id=self.recipe_id, batch_id=self.batch_id,
                                                     superseded_recipe=superseded_recipe)
            sub_recipes[node_name] = recipe

        Recipe.objects.bulk_create(sub_recipes.values())
        logger.info('Created %d recipe(s)', len(sub_recipes))

        # Create recipe nodes
        recipe_nodes = RecipeNode.objects.create_subrecipe_nodes(self.recipe_id, sub_recipes)
        RecipeNode.objects.bulk_create(recipe_nodes)

        # Set up process input dict
        for sub_recipe in self.sub_recipes:
            recipe = sub_recipes[sub_recipe.node_name]
            self._process_input[recipe.id] = sub_recipe.process_input

        # Set up recipe diffs
        if self.superseded_recipe_id:
            for recipe in sub_recipes.values():
                pair = _RecipePair(recipe.superseded_recipe, recipe)
                rev_id = recipe.superseded_recipe.recipe_type_rev_id
                old_revision = revs_by_id[rev_id]
                new_revision = revs_by_tuple[(recipe.recipe_type.name, recipe.recipe_type_rev.revision_num)]
                diff = RecipeDiff(old_revision.get_definition(), new_revision.get_definition())
                self._recipe_diffs.append(_RecipeDiff(diff, [pair]))

        return sub_recipes.values()

    def _find_existing_recipes(self):
        """Searches to determine if this message already ran and the new recipes already exist

        :returns: The list of recipe models found
        :rtype: list
        """

        if self.create_recipes_type == REPROCESS_TYPE:
            qry = Recipe.objects.select_related('superseded_recipe')
            recipes = qry.filter(root_superseded_recipe_id__in=self.root_recipe_ids, event_id=self.event_id)
        elif self.create_recipes_type == SUB_RECIPE_TYPE:
            node_names = [sub.node_name for sub in self.sub_recipes]
            qry = RecipeNode.objects.select_related('sub_recipe__superseded_recipe')
            qry = qry.filter(recipe_id=self.recipe_id, node_name__in=node_names, sub_recipe__event_id=self.event_id)
            recipes_by_node = {rn.node_name: rn.sub_recipe for rn in qry}
            recipes = list(recipes_by_node.values())
            if recipes_by_node:
                # Set up process input dict
                for sub_recipe in self.sub_recipes:
                    recipe = recipes_by_node[sub_recipe.node_name]
                    self._process_input[recipe.id] = sub_recipe.process_input

        if recipes and recipes[0].superseded_recipe:
            rev_ids = [recipe.recipe_type_rev_id for recipe in recipes]
            superseded_rev_ids = [recipe.superseded_recipe.recipe_type_rev_id for recipe in recipes]
            if superseded_rev_ids:
                # New recipes superseded old recipes, so create recipe diffs
                rev_ids.extend(superseded_rev_ids)
                revs = RecipeTypeRevision.objects.get_revisions(rev_ids, [])
                pair_dict = {}
                for recipe in recipes:
                    rev_tuple = (recipe.superseded_recipe.recipe_type_rev_id, recipe.recipe_type_rev_id)
                    pair = _RecipePair(recipe.superseded_recipe, recipe)
                    if rev_tuple not in pair_dict:
                        pair_dict[rev_tuple] = []
                    pair_dict[rev_tuple].append(pair)
                for pair_tuple, pairs in pair_dict.items():
                    old_revision = revs[pair_tuple[0]]
                    new_revision = revs[pair_tuple[1]]
                    diff = RecipeDiff(old_revision.get_definition(), new_revision.get_definition())
                    self._recipe_diffs.append(_RecipeDiff(diff, pairs))

        return recipes

    def _perform_locking(self):
        """Performs locking so that multiple messages don't interfere with each other. The caller must be within an
        atomic transaction.
        """

        if self.create_recipes_type == REPROCESS_TYPE:
            self._superseded_recipes = Recipe.objects.get_locked_recipes_from_root(self.root_recipe_ids)
        elif self.create_recipes_type == SUB_RECIPE_TYPE:
            Recipe.objects.get_locked_recipe(self.recipe_id)
