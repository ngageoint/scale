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


def create_update_recipe_message(root_recipe_id, forced_nodes=None):
    """Creates a message to update the given recipe from its root ID

    :param root_recipe_id: The root recipe ID
    :type root_recipe_id: int
    :param forced_nodes: Describes the nodes that have been forced to reprocess
    :type forced_nodes: :class:`recipe.diff.forced_nodes.ForcedNodes`
    :return: The message
    :rtype: :class:`recipe.messages.update_recipe.UpdateRecipe`
    """

    message = UpdateRecipe()
    message.root_recipe_id = root_recipe_id
    message.forced_nodes = forced_nodes
    return message


def create_update_recipe_messages_from_node(root_recipe_ids):
    """Creates messages to update the given recipes from the root IDs. This is intended to be used by recipe nodes that
    have been updated and need to then update the recipes that contain the nodes.

    :param root_recipe_ids: The root recipe IDs
    :type root_recipe_ids: list
    :return: The list of messages
    :rtype: list
    """

    # We force all nodes to reprocess because if we are updating due to a recipe node update (completed job, failed job,
    # completed recipe, etc) then we want all new nodes to be created, not copied. Copying should only occur in the
    # initial creation messages of a reprocess when recipe diffs are being evaluated.
    force_all_nodes = ForcedNodes()
    force_all_nodes.set_all_nodes()

    messages = []
    for root_recipe_id in root_recipe_ids:
        messages.append(create_update_recipe_message(root_recipe_id, forced_nodes=force_all_nodes))
    return messages


def create_update_recipe_messages(root_recipe_ids):
    """Creates messages to update the given recipes from their root IDs

    :param root_recipe_ids: The root recipe IDs
    :type root_recipe_ids: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    for root_recipe_id in root_recipe_ids:
        msg = UpdateRecipe()
        msg.root_recipe_id = root_recipe_id
        messages.append(msg)

    return messages


class UpdateRecipe(CommandMessage):
    """Command message that evaluates and updates a recipe
    """

    def __init__(self):
        """Constructor
        """

        super(UpdateRecipe, self).__init__('update_recipe')

        self.root_recipe_id = None
        self.forced_nodes = None

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        json_dict = {'root_recipe_id': self.root_recipe_id}

        if self.forced_nodes:
            json_dict['forced_nodes'] = convert_forced_nodes_to_v6(self.forced_nodes).get_dict()

        return json_dict

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = UpdateRecipe()
        message.root_recipe_id = json_dict['root_recipe_id']
        if 'forced_nodes' in json_dict:
            message.forced_nodes = ForcedNodesV6(json_dict['forced_nodes']).get_forced_nodes()

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        recipe = Recipe.objects.get_recipe_instance_from_root(self.root_recipe_id)
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
