"""Defines a command message that evaluates and updates a recipe"""
from __future__ import unicode_literals

import logging

from django.utils.timezone import now

from job.messages.blocked_jobs import create_blocked_jobs_messages
from job.messages.create_jobs import create_jobs_messages_for_recipe, RecipeJob
from job.messages.pending_jobs import create_pending_jobs_messages
from job.messages.process_job_input import create_process_job_input_messages
from messaging.messages.message import CommandMessage
from recipe.definition.node import JobNodeDefinition, RecipeNodeDefinition
from recipe.diff.forced_nodes import ForcedNodes
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6, ForcedNodesV6
from recipe.messages.create_recipes import create_subrecipes_messages, SubRecipe
from recipe.messages.process_recipe_input import create_process_recipe_input_messages
from recipe.models import Recipe


logger = logging.getLogger(__name__)


def create_sub_update_recipe_definition_message(recipe_type_id, sub_recipe_type_id):
    """Creates a message to update the given recipe type to use the latest revision of the sub recipe type

    :param recipe_type_id: The recipe type to update
    :type recipe_type_id: int
    :param sub_recipe_type_id: The sub recipe type
    :type sub_recipe_type_id: int
    :return: The message
    :rtype: :class:`recipe.messages.update_recipe.UpdateRecipeDefinition`
    """

    message = UpdateRecipeDefinition()
    message.recipe_type_id = recipe_type_id
    message.sub_recipe_type_id = sub_recipe_type_id
    return message


def create_job_update_recipe_definition_message(recipe_type_id, job_type_id):
    """Creates a message to update the given recipe type to use the latest revision of the job type

    :param recipe_type_id: The recipe type to update
    :type recipe_type_id: int
    :param job_type_id: The job type
    :type job_type_id: int
    :return: The list of messages
    :rtype: list
    """

    message = UpdateRecipeDefinition()
    message.recipe_type_id = recipe_type_id
    message.job_type_id = job_type_id
    return message


class UpdateRecipeDefinition(CommandMessage):
    """Command message that evaluates and updates a recipe
    """

    def __init__(self):
        """Constructor
        """

        super(UpdateRecipeDefinition, self).__init__('update_recipe_definition')

        self.recipe_type_id = None
        self.sub_recipe_type_id = None
        self.job_type_id = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {
            'recipe_type_id': self.recipe_type_id,
            'sub_recipe_type_id': self.sub_recipe_type_id,
            'job_type_id': self.job_type_id
        }

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = UpdateRecipeDefinition()
        message.recipe_type_id = json_dict['recipe_type_id']
        message.sub_recipe_type_id = json_dict['sub_recipe_type_id']
        message.job_type_id = json_dict['job_type_id']

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        # Acquire model lock for recipe type
        recipe_type = RecipeType.objects.select_for_update().get(pk=self.recipe_type_id)
        recipe_model = recipe.recipe_model
        when = now()

        jobs_to_update = recipe.get_jobs_to_update()
        blocked_job_ids = jobs_to_update['BLOCKED']
        pending_job_ids = jobs_to_update['PENDING']

        nodes_to_create = recipe.get_nodes_to_create()
        nodes_to_process_input = recipe.get_nodes_to_process_input()

        if not recipe_model.is_completed and recipe.has_completed():
            Recipe.objects.complete_recipes([recipe_model.id], when)

        # Create new messages for changing job statuses
        if len(blocked_job_ids):
            logger.info('Found %d job(s) that should transition to BLOCKED', len(blocked_job_ids))
            self.new_messages.extend(create_blocked_jobs_messages(blocked_job_ids, when))
        if len(pending_job_ids):
            logger.info('Found %d job(s) that should transition to PENDING', len(pending_job_ids))
            self.new_messages.extend(create_pending_jobs_messages(pending_job_ids, when))

        # Create new messages to create recipe nodes
        recipe_jobs = []
        subrecipes = []
        for node_name, node_def in nodes_to_create.items():
            process_input = False
            if node_name in nodes_to_process_input:
                process_input = True
                del nodes_to_process_input[node_name]
            if node_def.node_type == JobNodeDefinition.NODE_TYPE:
                job = RecipeJob(node_def.job_type_name, node_def.job_type_version, node_def.revision_num, node_name,
                                process_input)
                recipe_jobs.append(job)
            elif node_def.node_type == RecipeNodeDefinition.NODE_TYPE:
                subrecipe = SubRecipe(node_def.recipe_type_name, node_def.revision_num, node_name, process_input)
                subrecipes.append(subrecipe)
        if len(recipe_jobs):
            logger.info('Found %d job(s) to create for this recipe', len(recipe_jobs))
            self.new_messages.extend(create_jobs_messages_for_recipe(recipe_model, recipe_jobs))
        if len(subrecipes):
            logger.info('Found %d sub-recipe(s) to create for this recipe', len(subrecipes))
            self.new_messages.extend(create_subrecipes_messages(recipe_model, subrecipes,
                                                                forced_nodes=self.forced_nodes))

        # Create new messages for processing recipe node input
        process_job_ids = []
        process_recipe_ids = []
        for node_name, node in nodes_to_process_input.items():
            if node.node_type == JobNodeDefinition.NODE_TYPE:
                process_job_ids.append(node.job.id)
            elif node.node_type == RecipeNodeDefinition.NODE_TYPE:
                process_recipe_ids.append(node.recipe.id)
        if len(process_job_ids):
            logger.info('Found %d job(s) to process their input and move to the queue', len(process_job_ids))
            self.new_messages.extend(create_process_job_input_messages(process_job_ids))
        if len(process_recipe_ids):
            logger.info('Found %d sub-recipe(s) to process their input and begin processing', len(process_recipe_ids))
            self.new_messages.extend(create_process_recipe_input_messages(process_recipe_ids))

        return True
