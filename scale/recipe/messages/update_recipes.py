"""Defines a command message that evaluates and updates recipes"""
from __future__ import unicode_literals

import logging

from django.db import transaction
from django.utils.timezone import now

from job.messages.blocked_jobs import create_blocked_jobs_messages
from job.messages.pending_jobs import create_pending_jobs_messages
from job.messages.process_job_inputs import create_process_job_inputs_messages
from job.models import Job
from messaging.messages.message import CommandMessage
from recipe.models import Recipe, RecipeJob

# This is the maximum number of recipe models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100

# This is the maximum number of jobs to handle at a time so that the message handler memory is not exceeded.
MAX_JOBS_AT_A_TIME = 1000


logger = logging.getLogger(__name__)


def create_update_recipes_messages(recipe_ids):
    """Creates messages to update the given recipes

    :param recipe_ids: The recipe IDs
    :type recipe_ids: list
    :return: The list of messages
    :rtype: list
    """

    messages = []

    message = None
    for recipe_id in recipe_ids:
        if not message:
            message = UpdateRecipes()
        elif not message.can_fit_more():
            messages.append(message)
            message = UpdateRecipes()
        message.add_recipe(recipe_id)
    if message:
        messages.append(message)

    return messages


def create_update_recipes_messages_from_jobs(job_ids):
    """Creates messages to update the recipes for the given jobs

    :param job_ids: The job IDs
    :type job_ids: list
    :return: The list of messages
    :rtype: list
    """

    recipe_ids = Recipe.objects.get_latest_recipe_ids_for_jobs(job_ids)
    return create_update_recipes_messages(recipe_ids)


class UpdateRecipes(CommandMessage):
    """Command message that evaluates and updates recipes
    """

    def __init__(self):
        """Constructor
        """

        super(UpdateRecipes, self).__init__('update_recipes')

        self._count = 0
        self._recipe_ids = []

    def add_recipe(self, recipe_id):
        """Adds the given recipe ID to this message

        :param recipe_id: The recipe ID
        :type recipe_id: int
        """

        self._count += 1
        self._recipe_ids.append(recipe_id)

    def can_fit_more(self):
        """Indicates whether more recipes can fit in this message

        :return: True if more recipes can fit, False otherwise
        :rtype: bool
        """

        return self._count < MAX_NUM

    def to_json(self):
        """See :meth:`messaging.messages.message.CommandMessage.to_json`
        """

        return {'recipe_ids': self._recipe_ids}

    @staticmethod
    def from_json(json_dict):
        """See :meth:`messaging.messages.message.CommandMessage.from_json`
        """

        message = UpdateRecipes()
        for recipe_id in json_dict['recipe_ids']:
            message.add_recipe(recipe_id)

        return message

    def execute(self):
        """See :meth:`messaging.messages.message.CommandMessage.execute`
        """

        when = now()
        blocked_job_ids = set()
        pending_job_ids = set()
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
                            recipe_job = RecipeJob()
                            recipe_job.job = job
                            recipe_job.job_name = job_name
                            recipe_job.recipe_id = recipe_id
                            recipe_jobs.append(recipe_job)
                    recipe_jobs_to_create.extend(recipe_jobs)
                    handler.add_jobs(recipe_jobs)
                if recipe_jobs_to_create:
                    RecipeJob.objects.bulk_create(recipe_jobs_to_create)

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
                    # TODO: handle this in a new message where recipe models lock themselves and then update
                    if handler.is_completed():
                        Recipe.objects.complete_recipe(handler.recipe.id, when)

        # Create new messages
        self.new_messages.extend(create_blocked_jobs_messages(blocked_job_ids, when))
        self.new_messages.extend(create_pending_jobs_messages(pending_job_ids, when))
        # Jobs ready for their first queue need to have their input processed
        self.new_messages.extend(create_process_job_inputs_messages(job_ids_ready_for_first_queue))

        logger.info('Found %d job(s) that should transition to BLOCKED', len(blocked_job_ids))
        logger.info('Found %d job(s) that should transition to PENDING', len(pending_job_ids))
        logger.info('Found %d job(s) that received their input', num_jobs_with_input)
        logger.info('Found %d job(s) that are ready to be queued', len(job_ids_ready_for_first_queue))

        return True
