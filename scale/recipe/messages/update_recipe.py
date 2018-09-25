"""Defines a command message that evaluates and updates a recipe"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.utils.timezone import now

from job.messages.blocked_jobs import create_blocked_jobs_messages
from job.messages.pending_jobs import create_pending_jobs_messages
from job.messages.process_job_input import create_process_job_input_messages
from job.models import Job
from messaging.messages.message import CommandMessage
from recipe.diff.json.forced_nodes_v6 import convert_forced_nodes_to_v6, ForcedNodesV6
from recipe.models import Recipe, RecipeNode


logger = logging.getLogger(__name__)


def create_update_recipe_message(root_recipe_id, forced_nodes=None):
    """Creates a message to update the given recipe from its root ID

    :param root_recipe_id: The root recipe ID
    :type root_recipe_id: int
    :param forced_nodes: Describes the nodes that have been forced to reprocess
    :type forced_nodes: :class:`recipe.diff.forced_nodes.ForcedNodes`
    :return: The list of messages
    :rtype: list
    """

    message = UpdateRecipe()
    message.root_recipe_id = root_recipe_id
    message.forced_nodes = forced_nodes
    return message


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

        # TODO: - implement
        recipe = Recipe.objects.get_recipe_instance_from_root(self.root_recipe_id)
        when = now()

        jobs_to_update = recipe.get_jobs_to_update()
        blocked_job_ids = jobs_to_update['BLOCKED']
        pending_job_ids = jobs_to_update['PENDING']



        # TODO: - remove old code
        when = now()
        blocked_job_ids = set()
        pending_job_ids = set()
        completed_recipe_ids = []
        updated_batch_ids = []
        num_jobs_with_input = 0
        job_ids_ready_for_first_queue = []

        with transaction.atomic():
            # Lock recipes
            Recipe.objects.get_locked_recipes(self._recipe_ids)

            # Process all recipe handlers
            recipes = list(Recipe.objects.get_recipes_with_definitions(self._recipe_ids))
            while len(recipes) > 0:
                # Gather up a list of recipes that doesn't exceed the job number limit
                recipe_list = [recipes.pop()]
                # TODO: eventually use job count per recipe, right now assume 10
                num_jobs = 10
                while len(recipes) > 0 and num_jobs + 10 < MAX_JOBS_AT_A_TIME:
                    num_jobs += 10
                    recipe_list.append(recipes.pop())

                # Process handlers for the list of recipes
                handlers = Recipe.objects.get_recipe_handlers(recipe_list)

                # Create any jobs needed
                jobs_to_create = []
                recipe_handler_dicts = {}
                for handler in handlers:
                    handler_dict = handler.get_jobs_to_create()
                    recipe_handler_dicts[handler.recipe.id] = handler_dict
                    for job_list in handler_dict.values():
                        for job in job_list:
                            jobs_to_create.append(job)
                if jobs_to_create:
                    Job.objects.bulk_create(jobs_to_create)
                recipe_jobs_to_create = []
                for handler in handlers:
                    recipe_id = handler.recipe.id
                    handler_dict = recipe_handler_dicts[recipe_id]
                    recipe_jobs = []
                    for job_name, job_list in handler_dict.iteritems():
                        for job in job_list:
                            recipe_job = RecipeNode()
                            recipe_job.job = job
                            recipe_job.node_name = job_name
                            recipe_job.recipe_id = recipe_id
                            recipe_jobs.append(recipe_job)
                    recipe_jobs_to_create.extend(recipe_jobs)
                    handler.add_jobs(recipe_jobs)
                if recipe_jobs_to_create:
                    RecipeNode.objects.bulk_create(recipe_jobs_to_create)

                for handler in handlers:
                    for blocked_job in handler.get_blocked_jobs():
                        blocked_job_ids.add(blocked_job.id)
                    for pending_job in handler.get_pending_jobs():
                        pending_job_ids.add(pending_job.id)
                    jobs_with_input = handler.get_jobs_ready_for_input()
                    num_jobs_with_input += len(jobs_with_input)
                    for job in jobs_with_input:
                        job.update_database_with_input(when)
                    for job in handler.get_jobs_ready_for_first_queue():
                        job_ids_ready_for_first_queue.append(job.id)
                    if handler.is_completed() and not handler.recipe.is_completed:
                        completed_recipe_ids.append(handler.recipe.id)
                        if handler.recipe.batch_id:
                            updated_batch_ids.append(handler.recipe.batch_id)

            Recipe.objects.complete_recipes(completed_recipe_ids, when)

        # Create new messages
        self.new_messages.extend(create_blocked_jobs_messages(blocked_job_ids, when))
        self.new_messages.extend(create_pending_jobs_messages(pending_job_ids, when))
        # Jobs ready for their first queue need to have their input processed
        self.new_messages.extend(create_process_job_input_messages(job_ids_ready_for_first_queue))

        logger.info('Found %d job(s) that should transition to BLOCKED', len(blocked_job_ids))
        logger.info('Found %d job(s) that should transition to PENDING', len(pending_job_ids))
        logger.info('Found %d job(s) that received their input', num_jobs_with_input)
        logger.info('Found %d job(s) that are ready to be queued', len(job_ids_ready_for_first_queue))

        return True
