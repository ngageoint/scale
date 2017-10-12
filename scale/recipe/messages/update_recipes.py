"""Defines a command message that evaluates and updates recipes"""
from __future__ import unicode_literals

import logging

from django.utils.timezone import now

from job.messages.blocked_jobs import BlockedJobs
from job.messages.pending_jobs import PendingJobs
from messaging.messages.message import CommandMessage
from recipe.models import Recipe

# This is the maximum number of recipe models that can fit in one message. This maximum ensures that every message of
# this type is less than 25 KiB long and that each message can be processed quickly.
MAX_NUM = 100

# This is the maximum number of jobs to handle at a time so that the message handler memory is not exceeded.
MAX_JOBS_AT_A_TIME = 1000


logger = logging.getLogger(__name__)


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

        # Process all recipe handlers
        recipes = Recipe.objects.get_recipes_with_definitions(self._recipe_ids)
        while len(recipes) > 0:
            # Gather up a list of recipes that doesn't exceed the job number limit
            recipe_list = [recipes.pop()]
            # TODO: eventually use job count per recipe, right now assume 10
            num_jobs = 10
            while len(recipes) > 0 and num_jobs + 10 < MAX_JOBS_AT_A_TIME:
                recipe_list.append(recipes.pop())

            # Process handlers for the list of recipes
            for handler in Recipe.objects.get_recipe_handlers(recipe_list):
                for blocked_job in handler.get_blocked_jobs():
                    blocked_job_ids.add(blocked_job.id)
                for pending_job in handler.get_pending_jobs():
                    pending_job_ids.add(pending_job.id)

        # Create new messages
        self._create_blocked_jobs_messages(blocked_job_ids, when)
        self._create_pending_jobs_messages(pending_job_ids, when)

        return True

    def _create_blocked_jobs_messages(self, blocked_job_ids, when):
        """Creates messages to update the given job IDs to BLOCKED

        :param blocked_job_ids: The job IDs
        :type blocked_job_ids: list
        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        message = None
        for job_id in blocked_job_ids:
            if not message:
                message = BlockedJobs()
                message.status_change = when
            elif not message.can_fit_more():
                self.new_messages.append(message)
                message = BlockedJobs()
                message.status_change = when
            message.add_job(job_id)
        if message:
            self.new_messages.append(message)

    def _create_pending_jobs_messages(self, pending_job_ids, when):
        """Creates messages to update the given job IDs to PENDING

        :param pending_job_ids: The job IDs
        :type pending_job_ids: list
        :param when: The current time
        :type when: :class:`datetime.datetime`
        """

        message = None
        for job_id in pending_job_ids:
            if not message:
                message = PendingJobs()
                message.status_change = when
            elif not message.can_fit_more():
                self.new_messages.append(message)
                message = PendingJobs()
                message.status_change = when
            message.add_job(job_id)
        if message:
            self.new_messages.append(message)
