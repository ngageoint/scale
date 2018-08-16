"""Defines a command message that creates recipe models"""
from __future__ import unicode_literals

import logging

from django.db import transaction

from data.data.json.data_v6 import DataV6
from data.data.exceptions import InvalidData
from job.messages.process_job_input import create_process_job_input_messages
from messaging.messages.message import CommandMessage
from recipe.models import Recipe, RecipeNode, RecipeTypeRevision


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
    """Command message that creates job models
    """

    def __init__(self):
        """Constructor
        """

        super(CreateRecipes, self).__init__('create_recipes')

        self.count = 1  # TODO: determine this from superseded_recipes (reprocess) or 1 (sub-recipes)
        self.event_id = None

        # TODO: group fields so we could do multiple recipe types
        # recipe_type_name, recipe_type_rev_num, recipe_node_name
        self.recipe_type_name = None
        self.recipe_type_rev_num = None
        self.recipe_node_name = None
        self.process_input = False

        # These fields are related to the recipe containing the new created recipe(s)
        self.root_recipe_id = None
        self.superseded_recipe_id = None
        self.recipe_id = None
        self.batch_id = None

        # TODO: figure out all_jobs and job_names functionality

    # TODO:
    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'count': self.count, 'job_type_name': self.job_type_name,
                     'job_type_version': self.job_type_version, 'job_type_rev_num': self.job_type_rev_num,
                     'event_id': self.event_id, 'process_input': self.process_input}

        if self.input_data:
            json_dict['input_data'] = self.input_data
        if self.root_recipe_id:
            json_dict['root_recipe_id'] = self.root_recipe_id
        if self.superseded_recipe_id:
            json_dict['superseded_recipe_id'] = self.superseded_recipe_id
        if self.recipe_id:
            json_dict['recipe_id'] = self.recipe_id
        if self.recipe_node_name:
            json_dict['recipe_node_name'] = self.recipe_node_name
        if self.batch_id:
            json_dict['batch_id'] = self.batch_id

        return json_dict

    # TODO:
    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = CreateJobs()
        message.count = json_dict['count']
        message.job_type_name = json_dict['job_type_name']
        message.job_type_version = json_dict['job_type_version']
        message.job_type_rev_num = json_dict['job_type_rev_num']
        message.event_id = json_dict['event_id']
        message.process_input = json_dict['process_input']

        if 'input_data' in json_dict:
            message.input_data = json_dict['input_data']
        if 'root_recipe_id' in json_dict:
            message.root_recipe_id = json_dict['root_recipe_id']
        if 'superseded_recipe_id' in json_dict:
            message.superseded_recipe_id = json_dict['superseded_recipe_id']
        if 'recipe_id' in json_dict:
            message.recipe_id = json_dict['recipe_id']
        if 'recipe_node_name' in json_dict:
            message.recipe_node_name = json_dict['recipe_node_name']
        if 'batch_id' in json_dict:
            message.batch_id = json_dict['batch_id']

        return message

    # TODO:
    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # TODO:
        #  - lock superseded recipes to make sure a recipe isn't reprocessed twice
        #  - look for existing recipes to see if message has already run, if not go to next step
        #  - superseded recipe can be provided or found from containing recipe's superseded recipe (two cases, one from
        #    top level reprocess/batch and the other from update_recipes)
        #  - bulk create new recipe models
        #  - bulk create new recipe_node models if new recipes are sub-recipes
        #  - if new recipe is superseding another recipe, then it is a reprocess, flag indicates to do diff
        #   - if flag is set
        #       - if superseded recipe has data, copy data from it
        #       - supersede/cancel/unpublish deleted jobs and sub-recipes (message for sub-recipes to s/c/u)
        #       - supersede/cancel changed jobs and sub-recipes (message for sub-recipes to s/c)
        #       - copy identical jobs and sub-recipes from superseded recipe
        #   - if has data or in a recipe and process_input flag, send message to process_recipe_input
        #  - send messages for canceling and unpublishing
        #  - send update_recipe_metrics message if in a recipe

        # TODO: figure out how to handle two re-processes over top of each other

        # TODO: move this to _create_recipes()?
        recipe_type_rev = RecipeTypeRevision.objects.get_revision(self.recipe_type_name, self.recipe_type_rev_num)

        # Check to see if jobs were already created so that message is idempotent
        jobs = self._find_existing_jobs(job_type_rev)
        if not jobs:
            jobs = self._create_jobs(job_type_rev)

        # If the jobs already have their input data or process_input flag is set (recipe is ready to pass input), send
        # messages to process job input
        if jobs and (self.input_data or self.process_input):
            job_ids = [job.id for job in jobs]
            self.new_messages.extend(create_process_job_input_messages(job_ids))

        return True

    # TODO:
    def _create_recipes(self, recipe_type_rev):
        """Creates the recipe models for the message

        :param recipe_type_rev: The recipe type revision with populated recipe_type model
        :type recipe_type_rev: :class:`recipe.models.RecipeTypeRevision`
        :returns: The list of recipe models created
        :rtype: list
        """

        recipes = []

        # TODO: superseded jobs and sub-recipes all the way down
        # TODO: create messages to cancel superseded jobs all the way down
        # TODO: create messages to unpublish deleted jobs all the way down

        # If this new sub-recipe(s) is in a recipe that supersedes another recipe, find the corresponding superseded
        # sub-recipe(s)
        superseded_subrecipe = None
        if self.superseded_recipe_id:
            superseded_subrecipes = RecipeNode.objects.get_superseded_subrecipes(self.superseded_recipe_id,
                                                                                 self.recipe_node_name)
            if len(superseded_subrecipes) == 1:
                superseded_subrecipe = superseded_subrecipes[0]

        try:
            with transaction.atomic():
                # Bulk create recipes
                for _ in xrange(self.count):
                    input_data = DataV6(self.input_data, do_validate=True).get_data() if self.input_data else None
                    job = Job.objects.create_job_v6(job_type_rev, self.event_id, input_data=input_data,
                                                    root_recipe_id=self.root_recipe_id, recipe_id=self.recipe_id,
                                                    batch_id=self.batch_id, superseded_job=superseded_job)
                    jobs.append(job)
                Job.objects.bulk_create(jobs)

                if self.recipe_id:
                    # Bulk create recipe nodes
                    node_models = RecipeNode.objects.create_recipe_job_nodes(self.recipe_id, self.recipe_node_name,
                                                                             jobs)
                    RecipeNode.objects.bulk_create(node_models)
        except InvalidData:
            msg = 'Recipe of type (%s, %d) was given invalid input data. Message will not re-run.'
            logger.exception(msg, self.recipe_type_name, self.recipe_type_rev_num)
            recipes = []

        return recipes

    def _find_existing_recipes(self):
        """Searches to determine if this message already ran and the recipes already exist

        :returns: The list of recipe models found
        :rtype: list
        """

        if self.recipe_id:
            qry = RecipeNode.objects.filter(recipe_id=self.recipe_id, node_name=self.recipe_node_name)
            qry = qry.filter(sub_recipe__event_id=self.event_id)
            recipes = [recipe_node.sub_recipe for recipe_node in qry]
        else:
            qry = Recipe.objects.filter(event_id=self.event_id)
            if self.batch_id:
                qry = qry.filter(batch_id=self.batch_id)
            if self.input_data:
                qry = qry.filter(input=self.input_data)
            recipes = list(qry)

        return recipes
